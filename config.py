import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

TOKEN = os.getenv('TOKEN')

# URL API для получения вакансий с hh.ru
HH_API_URL = "https://api.hh.ru/vacancies"
