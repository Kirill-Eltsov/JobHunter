import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool for PostgreSQL"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT'),
                database=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
        except Exception as e:
            print(f"Error initializing connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        return self.connection_pool.getconn()

    def release_connection(self, connection):
        """Release connection back to pool"""
        self.connection_pool.putconn(connection)

    def close_all_connections(self):
        """Close all connections in the pool"""
        self.connection_pool.closeall()

    def execute_query(self, query, params=None, fetch=False):
        """Execute SQL query with parameters"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
                return result
            conn.commit()
            return True
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error executing query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.release_connection(conn)
