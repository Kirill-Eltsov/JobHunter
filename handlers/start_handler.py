from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils.logger import log_warning, log_info, log_error
from services.hh_service import fetch_vacancies, parse_vacancies

# Определение состояний для ConversationHandler
CITY, POSITION, SALARY, SEARCH = range(4)

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
    # Создаем клавиатуру с кнопками городов
    keyboard = [[KeyboardButton(city)] for city in CITIES]
    keyboard.append([KeyboardButton("Другой город")])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите город для поиска вакансий:", reply_markup=reply_markup)


async def city_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора города."""
    city = update.message.text
    
    if city == "Другой город":
        await update.message.reply_text("Пожалуйста, введите название города:")
        context.user_data['awaiting_custom_city'] = True
        return CITY
    
    # Сохраняем выбранный город
    context.user_data['city'] = city
    context.user_data['city_id'] = CITY_IDS.get(city.lower(), None)
    
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
    
    # Запускаем поиск вакансий
    await search_vacancies(update, context)
    return ConversationHandler.END


async def search_vacancies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Поиск вакансий на основе выбранных параметров."""
    city = context.user_data.get('city', 'Не указан')
    city_id = context.user_data.get('city_id', None)
    position = context.user_data.get('position', 'Не указана')
    salary_range = context.user_data.get('salary', 'Не указана')
    
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
    vacancies_data = await fetch_vacancies(position, city_id, salary_from, salary_to)
    
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
        [KeyboardButton("История поиска")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Хотите выполнить новый поиск или воспользоваться другими функциями?", 
                                   reply_markup=reply_markup)
