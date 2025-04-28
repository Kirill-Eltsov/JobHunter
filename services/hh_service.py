import aiohttp
import asyncio
import statistics
from config import HH_API_URL, SEARCH_PARAMS
from utils.logger import log_info, log_error
from .database import DatabaseHandler



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


def parse_vacancies(data):
    """Парсинг данных вакансий из ответа API."""
    if not data or 'items' not in data:
        log_error("Нет данных для парсинга.")
        return []

    vacancies = []
    for item in data['items']:
        vacancy = {
            "id": str(item.get("id")),
            "title": item.get("name"),
            "url": item.get("alternate_url"),
            "salary": item.get("salary"),
            "company": item.get("employer", {}).get("name"),
            "area": item.get("area", {}).get("name"),
            "published_at": item.get("published_at")
        }
        vacancies.append(vacancy)

    log_info(f"Парсинг завершен. Найдено {len(vacancies)} вакансий.")
    return vacancies

async def get_vacancies_stats(keyword: str, city: str, count: int = 50) -> dict:
    """Сбор статистики по вакансиям"""
    params = {
        "text": keyword,
        "area": city,
        "per_page": min(count, 100),  # API HH ограничивает 100 вакансий на страницу
        "only_with_salary": True  # Получаем только вакансии с указанной зарплатой
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
                        "min_salary": 0,
                        "max_salary": 0,
                        "vacancies_count": 0
                    }

                # Собираем все зарплаты
                all_salaries = []
                for vacancy in vacancies:
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

                if not all_salaries:
                    return {
                        "avg_salary": 0,
                        "min_salary": 0,
                        "max_salary": 0,
                        "vacancies_count": 0
                    }
                
                return {
                    "avg_salary": round(statistics.mean(all_salaries), 2),
                    "min_salary": min(all_salaries),
                    "max_salary": max(all_salaries),
                    "vacancies_count": len(vacancies)
                }

        except Exception as e:
            log_error(f"Ошибка при сборе статистики: {e}")
            return {
                "avg_salary": 0,
                "vacancies_count": 0,
                "salary_distribution": []
            }


# Пример использования
async def main():
    keyword = "devops"
    vacancies_data = await fetch_vacancies(keyword)
    vacancies = parse_vacancies(vacancies_data)
    for vacancy in vacancies:
        print(vacancy)


if __name__ == "__main__":
    asyncio.run(main())
