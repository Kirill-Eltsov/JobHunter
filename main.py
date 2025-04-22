from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()

TOKEN = os.getenv('TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    current_update = update
    current_context = context
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
    await update.message.reply_html(text=welcome_message, reply_markup=reply_markup)


def main():
    """Запускает бота."""
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()


if __name__ == '__main__':
    print(TOKEN)
    main()
