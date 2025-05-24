import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from utils.logger import log_warning, log_info, log_error
from services.hh_service import fetch_vacancies, parse_vacancies, get_vacancies_stats, get_city_id_by_city_name
from services.database import DatabaseHandler
from services.osm_service import get_city_by_location

# Определение состояний для ConversationHandler
CITY, POSITION, SALARY, NUMBER_OF_VACANCIES, SEARCH, HISTORY = range(6)

# Предопределенные города
CITIES = ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск", "Казань", "Другой город"]
POSITIONS_PER_PAGE = 4
# Предопределенные должности
POSITIONS = ["Разработчик", "Дизайнер", "Менеджер",
 "Аналитик", "Тестировщик", "DevOps-инженер", "Андроид-разработчик", "Ios-разработчик", "C++ developer", "C# dev"]
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
        await show_favorites(update, context)
        return ConversationHandler.END
    elif message_text == "История поиска":
        await show_search_history(update, context)
        return HISTORY
    else:
        return ConversationHandler.END


async def show_city_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать пользователю выбор города для поиска вакансий."""
    # Создаем клавиатуру с кнопками городов и определением местоположения
    keyboard = [[KeyboardButton(CITIES[i]),KeyboardButton(CITIES[i+1]) ] for i in range(0, len(CITIES), 2)]
    keyboard.append([KeyboardButton("Определить местоположение", request_location=True)])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Выберите город для поиска вакансий или напишите его вручную", reply_markup=reply_markup)


async def city_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора города."""
    if update.message.location:
        # Получаем координаты
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        # Определяем город по координатам
        city = await get_city_by_location(lat, lon)
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
    city_id = await get_city_id_by_city_name(city)
    if not city_id:
        await update.message.reply_text("Не удалось определить ID города, попробуйте ввести название заново ")
        return CITY
        
    context.user_data['city_id'] = city_id
    await update.message.reply_text(f"Вы выбрали город: {city}")
    await show_position_selection(update, context)
    return POSITION


async def custom_city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ввода пользовательского города."""
    city = update.message.text
    city_id = await get_city_id_by_city_name(city)
    if not city_id:
        await update.message.reply_text("Ошибка в названии города, попробуйте ввести название заново ")
        return CITY
    # Сохраняем введенный город
    context.user_data['city'] = city
    context.user_data['city_id'] = city_id

    await update.message.reply_text(f"Вы выбрали город: {city}")
    await show_position_selection(update, context)
    return POSITION


async def show_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Показать пользователю выбор должности с пагинацией."""
    # Вычисляем диапазон должностей для текущей страницы
    start_idx = page * POSITIONS_PER_PAGE
    end_idx = start_idx + POSITIONS_PER_PAGE
    current_positions = POSITIONS[start_idx:end_idx]
    
    # Создаем клавиатуру с кнопками должностей
    keyboard = [[KeyboardButton(current_positions[i]), KeyboardButton(current_positions[i+1])] for i in range(0, len(current_positions), 2)]
    
    # Добавляем кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(KeyboardButton("← Назад"))
    if end_idx < len(POSITIONS):
        nav_buttons.append(KeyboardButton("Еще →"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([KeyboardButton("Другая должность")])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "Выберите должность для поиска вакансий",
        reply_markup=reply_markup
    )
    # Сохраняем текущую страницу
    context.user_data['current_page'] = page

def validate_position_symbols(position: str) -> bool:
    """Validate job title contains only allowed characters."""
    pattern = r'^[a-zA-Zа-яА-ЯёЁ\s-]+$'
    return bool(re.fullmatch(pattern, position))

def validate_position_length(position: str) -> bool:
    """Validate job title length"""
    length = len(position)
    return 2 <= length <= 30

async def handle_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора должности с учетом пагинации."""
    text = update.message.text
    current_page = context.user_data.get('current_page', 0)
    
    if text == "← Назад":
        await show_position_selection(update, context, page=current_page - 1)
        return
    
    if text == "Еще →":
        await show_position_selection(update, context, page=current_page + 1)
        return
    
    if text == "Другая должность":
        await update.message.reply_text(
            "Пожалуйста, введите желаемую должность:",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data['awaiting_custom_position'] = True
        return
    
    # Handle custom position input with validation
    if context.user_data.get('awaiting_custom_position', False):
        if not validate_position_symbols(text):
            await update.message.reply_text(
                "Некорректное название должности. Используйте только буквы, пробелы и дефисы.\n"
                "Пожалуйста, введите должность снова:"
            )
            return
        
        if not validate_position_length(text):
            await update.message.reply_text(
                "Название должности слишком короткое (длинное). Введите не менее 2 и не более 30 символов\n"
                "Пожалуйста, введите должность снова:"
            )
            return
        
        context.user_data['awaiting_custom_position'] = False
        context.user_data['position'] = text
        await update.message.reply_text(
            f"Вы выбрали должность: {text}",
            reply_markup=ReplyKeyboardRemove()
        )
        await show_salary_selection(update, context)
        return SALARY
    
    # Сохраняем выбранную должность
    context.user_data['position'] = text
    await update.message.reply_text(
        f"Вы выбрали должность: {text}",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_salary_selection(update, context)
    return SALARY


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
    number_of_vacancies = context.user_data.get('number_of_vacancies', 3)

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

    # Сохраняем запрос в историю
    db_handler = DatabaseHandler()
    db_handler.save_search_history(
        user_id=update.effective_user.id,
        position=position,
        city=city,
        salary_range=salary_range,
        vacancies_count=len(vacancies)
    )
    db_handler.close()

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

        context.user_data[f'vacancy_{vacancy["id"]}'] = vacancy
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('Добавить в избранное', callback_data=f'add_fav:{vacancy["id"]}')]
        ])
        await update.message.reply_text(vacancy_text, reply_markup=keyboard)

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

# --- Новый CallbackQueryHandler для избранного ---
async def favorite_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    db_handler = DatabaseHandler()
    data = query.data.split(':')
    action = data[0]
    vacancy_id = data[1]
    db_id = int(data[2]) if len(data) > 2 else None

    if action == 'add_fav':
        # vacancy_data должен быть сохранён в context.user_data при показе вакансий
        vacancy_data = context.user_data.get(f'vacancy_{vacancy_id}')
        if vacancy_data:
            db_handler.add_to_favorites(user_id, vacancy_data)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text('Вакансия добавлена в избранное!')
    elif action == 'remove_fav' and db_id:
        db_handler.remove_from_favorites(user_id, db_id)
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text('Вакансия удалена из избранного!')
    db_handler.close()

# --- Изменяем обработку кнопки "Избранное" ---
async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db_handler = DatabaseHandler()
    favorites = db_handler.get_favorites(user_id)
    db_handler.close()
    if not favorites:
        await update.message.reply_text('У вас нет избранных вакансий.')
        return
    for fav in favorites:
        salary = fav['salary']
        salary_info = 'Не указана'
        if salary['from'] and salary['to']:
            salary_info = f"{salary['from']} - {salary['to']} {salary['currency']}"
        elif salary['from']:
            salary_info = f"от {salary['from']} {salary['currency']}"
        elif salary['to']:
            salary_info = f"до {salary['to']} {salary['currency']}"
        text = (f"{fav['title']}\nКомпания: {fav['company']}\nГород: {fav['city']}\nЗарплата: {salary_info}\nСсылка: {fav['url']}")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton('Удалить из избранного', callback_data=f'remove_fav:{fav["id"]}:{fav["db_id"]}')]
        ])
        await update.message.reply_text(text, reply_markup=keyboard)

async def show_search_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю поиска с пагинацией."""
    user_id = update.effective_user.id
    page = context.user_data.get('history_page', 1)
    
    db_handler = DatabaseHandler()
    history, total_count = db_handler.get_search_history(user_id, page=page)
    db_handler.close()

    if not history:
        await update.message.reply_text("У вас пока нет истории поиска.")
        return

    # Формируем сообщение с историей
    message = "📜 История поиска:\n\n"
    for i, item in enumerate(history, 1):
        message += (f"{i}. Должность: {item['position']}\n"
                   f"   Город: {item['city']}\n"
                   f"   Зарплата: {item['salary_range']}\n"
                   f"   Найдено вакансий: {item['vacancies_count']}\n"
                   f"   Дата: {item['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n")

    # Добавляем информацию о страницах
    total_pages = (total_count + 4) // 5  # Округление вверх
    message += f"\nСтраница {page} из {total_pages}"

    # Создаем клавиатуру для навигации
    keyboard = []
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"history:prev:{page}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"history:next:{page}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Если это первый показ истории (не навигация), отправляем новое сообщение
    if not update.callback_query:
        await update.message.reply_text(message, reply_markup=reply_markup)
    else:
        # Если это навигация, обновляем существующее сообщение
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup
        )

async def history_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки навигации в истории поиска."""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(':')
    action = data[1]
    current_page = int(data[2])
    
    if action == 'prev':
        new_page = current_page - 1
    elif action == 'next':
        new_page = current_page + 1
    else:
        return
    
    context.user_data['history_page'] = new_page
    # Передаем query в show_search_history для обновления существующего сообщения
    await show_search_history(update, context)
