

# Параметры для поиска вакансий
SEARCH_PARAMS = {
    "text": "devops",  # Ключевое слово для поиска
    "area": "113",          # ID региона (например, Москва)
    "per_page": 3          # Количество вакансий на странице
}

# URL API для получения вакансий с hh.ru
HH_API_URL = "https://api.hh.ru/vacancies"
# openstreetmap api
OPEN_STREET_MAP_URL = "https://nominatim.openstreetmap.org/reverse"
# получение id города
HH_API_CITY_ID = "https://api.hh.ru/suggests/areas"
# вакансии, похожие на вакансию с vacancy_id
HH_API_URL_RELATED = "https://api.hh.ru/vacancies/{vacancy_id}/related_vacancies"
