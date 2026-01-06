import pytest
import psycopg2
from faker import Faker
from contextlib import contextmanager
import os
from datetime import datetime

fake = Faker()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5437')),
    'dbname': os.getenv('POSTGRES_DB', 'postgres'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

@pytest.fixture(scope="session")
def db_connection():
    """Фикстура для подключения к БД"""
    with get_db_connection() as conn:
        conn.autocommit = True
        cur = conn.cursor()
        # Создаем тестовую таблицу
        cur.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                age INTEGER CHECK (age >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        yield conn
        # Очистка после всех тестов
        cur.execute("DROP TABLE IF EXISTS test_users")
        conn.commit()

@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

@pytest.fixture
def clean_table(db_connection):
    """Очищает таблицу перед каждым тестом"""
    cur = db_connection.cursor()
    cur.execute("DELETE FROM test_users")
    db_connection.commit()
    yield
    cur.execute("DELETE FROM test_users")
    db_connection.commit()

class TestUsersCRUD:
    """Тесты CRUD операций с пользователями"""
    
    def test_create_user_success(self, db_connection, clean_table):
        """Позитив: Создание пользователя"""
        user_data = {
            'name': fake.name(),
            'email': fake.email(),
            'age': fake.random_int(min=18, max=80)
        }
        
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES (%s, %s, %s) RETURNING id",
            (user_data['name'], user_data['email'], user_data['age'])
        )
        user_id = cur.fetchone()[0]
        db_connection.commit()
        
        # Проверяем создание
        cur.execute("SELECT * FROM test_users WHERE id = %s", (user_id,))
        created_user = cur.fetchone()
        assert created_user[1] == user_data['name']
        assert created_user[2] == user_data['email']
        assert created_user[3] == user_data['age']
    
    def test_create_user_duplicate_email(self, db_connection, clean_table):
        """Негатив: Дубликат email"""
        email = fake.email()
        
        # Создаем первого пользователя
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES ('Test User', %s, 25)",
            (email,)
        )
        db_connection.commit()
        
        # Пробуем создать второго с тем же email
        with pytest.raises(psycopg2.errors.UniqueViolation):
            cur.execute(
                "INSERT INTO test_users (name, email, age) VALUES ('Another User', %s, 30)",
                (email,)
            )
            db_connection.commit()
    
    def test_create_user_negative_age(self, db_connection, clean_table):
        """Негатив: Отрицательный возраст"""
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur = db_connection.cursor()
            cur.execute(
                "INSERT INTO test_users (name, email, age) VALUES ('Test', 'test@example.com', -5)"
            )
            db_connection.commit()
    
    def test_read_user_exists(self, db_connection, clean_table):
        """Позитив: Чтение существующего пользователя"""
        # Создаем тестового пользователя
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES ('John Doe', 'john@example.com', 30) RETURNING id"
        )
        user_id = cur.fetchone()[0]
        db_connection.commit()
        
        # Читаем
        cur.execute("SELECT * FROM test_users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        assert user is not None
        assert user[1] == 'John Doe'
    
    def test_read_user_not_exists(self, db_connection, clean_table):
        """Негатив: Чтение несуществующего пользователя"""
        cur = db_connection.cursor()
        cur.execute("SELECT * FROM test_users WHERE id = %s", (999,))
        user = cur.fetchone()
        assert user is None
    
    def test_update_user_success(self, db_connection, clean_table):
        """Позитив: Обновление пользователя"""
        # Создаем
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES ('Old Name', 'old@example.com', 25) RETURNING id"
        )
        user_id = cur.fetchone()[0]
        db_connection.commit()
        
        # Обновляем
        cur.execute(
            "UPDATE test_users SET name = %s, age = %s WHERE id = %s",
            ('New Name', 35, user_id)
        )
        db_connection.commit()
        
        # Проверяем
        cur.execute("SELECT name, age FROM test_users WHERE id = %s", (user_id,))
        updated_user = cur.fetchone()
        assert updated_user[0] == 'New Name'
        assert updated_user[1] == 35
    
    def test_update_user_not_exists(self, db_connection, clean_table):
        """Негатив: Обновление несуществующего"""
        cur = db_connection.cursor()
        result = cur.execute(
            "UPDATE test_users SET name = 'New' WHERE id = %s", (999,)
        )
        assert cur.rowcount == 0  # Не обновлено ни одной строки
    
    def test_delete_user_success(self, db_connection, clean_table):
        """Позитив: Удаление пользователя"""
        # Создаем
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES ('To Delete', 'delete@example.com', 40) RETURNING id"
        )
        user_id = cur.fetchone()[0]
        db_connection.commit()
        
        # Удаляем
        cur.execute("DELETE FROM test_users WHERE id = %s", (user_id,))
        db_connection.commit()
        
        # Проверяем удаление
        cur.execute("SELECT * FROM test_users WHERE id = %s", (user_id,))
        assert cur.fetchone() is None
    
    def test_delete_user_not_exists(self, db_connection, clean_table):
        """Негатив: Удаление несуществующего"""
        cur = db_connection.cursor()
        cur.execute("DELETE FROM test_users WHERE id = %s", (999,))
        assert cur.rowcount == 0

    def test_list_users(self, db_connection, clean_table):
        """Позитив: Список пользователей"""
        # Создаем несколько пользователей
        users_data = [
            ('User1', fake.email(), 25),
            ('User2', fake.email(), 30),
            ('User3', fake.email(), 35)
        ]
        
        cur = db_connection.cursor()
        for name, email, age in users_data:
            cur.execute("INSERT INTO test_users (name, email, age) VALUES (%s, %s, %s)", (name, email, age))
        db_connection.commit()
        
        # Получаем список
        cur.execute("SELECT COUNT(*) FROM test_users")
        count = cur.fetchone()[0]
        assert count == 3

@pytest.mark.parametrize("invalid_email", [
    "invalid-email",
    "@example.com",
    "user@",
    "user@example"
])
def test_create_user_invalid_email(self, db_connection, clean_table, invalid_email):
    """Негатив: Неверный формат email"""
    with pytest.raises(psycopg2.errors.InvalidTextRepresentation):
        cur = db_connection.cursor()
        cur.execute(
            "INSERT INTO test_users (name, email, age) VALUES ('Test', %s, 25)",
            (invalid_email,)
        )
        db_connection.commit()
