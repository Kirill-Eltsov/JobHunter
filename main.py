from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from handlers.start_handler import (
    start, button_handler, city_selection_handler, handle_position_selection,
    handle_position_input, salary_selection_handler, show_city_selection, number_of_vacancies_handler,
    CITY, POSITION, SALARY, NUMBER_OF_VACANCIES
)
from utils.logger import log_warning
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('MY_TOKEN')

def main():
    """Запускает бота."""
    application = ApplicationBuilder().token(TOKEN).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # Обработчик для поиска вакансий
    job_search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Поиск вакансий$'), button_handler)],
        states={
            CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, city_selection_handler),
            ],
            POSITION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_position_selection),
            ],
            SALARY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, salary_selection_handler),
            ],
            NUMBER_OF_VACANCIES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, number_of_vacancies_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        name="job_search_conversation",
        persistent=False
    )
    application.add_handler(job_search_conv)

    # Обработчик для других кнопок главного меню
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    application.run_polling()


if __name__ == '__main__':
    main()