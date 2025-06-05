from typing import Dict, List, Optional
from datetime import datetime
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from services.database import DatabaseHandler
from utils.parse_salary import parse_salary

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
    location=context.user_data.get('city', 'Не указан')
    
    user_id = update.effective_user.id
    success = db.add_subscription(
        user_id=user_id,
        position=position,
        salary_min=salary_min,
        salary_max=salary_max,
        location=location
    )
    
    # Форматируем информацию о зарплате
    salary_range = ""
    if salary_min is not None or salary_max is not None:
        min_salary = str(salary_min) if salary_min is not None else "?"
        max_salary = str(salary_max) if salary_max is not None else "?"
        salary_range = f" с зарплатой {min_salary} - {max_salary}"
    
    # Форматируем информацию о локации
    location_text = f" в {location}" if location else ""
    
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
    subscriptions = db.get_active_subscriptions(user_id)
    
    if not subscriptions:
        await update.message.reply_text('У вас пока нет активных подписок')
        return
    
    message_text = "📋 Ваши активные подписки:\n\n"
    for index, sub in enumerate(subscriptions, start=1):
        message_text += (
            f"{index}. 🔹 Должность: {sub['position']}\n"
            f"   📍 Локация: {sub['location'] or 'Не указана'}\n"
            f"   💰 Зарплата: {sub['salary_min'] or '?'}-{sub['salary_max'] or '?'}\n"
            f"   📅 Создана: {sub['created_at'].strftime('%d.%m.%Y')}\n\n"
    )
    
    await update.message.reply_text(
        text=message_text,
        parse_mode='Markdown'
    )

async def remove_subscription_handler(
    db: DatabaseHandler,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    subscription_id: int
) -> Dict[str, str]:
    """Handle subscription removal"""
    query = update.callback_query
    await query.answer()

    success = db.remove_subscription(subscription_id)
    return {
        'success': success,
        'message': '✅ Подписка удалена!' if success else '❌ Ошибка удаления подписки'
    }

async def clear_subscriptions_handler(
    db: DatabaseHandler,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> Dict[str, str]:
    """Handle clearing all subscriptions"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    success = db.clear_all_subscriptions(user_id)
    return {
        'success': success,
        'message': '✅ Все подписки удалены!' if success else '❌ Ошибка очистки подписок'
    }