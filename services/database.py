from typing import List, Dict, Optional
from config.database import Database
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.db = Database()
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database tables if they don't exist"""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    vacancy_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency TEXT,
                    city TEXT,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, vacancy_id)
                )
            """)

            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    position TEXT NOT NULL,
                    city TEXT NOT NULL,
                    avg_salary FLOAT NOT NULL,
                    vacancies_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    position TEXT NOT NULL,
                    city TEXT NOT NULL,
                    salary_range TEXT,
                    vacancies_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    position TEXT NOT NULL,  -- вместо search_query
                    salary_min INTEGER,
                    salary_max INTEGER,  -- переименовано для ясности
                    city_id INTEGER,
                    city TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    last_vacancy_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, position, city_id, salary_min, salary_max)  -- предотвращает дубли
                )
            """)
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def add_to_favorites(self, user_id: int, vacancy_data: Dict) -> bool:
        """Add vacancy to favorites"""
        try:
            return self.db.execute_query("""
                INSERT INTO favorites (
                    user_id, vacancy_id, title, company, salary_from,
                    salary_to, currency, city, url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, vacancy_id) DO NOTHING
            """, (
                user_id,
                vacancy_data.get('id', ''),
                vacancy_data['title'],
                vacancy_data.get('company', ''),
                vacancy_data.get('salary', {}).get('from'),
                vacancy_data.get('salary', {}).get('to'),
                vacancy_data.get('salary', {}).get('currency', ''),
                vacancy_data.get('area', ''),
                vacancy_data['url']
            ))
        except Exception as e:
            print(f"Error adding to favorites: {e}")
            return False

    def get_favorites(self, user_id: int) -> List[Dict]:
        """Get user's favorite vacancies"""
        try:
            rows = self.db.execute_query("""
                SELECT
                    id, vacancy_id, title, company, salary_from,
                    salary_to, currency, city, url, created_at
                FROM favorites
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,), fetch=True)
            
            return [{
                'db_id': row[0],
                'id': row[1],
                'title': row[2],
                'company': row[3],
                'salary': {
                    'from': row[4],
                    'to': row[5],
                    'currency': row[6]
                },
                'city': row[7],
                'url': row[8],
                'created_at': row[9]
            } for row in rows]
        except Exception as e:
            print(f"Error getting favorites: {e}")
            return []

    def remove_from_favorites(self, user_id: int, db_id: int) -> bool:
        """Remove vacancy from favorites"""
        try:
            return self.db.execute_query("""
                DELETE FROM favorites
                WHERE user_id = %s AND id = %s
            """, (user_id, db_id))
        except Exception as e:
            print(f"Error removing from favorites: {e}")
            return False

    def save_analytics(self, user_id: int, position: str, city: str,
                     avg_salary: float, vacancies_count: int) -> bool:
        """Save analytics data"""
        try:
            return self.db.execute_query("""
                INSERT INTO analytics (
                    user_id, position, city, avg_salary, vacancies_count
                ) VALUES (%s, %s, %s, %s, %s)
            """, (user_id, position, city, avg_salary, vacancies_count))
        except Exception as e:
            print(f"Error saving analytics: {e}")
            return False

    def get_last_analytics(self, user_id: int) -> Optional[Dict]:
        """Get last analytics for user"""
        try:
            rows = self.db.execute_query("""
                SELECT position, city, avg_salary, vacancies_count, created_at
                FROM analytics
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,), fetch=True)
            
            if rows:
                row = rows[0]
                return {
                    'position': row[0],
                    'city': row[1],
                    'avg_salary': row[2],
                    'vacancies_count': row[3],
                    'created_at': row[4]
                }
            return None
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return None

    def save_search_history(self, user_id: int, position: str, city: str, salary_range: str, vacancies_count: int) -> bool:
        """Save search query to history"""
        try:
            return self.db.execute_query("""
                INSERT INTO search_history (
                    user_id, position, city, salary_range, vacancies_count
                ) VALUES (%s, %s, %s, %s, %s)
            """, (user_id, position, city, salary_range, vacancies_count))
        except Exception as e:
            print(f"Error saving search history: {e}")
            return False

    def get_search_history(self, user_id: int, page: int = 1, per_page: int = 5) -> tuple:
        """Get user's search history with pagination"""
        try:
            # Получаем общее количество запросов
            count_result = self.db.execute_query("""
                SELECT COUNT(*) FROM search_history WHERE user_id = %s
            """, (user_id,), fetch=True)
            total_count = count_result[0][0] if count_result else 0

            # Получаем записи для текущей страницы
            offset = (page - 1) * per_page
            rows = self.db.execute_query("""
                SELECT id, position, city, salary_range, vacancies_count, created_at
                FROM search_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, per_page, offset), fetch=True)
            
            history = [{
                'id': row[0],
                'position': row[1],
                'city': row[2],
                'salary_range': row[3],
                'vacancies_count': row[4],
                'created_at': row[5]
            } for row in rows]

            return history, total_count
        except Exception as e:
            print(f"Error getting search history: {e}")
            return [], 0
        
    def add_subscription(self, user_id: int, position: str, city: str,
                   salary_min: int = None, salary_max: int = None, 
                   city_id: int = None) -> bool:
        """Add new subscription with clear parameters"""
        try:
            self.db.execute_query("""
                INSERT INTO subscriptions 
                (user_id, position, salary_min, salary_max, city_id, city)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, position, salary_min, salary_max, city_id, city))
            return True
        except Exception as e:
            print(f"Subscription exists or error: {e}")
            return False

    def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Optional[str | int | datetime]]]:
        """Get all active subscriptions for specified user.
        
        Args:
            user_id: Telegram user ID to fetch subscriptions for
            
        Returns:
            List of dictionaries with subscription details:
            [
                {
                    'id': int,
                    'position': str,
                    'salary_min': Optional[int],
                    'salary_max': Optional[int],
                    'city_id': int, 
                    'city': Optional[str],
                    'created_at': datetime
                },
                ...
            ]
            Empty list if no subscriptions found or error occurred
        """
        try:
            rows = self.db.execute_query(
                """
                SELECT 
                    id,
                    position,
                    salary_min, 
                    salary_max,
                    city_id,
                    city,
                    created_at
                FROM subscriptions
                WHERE user_id = %s
                ORDER BY created_at DESC
                """,
                (user_id,),
                fetch=True
            )
            
            if not rows:
                return []
                
            return [{
                'id': row[0],
                'position': row[1],
                'salary_min': row[2],
                'salary_max': row[3],
                'city_id': row[4],
                'city': row[5],
                'created_at': row[6]
            } for row in rows]
            
        except Exception as e:
            print(f"Error fetching subscriptions for user {user_id}: {str(e)}")
            return []


    def get_all_subscriptions(self) -> list[dict] | None:
        """
        Получает список всех активных подписок из базы данных
        
        Returns:
            list[dict]: Список подписок в формате:
                {
                    "id": int, 
                    "user_id": int,
                    "position": str,
                    "salary_min": int | None,
                    "salary_max": int | None,
                    "city_id": int,
                    "city": str | None,
                    "created_at": datetime,
                    "last_vacancy_time": datetime
                }
            None: В случае ошибки
        """
        try:
            result = self.db.execute_query(
                """
                SELECT 
                    id,
                    user_id,
                    position,
                    salary_min,
                    salary_max,
                    city_id,
                    city,
                    created_at,
                    last_vacancy_time
                FROM subscriptions
                """,
                fetch=True
            )
            
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "position": row[2],
                    "salary_min": row[3],
                    "salary_max": row[4],
                    "city_id": row[5],
                    "city": row[6],
                    "created_at": row[7],
                    "last_vacancy_time": row[8]
                }
                for row in result
            ] if result else []
        
        except Exception as e:
            print(f"Error fetching subscriptions: {e}")
            return None


    def clear_all_subscriptions(self, user_id: int) -> bool:
        """Remove all subscriptions for specified user.
        
        Args:
            user_id: Telegram user ID to clear subscriptions for
            
        Returns:
            bool: True if all subscriptions were deleted, False if error occurred
        """
        try:
            self.db.execute_query(
                """
                DELETE FROM subscriptions
                WHERE user_id = %s
                """,
                (user_id,)
            )
            return True
        except Exception as e:
            print(f"Error clearing subscriptions for user {user_id}: {e}")
            return False

    def remove_subscription(self, user_id: int, subscription_id: int) -> bool:
        """Remove a subscription"""
        try:
            return self.db.execute_query("""
                DELETE FROM subscriptions
                WHERE user_id = %s AND id = %s
            """, (user_id, subscription_id))
        except Exception as e:
            print(f"Error removing subscription: {e}")
            return False
        

    def update_last_vacancy_time(self, id: int) -> bool:
        """Update the last vacancy check time for a user to current timestamp"""
        try:
            return self.db.execute_query("""
                UPDATE subscriptions 
                SET last_vacancy_time = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (id,))
        except Exception as e:
            print(f"Error updating last vacancy time for subscription {id}: {e}")
            return False


    def close(self):
        """Close all database connections"""
        self.db.close_all_connections()
