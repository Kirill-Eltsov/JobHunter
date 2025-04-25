from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.start_handler import start, button_handler, city_selection_handler, \
    handle_position_input, salary_selection_handler, handle_position_selection
from utils.logger import log_warning
from config import TOKEN


def main():
    """Запускает бота."""
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^choose_vacancies$'))
    application.add_handler(CallbackQueryHandler(city_selection_handler, pattern='^city_'))
    application.add_handler(CallbackQueryHandler(handle_position_selection, pattern='^position_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_position_input))
    application.add_handler(CallbackQueryHandler(salary_selection_handler, pattern='^salary_'))

    application.run_polling()


if __name__ == '__main__':
    main()
