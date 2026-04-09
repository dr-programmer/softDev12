# Doctor Appointment Booking API

REST API система за записване на посещения при лични лекари.

## Изисквания

- Python 3.10+

## Инсталация и стартиране

```bash
# Създаване на виртуална среда
python3 -m venv venv
source venv/bin/activate

# Инсталиране на зависимости
pip install -r requirements.txt

# Стартиране на сървъра
uvicorn app.main:app --reload
```

Сървърът ще стартира на `http://localhost:8000`.

## API документация

След стартиране на сървъра, отворете:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Стартиране на тестове

```bash
pytest tests/ -v
```

## Технологичен стек

- **FastAPI** — уеб фреймуърк
- **SQLAlchemy** — ORM за база данни
- **SQLite** — база данни
- **JWT** — автентикация
- **pytest** — тестове
