# 🤖 Smart Agent

AI-агент с поддержкой RAG, Human-in-the-Loop и интеграцией с внешними инструментами.

## 🛠 Стек

- **Backend:** FastAPI, SQLAlchemy 2.0 (async), Alembic
- **AI/ML:** LangGraph, LangChain, OpenAI
- **Vector DB:** Qdrant
- **Relational DB:** PostgreSQL 16
- **DevOps:** Docker Compose

## 📊 База данных

### PostgreSQL (порт 5433) хранит:

- Документы и их метаданные
- Историю диалогов
- Pending actions для Human-in-the-Loop

### Qdrant (порт 6333) хранит:

- Эмбеддинги документов
- Гибридный поиск (Dense + Sparse vectors)

## 🚀 Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/dimasimakov1212/smart_agent.git
cd smart_agent
```

### 2. Настроить окружение по .env.example

### 3. Установить зависимости
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 4. Запустить инфраструктуру
```bash
docker compose up -d
```

### 5. Проверить статус
```bash
docker compose ps
```
Контейнеры должны быть в статусе Up (healthy)


### 6. Создать миграции
```bash
alembic revision --autogenerate -m "Краткое описание изменений"
```

### 7. Применить миграции
```bash
alembic upgrade head
```

### 8. Проверить результат применения миграций
```bash
docker exec -it smart_agent_postgres psql -U postgres -d smart_agent -c "\dt"
```

### 9. При необходимости отката последней миграции применить
```bash
alembic downgrade -1
```
