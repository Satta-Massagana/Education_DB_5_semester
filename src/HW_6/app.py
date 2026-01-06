import os
from fastapi import FastAPI
import redis
import psycopg2
import uvicorn

app = FastAPI()

# Используем переменные окружения
POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5437/postgres')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

@app.get("/")
def read_root():
    # Пример работы с PostgreSQL
    conn = psycopg2.connect(POSTGRES_URL)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    cur.close()
    conn.close()
    
    # Пример работы с Redis
    redis_client.incr("visit_count")
    visit_count = redis_client.get("visit_count") or "0"
    
    return {
        "message": "Приложение работает!",
        "postgres_version": db_version[0],
        "visit_count": visit_count
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)