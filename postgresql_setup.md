# PostgreSQL Setup Guide

## 1. Install PostgreSQL
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# On CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
```

## 2. Create Database and User
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

## 3. Install Python Packages
```bash
pip install psycopg2-binary python-dotenv
```

## 4. Configure Environment Variables
Add to your `.env` file:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=job_hunter
POSTGRES_USER=job_user
POSTGRES_PASSWORD=your_password
```

## 5. Database Schema
The following tables will be created automatically by the application:
- `vacancies` - stores job postings
- `users` - stores user accounts
- `favorites` - stores user's favorite jobs

## 6. Test Connection
Create a test script `test_db.py`:
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

## 7. Troubleshooting

### Permission Issues
If you get "permission denied for schema public" errors:
1. Connect to PostgreSQL as admin:
```bash
sudo -u postgres psql
```

2. Run these commands:
```sql
GRANT CREATE ON SCHEMA public TO job_user;
GRANT USAGE ON SCHEMA public TO job_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO job_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO job_user;
```

### Connection Issues
If connection fails:
1. Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

2. Check pg_hba.conf authentication:
```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```
Add line for local connections:
```
local   all             all                                     trust
```

3. Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

## 8. Run the Application
```bash
python main.py
