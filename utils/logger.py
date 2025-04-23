import logging
import os

cwd = os.getcwd()
# Создаем директорию для логов, если она не существует
log_directory = cwd + "/utils/logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Настройка логирования
logging.basicConfig(
    filename=os.path.join(log_directory, 'bot.log'),  # Путь к файлу лога
    level=logging.INFO,  # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат сообщений
    datefmt='%Y-%m-%d %H:%M:%S'  # Формат даты и времени
)
# Настройка уровня логирования для сторонних библиотек
logging.getLogger("telegram").setLevel(logging.WARNING)  # Игнорировать DEBUG и INFO от telegram
# Создание логгера
logger = logging.getLogger()

def log_info(message):
    """Логирование информационных сообщений."""
    logger.info(message)

def log_warning(message):
    """Логирование предупреждений."""
    logger.warning(message)

def log_error(message):
    """Логирование ошибок."""
    logger.error(message)

def log_debug(message):
    """Логирование отладочных сообщений."""
    logger.debug(message)

# Пример использования
if __name__ == "__main__":
    log_info("Бот запущен.")
    log_debug("Это отладочное сообщение.")
    log_warning("Это предупреждение.")
    log_error("Это сообщение об ошибке.")
