from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.logger import log_warning


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = (rf"""
    Привет, {user.mention_html()}!👋🎉
Я Ваш личный бот, готовый помочь Вам с поиском и анализом вакансий на бирже труда HeadHunter!
    """)

    keyboard = [
        [InlineKeyboardButton("Поиск вакансий", callback_data='choose_vacancies')],
        [InlineKeyboardButton("Избранное", callback_data='select')],
        [InlineKeyboardButton("История поиска", callback_data='search_history')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    log_warning(f"Пользователь запустил бота.")
    await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'choose_vacancies':
        await show_city_selection(query)


async def show_city_selection(query):
    """Показать пользователю выбор города для поиска вакансий."""
    keyboard = [
        [InlineKeyboardButton("Москва", callback_data='city_moscow')],
        [InlineKeyboardButton("Санкт-Петербург", callback_data='city_spb')],
        [InlineKeyboardButton("Екатеринбург", callback_data='city_ekb')],
        [InlineKeyboardButton("Другой город", callback_data='city_other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите город для поиска вакансий:", reply_markup=reply_markup)


async def city_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('city_'):
        city = query.data.split('_')[1]
        context.user_data['city'] = city  # Сохранение выбранного города

        # Объединяем оба сообщения в одно
        await query.edit_message_text(text=f"Вы выбрали город: {city}. Теперь выберите должность для поиска вакансий.")
        await show_position_selection(query)


async def show_position_selection(query):
    """Показать пользователю выбор должности для поиска вакансий."""
    keyboard = [
        [InlineKeyboardButton("Разработчик", callback_data='position_developer')],
        [InlineKeyboardButton("Дизайнер", callback_data='position_designer')],
        [InlineKeyboardButton("Менеджер", callback_data='position_manager')],
        [InlineKeyboardButton("Введите свою должность", callback_data='position_other')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Выберите должность для поиска вакансий:", reply_markup=reply_markup)


async def handle_position_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('position_'):
        if query.data == 'position_other':
            await update.message.reply_text("Пожалуйста, введите желаемую должность:")
            return  # Ожидание ввода должности от пользователя
        position = query.data.split('_')[1]
        context.user_data['position'] = position  # Сохранение выбранной должности

        # Объединяем сообщение и вызов функции show_salary_selection
        await update.message.reply_text(f"Вы выбрали должность: {position}. Теперь выберите желаемую зарплату.")
        await show_salary_selection(update)


async def handle_position_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    position = update.message.text
    context.user_data['position'] = position  # Сохранение введенной должности

    # Объединяем сообщение и вызов функции show_salary_selection
    await update.message.reply_text(f"Вы выбрали должность: {position}. Теперь выберите желаемую зарплату.")
    await show_salary_selection(update)


async def show_salary_selection(update):
    """Показать пользователю выбор желаемой зарплаты."""
    keyboard = [
        [InlineKeyboardButton("Не важно", callback_data='salary_any')],
        [InlineKeyboardButton("0-30,000", callback_data='salary_0_30000')],
        [InlineKeyboardButton("30,000-60,000", callback_data='salary_30000_60000')],
        [InlineKeyboardButton("60,000-100,000", callback_data='salary_60000_100000')],
        [InlineKeyboardButton("Более 100,000", callback_data='salary_100000_plus')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите желаемую зарплату:", reply_markup=reply_markup)


async def salary_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('salary_'):
        salary = query.data.split('_')[1:]
        salary_range = " ".join(salary).replace("_", "-")
        await query.edit_message_text(
            text=f"Вы выбрали желаемую зарплату: {salary_range}. Теперь можно выполнить поиск вакансий.")
        context.user_data['salary'] = salary_range  # Сохранение выбранной зарплаты
