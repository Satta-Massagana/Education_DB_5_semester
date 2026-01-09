# Task Tracker API
FastAPI приложение для управления задачами с ролевой моделью доступа, аналитикой и JWT аутентификацией.


## Архитектура
```mermaid
src/Final_task/app/  
├── main.py         # FastAPI приложение + роутеры  
├── config.py       # Pydantic Settings (.env)  
├── database.py     # SQLAlchemy engine + сессии  
├── models.py       # SQLAlchemy модели (User, Task)  
├── schemas.py      # Pydantic схемы  
├── crud.py         # CRUD операции  
├── auth.py         # JWT аутентификация  
└── routers/        # Роутеры  
    ├── tasks.py        # /tasks CRUD (пользователь/админ)  
    └── analytics.py    # /analytics графики (matplotlib)  
└── tests/          # Тесты  
```

### Основные возможности
- **RBAC**: user (свои задачи) / admin (все задачи)
- **JWT**: Bearer токены с ролями
- **PostgreSQL**: через SQLAlchemy ORM
- **Аналитика**: PNG графики задач (matplotlib/seaborn)
- **Тесты**: pytest

### API Endpoints
| Метод | Endpoint                    | Описание                          | Доступ      |
|-------|-----------------------------|-----------------------------------|-------------|
| POST  | `/register`                 | Регистрация                       | public      |
| POST  | `/token`                    | Логин JWT                         | public      |
| GET   | `/tasks/`                   | Список задач с пагинацией         | owner/admin |
| POST  | `/tasks/`                   | Создать задачу                    | user/admin  |
| GET   | `/tasks/{id}`               | Задача по ID                      | owner/admin |
| PUT   | `/tasks/{id}`               | Обновить задачу                   | owner/admin |
| DELETE| `/tasks/{id}`               | Удалить задачу                    | admin       |
| GET   | `/analytics/tasks-by-status`| График по статусам                | owner/admin |
| GET   | `/analytics/tasks-by-user`  | График по пользователям           | admin       |
| GET   | `/analytics/tasks-table`    | JSON таблица для фронтенда        | owner/admin |

### ERD диаграмма
```mermaid
┌─────────────────┐       1        N       ┌──────────────────┐  
│     USERS       │◄──────────────────────►│      TASKS       │  
├─────────────────┤                        ├──────────────────┤  
│ • id (PK)       │                        │ • id (PK)        │  
│ • username (UK) │                        │ • title          │  
│ • hashed_passwd │                        │ • description    │  
│ • role          │                        │ • status (ENUM)  │  
│ • is_active     │                        │ • owner_id (FK)  │  
│                 │                        │ • created_at     │  
└─────────────────┘                        └──────────────────┘  
```


## Быстрый запуск

### 1. Зависимости
cd src/Final_task  
pip install -r requirements.txt

### 2. Настройка .env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/taskdb  
SECRET_KEY=your-super-secret-key-here  
ACCESS_TOKEN_EXPIRE_MINUTES=30

### 3. Миграции БД
Таблицы создаются автоматически при первом запуске

### 4. Запуск
uvicorn app.main:app --reload

### 5. Swagger UI
http://127.0.0.1:8000/docs


## Тестирование
pytest app/tests/ -v --asyncio-mode=auto
