from typing import Dict, List, Optional
from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from services.database import DatabaseHandler
from utils.parse_salary import parse_salary

# Определение состояний для ConversationHandler
GET_SUBSCRIPTIONS_NUMBERS = 0

async def add_subscription_handler(
    db: DatabaseHandler,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle subscription addition """
    position = context.user_data["position"]
    if not position:
        await update.message.reply_text("Сначала выполните поиск вакансий")
        return ConversationHandler.END

    salary_from, salary_to = parse_salary(context.user_data.get('salary', 'Не указана'))
    salary_min=salary_from
    salary_max=salary_to
    city=context.user_data.get('city')
    city_id=context.user_data.get('city_id', 'Не указан')
    
    user_id = update.effective_user.id
    success = db.add_subscription(
        user_id=user_id,
        position=position,
        city=city,
        salary_min=salary_min,
        salary_max=salary_max,
        city_id=city_id,
    )
    
    # Форматируем информацию о зарплате
    salary_range = ""
    if salary_min is not None or salary_max is not None:
        min_salary = str(salary_min) if salary_min is not None else "?"
        max_salary = str(salary_max) if salary_max is not None else "?"
        salary_range = f" с зарплатой {min_salary} - {max_salary}"
    
    # Форматируем информацию о локации
    location_text = f" в {city}" if city else ""
    
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Избранное")],
        [KeyboardButton("История поиска")],
        [
            KeyboardButton("Аналитика"), 
            KeyboardButton("Подписки")
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if success:
        await update.message.reply_text(
            f"✅ Вы подписались на уведомления о вакансиях {position}{salary_range}{location_text}",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ Не удалось оформить подписку. Попробуйте позже.",
            reply_markup=reply_markup

        )
    

async def list_subscriptions_handler(
    db: DatabaseHandler,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle subscription listing and send response directly to user"""
    user_id = update.effective_user.id
    subscriptions = db.get_user_subscriptions(user_id)
    
    if not subscriptions:
        await update.message.reply_text('У вас пока нет активных подписок')
        return
    
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Избранное")],
        [KeyboardButton("История поиска")],
        [
            KeyboardButton("Аналитика"), 
            KeyboardButton("Отписаться")
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    message_text = "📋 Ваши активные подписки:\n\n"
    for index, sub in enumerate(subscriptions, start=1):
        message_text += (
            f"{index}. 🔹 Должность: {sub['position']}\n"
            f"   📍 Локация: {sub['city'] or 'Не указана'}\n"
            f"   💰 Зарплата: {sub['salary_min'] or '?'}-{sub['salary_max'] or '?'}\n"
            f"   📅 Создана: {sub['created_at'].strftime('%d.%m.%Y')}\n\n"
    )
    
    await update.message.reply_text(
        text=message_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def unsubscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Отмена")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Укажите через пробел номера подписок, которые вы хотите отменить.",
                                    reply_markup=reply_markup)
    return GET_SUBSCRIPTIONS_NUMBERS

async def get_subscriptions_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Избранное")],
        [KeyboardButton("История поиска")],
        [
            KeyboardButton("Аналитика"), 
            KeyboardButton("Подписки")
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    user_id = update.effective_user.id
    try:
        subscriptions_numbers = [int(x) for x in update.message.text.split()]
    except Exception:
        await update.message.reply_text("Неверный формат. Введите через пробел номера подписок для удаления.")
        return GET_SUBSCRIPTIONS_NUMBERS
    
    db = DatabaseHandler()
    subscriptions = db.get_user_subscriptions(user_id)
    for sub in subscriptions_numbers:
        try:
            sub_id = subscriptions[sub - 1]["id"]
        except Exception:
            await update.message.reply_text(f"Ошибка удаления подписки №{sub}")
        if db.remove_subscription(user_id, sub_id):
            continue
        else:
            await update.message.reply_text("❌ Ошибка удаления подписок",reply_markup=reply_markup)
            return ConversationHandler.END
    
    await update.message.reply_text("✅ Подписки удалены!",reply_markup=reply_markup)
    return ConversationHandler.END

async def cancel_unsubscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Поиск вакансий")],
        [KeyboardButton("Избранное")],
        [KeyboardButton("История поиска")],
        [
            KeyboardButton("Аналитика"), 
            KeyboardButton("Подписки")
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Выбери действие:\n\n"
        "🔍 Поиск вакансий\n"
        "⭐ Избранное\n"
        "⏳ История поиска\n"
        "📊 Аналитика и подписки",
        reply_markup=reply_markup
    )
    return ConversationHandler.END
