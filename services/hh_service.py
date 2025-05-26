import aiohttp
import asyncio
import statistics
from config.api_url import HH_API_URL, SEARCH_PARAMS, HH_API_CITY_ID
from utils.logger import log_info, log_error
from .database import DatabaseHandler
from async_lru import alru_cache
from pprint import pprint
import re

async def fetch_vacancies(keyword, area=None, salary_from=None, salary_to=None, per_page=5):
    """Асинхронное получение вакансий с hh.ru по заданным параметрам."""
    params = {
        "text": keyword,
        "area": area if area else SEARCH_PARAMS["area"],
        "per_page": per_page if per_page else SEARCH_PARAMS["per_page"]
    }
    
    # Добавляем параметры зарплаты, если они указаны
    if salary_from:
        params["salary_from"] = salary_from
    if salary_to:
        params["salary_to"] = salary_to

    log_info(f"Запрос вакансий с параметрами: {params}")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(HH_API_URL, params=params) as response:
                response.raise_for_status()  # Проверка на ошибки HTTP
                log_info("Вакансии успешно получены.")
                return await response.json()  # Возвращаем JSON-ответ
        except aiohttp.ClientError as err:
            log_error(f"Ошибка запроса: {err}")
    return None


def parse_vacancies(data, user_id=1):
    """Парсинг данных вакансий из ответа API и сохранение в базу данных."""
    if not data or 'items' not in data:
        log_error("Нет данных для парсинга.")
        return []

    vacancies = []
    db_handler = DatabaseHandler()
    
    for item in data['items']:
        vacancy = {
            "id": str(item.get("id")),
            "title": item.get("name"),
            "url": item.get("alternate_url"),
            "salary": item.get("salary"),
            "experience": item.get("experience", {}).get("id"),
            "company": item.get("employer", {}).get("name"),
            "area": item.get("area", {}).get("name"),
            "published_at": item.get("published_at"),
            "requirements": item.get("snippet", {}).get("requirement", "")
        }
        vacancies.append(vacancy)
        
        # Сохраняем вакансию в базу данных, если указан user_id
        if user_id:
            db_handler.add_to_favorites(
                user_id=user_id,
                vacancy_data={
                    'id': vacancy['id'],
                    'title': vacancy['title'],
                    'company': vacancy['company'],
                    'salary': vacancy['salary'],
                    'area': vacancy['area'],
                    'url': vacancy['url']
                }
            )

    log_info(f"Парсинг завершен. Найдено {len(vacancies)} вакансий.")
    db_handler.close()
    return vacancies

async def get_vacancies_stats(keyword: str, city: str, count: int = 50) -> dict:
    """Сбор статистики по вакансиям"""
    params = {
        "text": keyword,
        "area": city,
        "per_page": min(count, 100),  # API HH ограничивает 100 вакансий на страницу
        "only_with_salary": 1  # Получаем только вакансии с указанной зарплатой
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(HH_API_URL, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                vacancies = parse_vacancies(data)
                if not vacancies:
                    return {
                        "avg_salary": 0,
                        "median_salary": 0,
                        "percentile_25": 0,
                        "percentile_75": 0,
                        "min_salary": 0,
                        "max_salary": 0,
                        "vacancies_count": 0,
                        "experience_distribution": {
                            "no_experience": 0,
                            "1-3_years": 0,
                            "3-6_years": 0,
                            "more_than_6": 0
                        }
                    }

                # Собираем зарплаты и опыт
                all_salaries = []
                experience_counts = {
                    "no_experience": 0,
                    "1-3_years": 0,
                    "3-6_years": 0,
                    "more_than_6": 0
                }
                all_skills = {}
                for vacancy in vacancies:
                    # Обработка зарплат
                    salary = vacancy.get("salary")
                    if salary:
                        from_salary = salary.get("from")
                        to_salary = salary.get("to")
                        if from_salary and to_salary:
                            all_salaries.append((from_salary + to_salary) / 2)
                        elif from_salary:
                            all_salaries.append(from_salary)
                        elif to_salary:
                            all_salaries.append(to_salary)
                    # skills
                    skills_row = vacancy.get("requirements")
                    pattern = r"\b[A-Za-z][A-Za-z0-9+#\. ]*(?:\s+[A-Za-z][A-Za-z0-9+#]*)*\b"
                    if skills_row:
                        skills = re.findall(pattern, skills_row)
                        for skill in skills:
                            if len(skill) >= 2 and not skill.isdigit():
                                skill = skill.strip(' .,').capitalize()
                                all_skills[skill] = all_skills.get(skill, 0) + 1
                    # Обработка опыта
                    exp = vacancy.get("experience")
                    if exp == "noExperience":
                        experience_counts["no_experience"] += 1
                    elif exp == "between1And3":
                        experience_counts["1-3_years"] += 1
                    elif exp == "between3And6":
                        experience_counts["3-6_years"] += 1
                    elif exp == "moreThan6":
                        experience_counts["more_than_6"] += 1

                if not all_salaries:
                    return {
                        "avg_salary": 0,
                        "median_salary": 0,
                        "percentile_25": 0,
                        "percentile_75": 0,
                        "min_salary": 0,
                        "max_salary": 0,
                        "vacancies_count": len(vacancies),
                        "experience_distribution": experience_counts
                    }

                filtered_skills = {skill: count for skill, count in all_skills.items() if count > 1 and skill != "Highlighttext"}
                skills_counter = sorted(filtered_skills.items(), key=lambda item: item[1], reverse=True)
                # Сортируем для расчета перцентилей
                all_salaries_sorted = sorted(all_salaries)
                n = len(all_salaries_sorted)
                
                return {
                    "avg_salary": round(statistics.mean(all_salaries_sorted), 2),
                    "median_salary": round(statistics.median(all_salaries_sorted), 2),
                    "percentile_25": round(all_salaries_sorted[int(n * 0.25)], 2),
                    "percentile_75": round(all_salaries_sorted[int(n * 0.75)], 2),
                    "min_salary": min(all_salaries_sorted),
                    "max_salary": max(all_salaries_sorted),
                    "vacancies_count": len(vacancies),
                    "experience_distribution": experience_counts,
                    "skills_counter": skills_counter
                }

        except Exception as e:
            log_error(f"Ошибка при сборе статистики: {e}")
            return {
                "avg_salary": 0,
                "vacancies_count": 0,
                "salary_distribution": []
            }

@alru_cache(maxsize=32)
async def get_city_id_by_city_name(city_name):
    params = {
        "text": city_name,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(HH_API_CITY_ID, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                city_id = data["items"][0]["id"]
                log_info("Был успешно получен id города в базе hh")
                return city_id
        except Exception as e:
            log_error("Ошибка при получении id города")

async def fetch_related_vacancies(vacancy_id: str) -> dict:
    """Запрос похожих вакансий через API HH."""
    params = {
        "per_page": 3,  # API HH ограничивает 100 вакансий на страницу
        "only_with_salary": 1  # Получаем только вакансии с указанной зарплатой
    }
    url = f"{HH_API_URL}/{vacancy_id}/related_vacancies"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            log_error(f"API HH error: {e}")
            return None

async def get_skills(vacancy_id: int):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'{HH_API_URL}/{vacancy_id}') as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("key_skills")
                # pprint(data)
        except Exception as e:
            log_error(f"ошибка получения навыков: {e}")
            return ""

# Пример использования
async def main():
    keyword = "devops"
    vacancies_data = await fetch_vacancies(keyword)
    vacancies = parse_vacancies(vacancies_data)
    for vacancy in vacancies:
        print(vacancy)


if __name__ == "__main__":
    asyncio.run(main())
