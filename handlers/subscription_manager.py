import time
from typing import List, Dict
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from utils.logger import log_error
from services.database import DatabaseHandler

class SubscriptionManager:
    def __init__(self):
        self.db = DatabaseHandler()

    async def add_subscription(self, user_id: int, position: str, city: str, salary_range: str) -> bool:
        """Add a new job subscription"""
        try:
            return self.db.execute_query("""
                INSERT INTO subscriptions 
                (user_id, position, city, salary_range, last_checked)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, position, city, salary_range) DO UPDATE
                SET last_checked = EXCLUDED.last_checked
            """, (user_id, position, city, salary_range, int(time.time())))
        except Exception as e:
            log_error(f"Error adding subscription: {e}")
            return False

    async def remove_subscription(self, user_id: int, subscription_id: int) -> bool:
        """Remove a subscription"""
        try:
            return self.db.execute_query("""
                DELETE FROM subscriptions
                WHERE user_id = %s AND id = %s
            """, (user_id, subscription_id))
        except Exception as e:
            log_error(f"Error removing subscription: {e}")
            return False

    async def get_user_subscriptions(self, user_id: int) -> List[Dict]:
        """Get all subscriptions for a user"""
        try:
            rows = self.db.execute_query("""
                SELECT id, position, city, salary_range, last_checked
                FROM subscriptions
                WHERE user_id = %s
            """, (user_id,), fetch=True)
            return [{
                'id': row[0],
                'position': row[1],
                'city': row[2],
                'salary_range': row[3],
                'last_checked': row[4]
            } for row in rows]
        except Exception as e:
            log_error(f"Error getting subscriptions: {e}")
            return []

    async def check_new_vacancies(self, subscription: Dict) -> List[Dict]:
        """Check for new vacancies matching subscription"""
        try:
            salary_min = subscription['salary_range'].split('-')[0] if '-' in subscription['salary_range'] else 0
            return self.db.execute_query("""
                SELECT * FROM vacancies
                WHERE position = %s
                AND city = %s
                AND salary >= %s
                AND created_at > %s
                ORDER BY created_at DESC
            """, (
                subscription['position'],
                subscription['city'],
                salary_min,
                subscription['last_checked']
            ), fetch=True)
        except Exception as e:
            log_error(f"Error checking new vacancies: {e}")
            return []

    async def notify_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE, vacancies: List[Dict]):
        """Send notification about new vacancies"""
        for vacancy in vacancies:
            message = (
                f"🔔 Новая вакансия по вашей подписке!\n"
                f"🏢 Компания: {vacancy['company']}\n"
                f"💼 Должность: {vacancy['position']}\n"
                f"📍 Город: {vacancy['city']}\n"
                f"💰 Зарплата: {vacancy['salary']}\n"
                f"🔗 Ссылка: {vacancy['url']}"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message
            )
