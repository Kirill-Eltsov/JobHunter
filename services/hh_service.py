import aiohttp
import asyncio
from config import HH_API_URL, SEARCH_PARAMS
from utils.logger import log_info, log_error



async def fetch_vacancies(keyword, area=None, per_page=5):
    """Асинхронное получение вакансий с hh.ru по заданным параметрам."""
    params = {
        "text": keyword,
        "area": area if area else SEARCH_PARAMS["area"],
        "per_page": SEARCH_PARAMS["per_page"]
    }

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


# Пример использования
async def main():
    keyword = "devops"
    vacancies_data = await fetch_vacancies(keyword)
    vacancies = parse_vacancies(vacancies_data)
    for vacancy in vacancies:
        print(vacancy)


if __name__ == "__main__":
    asyncio.run(main())
