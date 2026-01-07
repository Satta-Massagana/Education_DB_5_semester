import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from pymongo import MongoClient
from pymongo.errors import PyMongoError

POSTGRES_URL = "postgresql://postgres:postgres@localhost:5437/postgres"
MONGODB_URL = "mongodb://localhost:27017/"

# ==============================================
# POSTGRESQL: ВРЕДОНОСНЫЙ ВВОД (psycopg2)
# ==============================================
if False:
    print("1. Уязвимый psycopg2 (DROP сработает)")
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)")
        conn.commit()
        print("   Таблица users создана")
        
        malicious = "test'; DROP TABLE users; --"
        query = f"INSERT INTO users (name) VALUES ('{malicious}')"
        cur.execute(query)
        conn.commit()
        print(f"   Инъекция: '{malicious}' -> таблица УДАЛЕНА")
        
        cur.execute("SELECT * FROM users")
        print("   Таблица пуста:", cur.fetchall())
        
    except Exception as e:
        print(f"   Ошибка: {e}")
    finally:
        conn.close()

# ==============================================
# POSTGRESQL: ЗАЩИТА psycopg2
# ==============================================
if True:
    print("2. Безопасный psycopg2")
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)")
    conn.commit()
    
    malicious = "test'; DROP TABLE users; --"
    cur.execute("INSERT INTO users (name) VALUES (%s)", (malicious,))
    conn.commit()
    
    cur.execute("SELECT * FROM users WHERE name = %s", (malicious,))
    result = cur.fetchall()
    print(f"   Запись сохранена: {result}")
    
    cur.execute("DROP TABLE users")
    conn.commit()
    conn.close()

# ==============================================
# POSTGRESQL: ЗАЩИТА SQLAlchemy
# ==============================================
if True:
    print("3. Безопасный SQLAlchemy")
    engine = create_engine(POSTGRES_URL)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name TEXT)"))
        conn.commit()
        
        malicious = "test'; DROP TABLE users; --"
        try:
            conn.execute(text("INSERT INTO users (name) VALUES (:name)"), {"name": malicious})
            conn.commit()
            print("   INSERT сработал")
        except SQLAlchemyError as e:
            conn.rollback()
            print(f"   Ошибка откатилась: {e}")
        
        result = conn.execute(text("SELECT * FROM users WHERE name = :name"), {"name": malicious}).fetchall()
        print(f"   SELECT: {result}")
        
        conn.execute(text("DROP TABLE users"))
        conn.commit()

# ==============================================
# НАСТРОЙКА ПРАВ PostgreSQL
# ==============================================
if False:
    print("4. SQL для настройки прав")
    sql_commands = """
-- Отключить DROP/CREATE для всех
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM postgres;
GRANT USAGE ON SCHEMA public TO postgres;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO postgres;
    """
    print(sql_commands)

# ==============================================
# MONGODB: БАЗОВАЯ АУТЕНТИФИКАЦИЯ
# ==============================================
if True:
    print("5. MongoDB без auth (работает)")
    try:
        client = MongoClient(MONGODB_URL)
        client.admin.command('ping')
        print("   Подключение без auth OK")
        
        db = client.testdb
        collection = db.users
        collection.insert_one({"name": "test_user", "protected": True})
        print("   Данные записаны")
        
    except PyMongoError as e:
        print(f"   MongoDB ошибка: {e}")

if False:
    print("6. MongoDB с auth (после настройки)")
    secure_client = MongoClient('mongodb://admin:securepass@localhost:27017/')
    secure_client.admin.command('ping')
    print("   Auth подключение OK")
