# Инструкция по установке PostgreSQL

## 1. Установка PostgreSQL
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# On CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
```

## 2. Создание БД и пользователя
```bash
sudo -u postgres psql
CREATE DATABASE job_hunter;
CREATE USER job_user WITH PASSWORD 'your_password';
ALTER USER job_user WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE job_hunter TO job_user;
ALTER DATABASE job_hunter OWNER TO job_user;
GRANT CREATE ON SCHEMA public TO job_user;
GRANT USAGE ON SCHEMA public TO job_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO job_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO job_user;
\q
```

## 3. Настройка переменных окружения
Добавить в .env файл:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=job_hunter
POSTGRES_USER=job_user
POSTGRES_PASSWORD=your_password
```

## 4. Тестирование соединения
Создать скрипт `test_db.py`:
```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    dbname=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD')
)
print("Connection successful!")
conn.close()
```


## 5. Запуск приложения
```bash
python main.py
