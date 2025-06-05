from utils.logger import log_error
def parse_salary(salary_range: str) -> tuple[int,int]: 
    # Парсим диапазон зарплаты из формата "xx,xxx-xx,xxx"
    salary_from = None
    salary_to = None

    if salary_range != "Не важно" and salary_range != "Не указана":
        try:
            if salary_range == "Более 100,000":
                salary_from = 100000
            elif "-" in salary_range:
                parts = salary_range.replace(",", "").split("-")
                salary_from = int(parts[0])
                salary_to = int(parts[1])
        except (ValueError, IndexError):
            log_error(f"Ошибка при парсинге диапазона зарплаты: {salary_range}")
    return salary_from, salary_to