from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Создаем базовый класс с помощью DeclarativeBase
class Base(DeclarativeBase):
    pass

# Настройка подключения
engine = create_engine('postgresql+psycopg2://postgres:postgres@localhost:5437/postgres', echo=True)
Session = sessionmaker(bind=engine)

# ORM-модель User
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    age = Column(Integer, nullable=True)

    posts = relationship('Post', back_populates='user', cascade="all, delete")

# ORM-модель Post (связь с User через user_id)
class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship('User', back_populates='posts')


# Функции работы с сессией и ORM
def create_user(name, email, age=None):
    session = Session()
    try:
        user = User(name=name, email=email, age=age)
        session.add(user)
        session.commit()
        print(f"User created with id: {user.id}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error creating user: {e}")
    finally:
        session.close()

def create_post(user_id, title, content=None):
    session = Session()
    try:
        post = Post(user_id=user_id, title=title, content=content)
        session.add(post)
        session.commit()
        print(f"Post created with id: {post.id} for user_id: {user_id}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error creating post: {e}")
    finally:
        session.close()

def read_user(user_id):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        return user
    except SQLAlchemyError as e:
        print(f"Error reading user: {e}")
        return None
    finally:
        session.close()

def update_user(user_id, name=None, email=None, age=None):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            print("User not found")
            return
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email
        if age is not None:
            user.age = age
        session.commit()
        print(f"Updated user with id: {user_id}")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error updating user: {e}")
    finally:
        session.close()

def delete_user(user_id):
    session = Session()
    try:
        user = session.query(User).filter(User.id == user_id).one_or_none()
        if not user:
            print("User not found")
            return
        session.delete(user)  # Каскадное удаление связанных posts
        session.commit()
        print(f"Deleted user with id: {user_id} and their posts")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error deleting user: {e}")
    finally:
        session.close()

# Пример использования функций
if __name__ == "__main__":
    create_user("Alice", "alice3@example.com", 30)
    user = read_user(1)
    print(user)
    create_post(2, "First post", "Hello world!")
    update_user(1, age=41)
    #delete_user(1)
