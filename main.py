from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters, 
    ConversationHandler, 
    CallbackQueryHandler
)
from handlers.start_handler import (
    start, button_handler, city_selection_handler, handle_position_selection,
    salary_selection_handler, show_city_selection, number_of_vacancies_handler,
    CITY, POSITION, SALARY, NUMBER_OF_VACANCIES, HISTORY,
    favorite_callback_handler, history_callback_handler
)
from handlers.subscription_handlers import (
    add_subscription_handler, get_subscriptions_to_remove, cancel_unsubscription,
    unsubscribe_handler, GET_SUBSCRIPTIONS_NUMBERS
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
                MessageHandler(filters.TEXT & ~filters.COMMAND | filters.LOCATION, city_selection_handler),
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
            HISTORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        name="job_search_conversation",
        persistent=False
    )


    unsubscribe_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Отписаться$') & ~filters.COMMAND, unsubscribe_handler)],
        states={
            GET_SUBSCRIPTIONS_NUMBERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex('^Отмена$'), get_subscriptions_to_remove)
            ],
        },
        fallbacks=[MessageHandler(filters.Regex('^Отмена$') | filters.COMMAND, cancel_unsubscription)],
        name="unsubscribe_conversation",
        persistent=False
    )

    application.add_handler(job_search_conv)

    application.add_handler(unsubscribe_conv)

    # Обработчик для других кнопок главного меню
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))

    # Добавляем CallbackQueryHandler для избранного и похожих вакансий
    application.add_handler(CallbackQueryHandler(favorite_callback_handler, pattern=r'^(add_fav|remove_fav|related):'))

    # Добавляем CallbackQueryHandler для истории поиска
    application.add_handler(CallbackQueryHandler(history_callback_handler, pattern=r'^history:'))

    application.add_handler(CallbackQueryHandler(add_subscription_handler, pattern=r'^subscribe_updates$'))

    application.run_polling()


if __name__ == '__main__':
    main()