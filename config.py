# import os
# from dotenv import load_dotenv, dotenv_values

# load_dotenv()

# TOKEN = os.getenv('TOKEN')

# Параметры для поиска вакансий
SEARCH_PARAMS = {
    "text": "devops",  # Ключевое слово для поиска
    "area": "113",          # ID региона (например, Москва)
    "per_page": 3          # Количество вакансий на странице
}

# URL API для получения вакансий с hh.ru
HH_API_URL = "https://api.hh.ru/vacancies"
