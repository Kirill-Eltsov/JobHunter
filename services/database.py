import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'job_hunter.db'

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Инициализация базы данных и создание таблиц"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(DB_PATH)
        cursor = self.conn.cursor()
        
        # Создаем таблицу для избранных вакансий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        ''')
        
        # Создаем таблицу для хранения аналитики
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            city TEXT NOT NULL,
            avg_salary REAL NOT NULL,
            vacancies_count INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.conn.commit()

    def add_to_favorites(self, user_id: int, vacancy_data: Dict) -> bool:
        """Добавление вакансии в избранное"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO favorites (
                user_id, vacancy_id, title, company, 
                salary_from, salary_to, currency, city, url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
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
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Вакансия уже в избранном
            return False
        except Exception as e:
            print(f"Error adding to favorites: {e}")
            return False

    def get_favorites(self, user_id: int) -> List[Dict]:
        """Получение списка избранных вакансий"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            id, vacancy_id, title, company, 
            salary_from, salary_to, currency, city, url, created_at
        FROM favorites 
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,))
        
        favorites = []
        for row in cursor.fetchall():
            favorites.append({
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
            })
        return favorites

    def remove_from_favorites(self, user_id: int, db_id: int) -> bool:
        """Удаление вакансии из избранного"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            DELETE FROM favorites 
            WHERE user_id = ? AND id = ?
            ''', (user_id, db_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing favorite: {e}")
            return False

    def save_analytics(self, user_id: int, position: str, city: str, 
                      avg_salary: float, vacancies_count: int) -> bool:
        """Сохранение результатов аналитики"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO analytics (
                user_id, position, city, avg_salary, vacancies_count
            ) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, position, city, avg_salary, vacancies_count))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving analytics: {e}")
            return False

    def get_last_analytics(self, user_id: int) -> Optional[Dict]:
        """Получение последней аналитики пользователя"""
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT position, city, avg_salary, vacancies_count, created_at
        FROM analytics
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'position': row[0],
                'city': row[1],
                'avg_salary': row[2],
                'vacancies_count': row[3],
                'created_at': row[4]
            }
        return None

    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
