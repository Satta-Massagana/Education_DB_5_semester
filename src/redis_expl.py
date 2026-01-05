import redis
import json
import time
import threading
import os
from typing import Callable

# Подключение к Redis (localhost:6379)
r = redis.Redis(host='localhost', port=6379, decode_responses=True, db=0)

## Кеширование с TTL
def get_cached(key: str, compute: Callable[[], str], ttl: int = 300) -> str:
    """Получает из кеша или вычисляет с TTL."""
    cached = r.get(key)
    if cached:
        print(f"Закешированное значение: {cached}")
        return cached
    value = compute()
    r.setex(key, ttl, value)
    print(f"Закешированное значение: {value}")
    return value

def expensive_computation() -> str:
    time.sleep(2)
    return f"{time.ctime()}"

## Pub/Sub модель
CHANNEL = 'mychannel'

def publisher_thread():
    """Публикует 5 сообщений."""
    for i in range(5):
        message = f"Сообщение #{i} на {time.ctime()}"
        r.publish(CHANNEL, message)
        print(f"[PUBLISHER] Опубликовано: {message}")
        time.sleep(1)

def subscriber_thread():
    """Подписывается и слушает."""
    pubsub = r.pubsub()
    pubsub.subscribe(CHANNEL)
    print(f"[SUBSCRIBER] Подписка на {CHANNEL}...")
    for message in pubsub.listen():
        if message['type'] == 'message':
            print(f"[SUBSCRIBER] Получено из {message['channel']}: {message['data']}")
        time.sleep(0.1)

## Очередь задач
QUEUE_NAME = 'task_queue'

def add_task(task_data: dict):
    """Добавляет задачу в очередь."""
    task_id = f"task:{int(time.time()*1000)}"
    task = {**task_data, 'id': task_id, 'timestamp': time.time()}
    r.lpush(QUEUE_NAME, json.dumps(task))
    print(f"[QUEUE] Добавлена задача {task_id}: {task_data['action']}")

def process_queue_worker():
    """Обработчик очередей (worker)."""
    print("[QUEUE WORKER] Запуск обработчика...")
    time.sleep(10)
    while True:
        task_json = r.brpop(QUEUE_NAME, timeout=2)
        if task_json:
            _, task_str = task_json
            task = json.loads(task_str)
            task_id = task['id']
            print(f"[WORKER] Обработка {task_id}: {task['action']}")
            time.sleep(2)  # Имитация работы
            r.setex(f"done:{task_id}", 3600, json.dumps(task))
            print(f"[WORKER] Завершена {task_id}")
        else:
            print("[WORKER] Очередь пуста, ожидание...")


# Заменить на "if True" для тестирования

if False:
    print("\n=== ТЕСТ КЕША ===")
    # Первый вызов - вычислит
    get_cached("test_cache", expensive_computation, ttl=20)
    # Второй - из кеша
    get_cached("test_cache", expensive_computation)
    # Проверка TTL
    time.sleep(25)
    # После TTL - кеш пустой
    cached_value = r.get("test_cache")
    print(f"Закешированное значение: {cached_value if cached_value else 'кеш пустой'}")

if False:
    print("\n=== ТЕСТ PUB/SUB ===")
    # Запуск subscriber и publisher параллельно
    sub_thread = threading.Thread(target=subscriber_thread, daemon=True)
    sub_thread.start()
    time.sleep(1)
    publisher_thread()
    time.sleep(3)  # Ждем сообщений

if True:
    print("\n=== ТЕСТ ОЧЕРЕДИ ===")
    # Worker в фоне
    worker_thread = threading.Thread(target=process_queue_worker, daemon=True)
    worker_thread.start()
    time.sleep(1)
    
    # Добавляем задачи
    add_task({'action': 'отправить email', 'user': 'alice'})
    add_task({'action': 'генерировать отчет', 'type': 'daily'})
    add_task({'action': 'очистить кеш'})
    
    # Ждем обработки
    time.sleep(20)