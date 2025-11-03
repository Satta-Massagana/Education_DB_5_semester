from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.sql import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5437/postgres', echo=True)

metadata = MetaData()

user_table = Table('users', metadata,
                   Column('id', Integer, primary_key=True),
                   Column('name', String(50), nullable=False),
                   Column('email', String(100), unique=True, nullable=False),
                   Column('age', Integer, nullable=True)
                   )

# Создаем таблицу в базе
metadata.create_all(engine)


def create_user(name, email, age=None):
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            stmt = insert(user_table).values(name=name, email=email, age=age)
            result = conn.execute(stmt)
            trans.commit()
            print(f"User created with id: {result.inserted_primary_key}")
        except SQLAlchemyError as e:
            trans.rollback()
            print(f"Error creating user: {e}")


def read_user(user_id):
    with engine.connect() as conn:
        try:
            stmt = select(user_table).where(user_table.c.id == user_id)
            result = conn.execute(stmt).fetchone()
            return result
        except SQLAlchemyError as e:
            print(f"Error reading user: {e}")
            return None


def update_user(user_id, name=None, email=None, age=None):
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            values = {}
            if name is not None:
                values['name'] = name
            if email is not None:
                values['email'] = email
            if age is not None:
                values['age'] = age
            if not values:
                print("No values to update")
                return
            stmt = update(user_table).where(user_table.c.id == user_id).values(**values)
            result = conn.execute(stmt)
            trans.commit()
            print(f"Updated {result.rowcount} record(s)")
        except SQLAlchemyError as e:
            trans.rollback()
            print(f"Error updating user: {e}")


def delete_user(user_id):
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            stmt = delete(user_table).where(user_table.c.id == user_id)
            result = conn.execute(stmt)
            trans.commit()
            print(f"Deleted {result.rowcount} record(s)")
        except SQLAlchemyError as e:
            trans.rollback()
            print(f"Error deleting user: {e}")


if __name__ == "__main__":
    create_user("Alice", "alice2@example.com", 30)
    user = read_user(1)
    print(user)
    update_user(1, age=41)
    delete_user(1)
