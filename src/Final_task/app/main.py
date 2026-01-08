from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta
from .database import engine, Base, get_db
from .models import User as UserModel
from .routers import tasks, analytics
from .crud import get_user_by_username, create_user
from .schemas import UserCreate, Token, User as UserSchema
from .auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Tracker API", version="1.0.0")
app.include_router(tasks.router)
app.include_router(analytics.router)

app.openapi_tags = [
    {"name": "Tasks", "description": "CRUD операции с задачами"},
    {"name": "Analytics", "description": "Статистика и графики"},
    {"name": "Auth", "description": "Аутентификация"},
    {"name": "Health", "description": "Проверка состояния"},
]


@app.post("/register", response_model=UserSchema, tags=["Auth"])
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя:
    - Создает пользователя с ролью 'user' по умолчанию
    """
    try:
        # Проверка на существующего пользователя
        db_user = get_user_by_username(db, username=user_data.username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        # Хэширование пароля и создание пользователя
        hashed_password = get_password_hash(user_data.password)
        new_user = UserModel(
            username=user_data.username, hashed_password=hashed_password, role="user"
        )
        db_user = create_user(db, new_user)
        return User.model_validate(db_user)
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@app.post("/token", response_model=Token, tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Получить JWT токен для авторизации"""
    # Проверка пользователя и пароля
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    # Создание JWT токена
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health", tags=["Health"])
def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy", "service": "Task Tracker API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
