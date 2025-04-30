from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from utils.logger import log_warning, log_info, log_error
from services.hh_service import fetch_vacancies, parse_vacancies, get_vacancies_stats
from services.database import DatabaseHandler

# Определение состояний для ConversationHandler
CITY, POSITION, SALARY, NUMBER_OF_VACANCIES, SEARCH = range(5)

# Предопределенные города
CITIES = ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань"]
# Предопределенные должности
POSITIONS = ["Разработчик", "Дизайнер", "Менеджер", "Аналитик", "Тестировщик"]
# Предопределенные диапазоны зарплат
SALARY_RANGES = ["Не важно", "0-30,000", "30,000-60,000", "60,000-100,000", "Более 100,000"]

# Словарь соответствия городов и их ID в API HH.ru
CITY_IDS = {
    "москва": "1",
    "санкт-петербург": "2",
    "екатеринбург": "3",
    "новосибирск": "4",
    "казань": "88"
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    user = update.effective_user
    welcome_message = (rf"""
    Привет, {user.mention_html()}!👋🎉
Я Ваш личный бот, готовый помочь Вам с поиском и анализом вакансий на бирже труда HeadHunter!
    """)

    # Создаем клавиатуру с кнопками
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Определить местоположение", request_location=True)],
        [KeyboardButton("Избранное")],
        [KeyboardButton("История поиска")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    log_warning(f"Пользователь запустил бота.")
    await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Поиск вакансий'."""
    message_text = update.message.text

    if message_text == "Поиск вакансий":
        await show_city_selection(update, context)
        return CITY
    elif message_text == "Аналитика":
        position = context.user_data.get('position')
        city_id = context.user_data.get('city_id')
        
        if not position or not city_id:
            await update.message.reply_text("Сначала выполните поиск вакансий")
            return ConversationHandler.END
            
        await update.message.reply_text("Собираем аналитику...")
        
        stats = await get_vacancies_stats(position, city_id, count=50)
        
        if stats['vacancies_count'] == 0:
            await update.message.reply_text("Не удалось собрать аналитику")
            return ConversationHandler.END
            
        exp_dist = stats['experience_distribution']
        total_exp = sum(exp_dist.values()) if sum(exp_dist.values()) > 0 else 1
        
        message = (f"📊 Аналитика по вакансиям:\n"
                  f"🔹 Должность: {position}\n"
                  f"🔹 Количество вакансий: {stats['vacancies_count']}\n\n"
                  f"💰 Зарплаты:\n"
                  f"- Средняя: {stats['avg_salary']} руб.\n"
                  f"- Медианная: {stats['median_salary']} руб.\n"  
                  f"- 25-й перцентиль: {stats['percentile_25']} руб.\n"
                  f"- 75-й перцентиль: {stats['percentile_75']} руб.\n"
                  f"- Минимальная: {stats['min_salary']} руб.\n"
                  f"- Максимальная: {stats['max_salary']} руб.\n\n"
                  f"👔 Опыт работы:\n"
                  f"- Без опыта: {exp_dist['no_experience']} ({round(exp_dist['no_experience']/total_exp*100)}%)\n"
                  f"- 1-3 года: {exp_dist['1-3_years']} ({round(exp_dist['1-3_years']/total_exp*100)}%)\n"
                  f"- 3-6 лет: {exp_dist['3-6_years']} ({round(exp_dist['3-6_years']/total_exp*100)}%)\n"
                  f"- Более 6 лет: {exp_dist['more_than_6']} ({round(exp_dist['more_than_6']/total_exp*100)}%)")
                  
        await update.message.reply_text(message)
        return ConversationHandler.END
        
    elif message_text == "Избранное":
        await update.message.reply_text("Функция избранного пока не реализована.")
        return ConversationHandler.END
    elif message_text == "История поиска":
        await update.message.reply_text("Функция истории поиска пока не реализована.")
        return ConversationHandler.END
    else:
        return ConversationHandler.END


async def show_city_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать пользователю выбор города для поиска вакансий."""
    # Создаем клавиатуру с кнопками городов и определением местоположения
    keyboard = [[KeyboardButton(city)] for city in CITIES]
    keyboard.append([KeyboardButton("Другой город")])
    keyboard.append([KeyboardButton("Определить местоположение", request_location=True)])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите город для поиска вакансий:", reply_markup=reply_markup)


async def city_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора города."""
    if update.message.location:
        # Получаем координаты
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        
        # Определяем город по координатам
        city = await get_city_by_coordinates(lat, lon)
        if not city:
            await update.message.reply_text("Не удалось определить город по местоположению")
            return CITY
    else:
        city = update.message.text
        if city == "Другой город":
            await update.message.reply_text("Пожалуйста, введите название города:")
            context.user_data['awaiting_custom_city'] = True
            return CITY

    # Сохраняем выбранный город
    context.user_data['city'] = city
    city_id = CITY_IDS.get(city.lower())
    if not city_id:
        await update.message.reply_text("Не удалось определить ID города")
        return CITY
        
    context.user_data['city_id'] = city_id
    await update.message.reply_text(f"Вы выбрали город: {city}")
    await show_position_selection(update, context)
    return POSITION


async def custom_city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода пользовательского города."""
    city = update.message.text

    # Сохраняем введенный город
    context.user_data['city'] = city
    context.user_data['city_id'] = CITY_IDS.get(city.lower(), None)

    await update.message.reply_text(f"Вы выбрали город: {city}")
    await show_position_selection(update, context)
    return POSITION


async def show_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать пользователю выбор должности для поиска вакансий."""
    # Создаем клавиатуру с кнопками должностей
    keyboard = [[KeyboardButton(position)] for position in POSITIONS]
    keyboard.append([KeyboardButton("Другая должность")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите должность для поиска вакансий:", reply_markup=reply_markup)


async def handle_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора должности."""
    position = update.message.text

    if position == "Другая должность":
        await update.message.reply_text("Пожалуйста, введите желаемую должность:")
        context.user_data['awaiting_custom_position'] = True
        return POSITION

    # Сохраняем выбранную должность
    context.user_data['position'] = position

    await update.message.reply_text(f"Вы выбрали должность: {position}")
    await show_salary_selection(update, context)
    return SALARY


async def handle_position_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода пользовательской должности."""
    position = update.message.text

    # Проверяем, ожидаем ли мы ввод города
    if context.user_data.get('awaiting_custom_city', False):
        context.user_data['awaiting_custom_city'] = False
        return await custom_city_handler(update, context)

    # Проверяем, ожидаем ли мы ввод должности
    if context.user_data.get('awaiting_custom_position', False):
        context.user_data['awaiting_custom_position'] = False
        # Сохраняем введенную должность
        context.user_data['position'] = position

        await update.message.reply_text(f"Вы выбрали должность: {position}")
        await show_salary_selection(update, context)
        return SALARY

    # Если мы не ожидаем ни город, ни должность, проверяем, может это кнопка из главного меню
    return await button_handler(update, context)


async def show_salary_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать пользователю выбор желаемой зарплаты."""
    # Создаем клавиатуру с кнопками зарплат
    keyboard = [[KeyboardButton(salary)] for salary in SALARY_RANGES]

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите желаемую зарплату:", reply_markup=reply_markup)


async def salary_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора зарплаты."""
    salary = update.message.text

    # Сохраняем выбранную зарплату
    context.user_data['salary'] = salary

    await update.message.reply_text(f"Вы выбрали желаемую зарплату: {salary}")

    # # Запускаем поиск вакансий
    # await search_vacancies(update, context)
    # return ConversationHandler.END
    await show_number_of_vacancies_selection(update, context)
    return NUMBER_OF_VACANCIES


async def show_number_of_vacancies_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать выбор количества вакансий."""
    keyboard = [
        [KeyboardButton("1")],
        [KeyboardButton("2")],
        [KeyboardButton("3")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Пожалуйста, выберите количество вакансий (1-3):", reply_markup=reply_markup)

async def number_of_vacancies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора количества вакансий."""
    number_of_vacancies = update.message.text

    if number_of_vacancies in ["1", "2", "3"]:
        context.user_data['number_of_vacancies'] = int(number_of_vacancies)
        await update.message.reply_text(f"Вы выбрали {number_of_vacancies} вакансий.")
        await search_vacancies(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите корректное количество вакансий (1-3).")
        return NUMBER_OF_VACANCIES

async def search_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск вакансий на основе выбранных параметров."""
    city = context.user_data.get('city', 'Не указан')
    city_id = context.user_data.get('city_id', None)
    position = context.user_data.get('position', 'Не указана')
    salary_range = context.user_data.get('salary', 'Не указана')
    number_of_vacancies = context.user_data.get('number_of_vacancies', 3)  # По умолчанию 3

    await update.message.reply_text(f"Ищем вакансии по следующим параметрам:\n"
                                    f"Город: {city}\n"
                                    f"Должность: {position}\n"
                                    f"Зарплата: {salary_range}\n\n"
                                    f"Пожалуйста, подождите...")

    # Парсим диапазон зарплаты
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

    # Получаем вакансии через API HH.ru
    vacancies_data = await fetch_vacancies(position, city_id, salary_from, salary_to, per_page=number_of_vacancies)

    if not vacancies_data:
        await update.message.reply_text("К сожалению, не удалось получить вакансии. Попробуйте позже.")
        return

    # Парсим полученные данные
    vacancies = parse_vacancies(vacancies_data)

    if not vacancies:
        await update.message.reply_text("По вашему запросу не найдено вакансий.")
        return

    # Отправляем результаты пользователю
    await update.message.reply_text(f"Найдено {len(vacancies)} вакансий:")

    for i, vacancy in enumerate(vacancies, 1):
        salary_info = "Не указана"
        if vacancy.get("salary"):
            salary_from = vacancy["salary"].get("from", "")
            salary_to = vacancy["salary"].get("to", "")
            salary_currency = vacancy["salary"].get("currency", "")

            if salary_from and salary_to:
                salary_info = f"{salary_from} - {salary_to} {salary_currency}"
            elif salary_from:
                salary_info = f"от {salary_from} {salary_currency}"
            elif salary_to:
                salary_info = f"до {salary_to} {salary_currency}"

        vacancy_text = (f"{i}. {vacancy['title']}\n"
                        f"Компания: {vacancy['company']}\n"
                        f"Город: {vacancy['area']}\n"
                        f"Зарплата: {salary_info}\n"
                        f"Ссылка: {vacancy['url']}\n")

        await update.message.reply_text(vacancy_text)

    # Возвращаем клавиатуру с основными кнопками
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Избранное")],
        [KeyboardButton("Аналитика")],
        [KeyboardButton("История поиска")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Хотите выполнить новый поиск или воспользоваться другими функциями?",
                                    reply_markup=reply_markup)
