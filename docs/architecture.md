# Архитектура на проекта

## 1. Структура на проекта

Проектът следва трислойна архитектура:

```
app/
├── main.py              # Входна точка — създаване на FastAPI приложението
├── database.py          # Конфигурация на база данни (SQLAlchemy engine, сесия)
├── auth.py              # JWT автентикация и оторизация
├── models.py            # ORM модели (таблици в базата данни)
├── schemas.py           # Pydantic схеми (входни/изходни данни)
├── routers/             # HTTP слой — обработка на заявки
│   ├── auth.py          # Вход (login)
│   ├── doctors.py       # Регистрация на лекар, управление на работно време
│   ├── patients.py      # Регистрация на пациент
│   └── appointments.py  # Създаване, отмяна, преглед на посещения
└── services/            # Бизнес логика
    ├── schedule.py      # Разрешаване на работно време
    └── appointment.py   # Валидация на посещения
tests/
├── conftest.py          # Тестови фикстури (in-memory DB, тестов клиент)
├── test_doctors.py      # Тестове за лекари и работно време
├── test_patients.py     # Тестове за пациенти
└── test_appointments.py # Тестове за посещения
```

### Слоеве и отговорности

| Слой | Файлове | Отговорност |
|------|---------|-------------|
| **Routers** | `routers/*.py` | HTTP обработка — парсване на заявки, връщане на отговори, HTTP кодове |
| **Services** | `services/*.py` | Бизнес логика — валидация, изчисления, правила |
| **Models** | `models.py` | Persistence — ORM маппинг към SQLite таблици |
| **Schemas** | `schemas.py` | Договор — дефиниция на входни и изходни данни |
| **Auth** | `auth.py` | Сигурност — JWT токени, хеширане на пароли, role guards |

---

## 2. Ключови класове и модели

### ORM модели (`models.py`)

- **User** — базов потребител с email, парола и роля (`doctor`/`patient`)
- **Doctor** — име и адрес, свързан с User чрез споделен първичен ключ
- **Patient** — име, телефон и личен лекар (FK към Doctor)
- **DoctorWorkingHours** — интервали от работно време за конкретен ден от седмицата
- **DoctorScheduleChange** — временна или постоянна промяна на работно време
- **ScheduleChangeHours** — интервали на работно време за дадена промяна
- **Appointment** — посещение с начало, край, пациент, лекар и статус

### Ключови методи

- `get_working_hours_for_date(db, doctor_id, date)` (`services/schedule.py`) — определя работното време на лекар за конкретна дата с приоритет: временна промяна > постоянна промяна > базово работно време
- `validate_appointment(db, patient_id, start, end)` (`services/appointment.py`) — проверява всички бизнес правила за създаване на посещение
- `create_access_token(user_id, role)` (`auth.py`) — генерира JWT токен
- `get_current_user(token, db)` (`auth.py`) — FastAPI dependency за извличане на текущия потребител от токен

---

## 3. Обосновка на архитектурни решения

### Защо FastAPI?
- Автоматична генерация на OpenAPI/Swagger документация
- Вградена валидация чрез Pydantic
- Dependency injection система (`Depends()`) за чиста автентикация
- Модерен Python фреймуърк с добра документация

### Защо SQLite + SQLAlchemy?
- SQLite не изисква инсталация или конфигурация — грейдърът само стартира `uvicorn`
- SQLAlchemy предоставя ORM модели, които директно се мапват към UML диаграми
- За мащаба на проекта SQLite е напълно достатъчен

### Защо интервали за работно време (не ден-ниво)?
Работното време е моделирано като множество интервали (`start_time`, `end_time`) за даден ден. Това позволява естествено моделиране на обедни почивки без отделна таблица. Например:
- Понеделник 09:00-12:00 + 13:00-17:00 = обедна почивка от 12:00 до 13:00

### Защо единна `users` таблица?
Една таблица за автентикация с колона `role` опростява JWT логиката — не са необходими отделни login потоци за лекари и пациенти. Специфичните данни се пазят в `doctors`/`patients` таблици, свързани чрез споделен първичен ключ.

### Защо soft-delete за отмяна?
Отменените посещения получават `status = "cancelled"` вместо да се изтриват. Това запазва историята и предотвратява бъгове при проверка за припокриване.

---

## 4. UML диаграми

### Клас диаграма (Entity Relationship)

```mermaid
classDiagram
    class User {
        +int id
        +str email
        +str hashed_password
        +str role
    }

    class Doctor {
        +int id
        +str name
        +str address
    }

    class Patient {
        +int id
        +str name
        +str phone
        +int doctor_id
    }

    class DoctorWorkingHours {
        +int id
        +int doctor_id
        +int day_of_week
        +str start_time
        +str end_time
    }

    class DoctorScheduleChange {
        +int id
        +int doctor_id
        +str change_type
        +date effective_date
        +date end_date
    }

    class ScheduleChangeHours {
        +int id
        +int change_id
        +int day_of_week
        +str start_time
        +str end_time
    }

    class Appointment {
        +int id
        +int doctor_id
        +int patient_id
        +datetime start_time
        +datetime end_time
        +str status
    }

    User "1" -- "0..1" Doctor : id
    User "1" -- "0..1" Patient : id
    Doctor "1" -- "*" DoctorWorkingHours : doctor_id
    Doctor "1" -- "*" DoctorScheduleChange : doctor_id
    DoctorScheduleChange "1" -- "*" ScheduleChangeHours : change_id
    Doctor "1" -- "*" Patient : doctor_id
    Doctor "1" -- "*" Appointment : doctor_id
    Patient "1" -- "*" Appointment : patient_id
```

### Секвенциална диаграма — Създаване на посещение

```mermaid
sequenceDiagram
    participant P as Пациент
    participant R as Router (appointments.py)
    participant A as Auth (auth.py)
    participant S as Service (appointment.py)
    participant Sch as Service (schedule.py)
    participant DB as Database

    P->>R: POST /api/appointments/ {start, end}
    R->>A: get_current_user(token)
    A->>DB: Query User by JWT sub
    A-->>R: current_user (patient)

    R->>S: validate_appointment(db, patient_id, start, end)
    S->>S: Check start < end
    S->>S: Check start >= now + 24h
    S->>DB: Query Patient → get doctor_id
    S->>Sch: get_working_hours_for_date(db, doctor_id, date)
    Sch->>DB: Check temporary changes
    Sch->>DB: Check permanent changes
    Sch->>DB: Get base working hours
    Sch-->>S: working_intervals
    S->>S: Check appointment within intervals
    S->>DB: Check overlapping appointments
    S-->>R: doctor_id (validation passed)

    R->>DB: INSERT Appointment
    R-->>P: 201 Created {appointment}
```

### Секвенциална диаграма — Разрешаване на работно време

```mermaid
sequenceDiagram
    participant C as Caller
    participant S as schedule.py
    participant DB as Database

    C->>S: get_working_hours_for_date(db, doctor_id, date)

    S->>DB: Query temporary change covering date
    alt Temporary change exists
        S->>DB: Get ScheduleChangeHours for day_of_week
        S-->>C: intervals from temporary change
    else No temporary change
        S->>DB: Query latest permanent change <= date
        alt Permanent change exists
            S->>DB: Get ScheduleChangeHours for day_of_week
            S-->>C: intervals from permanent change
        else No permanent change
            S->>DB: Get DoctorWorkingHours for day_of_week
            S-->>C: intervals from base hours
        end
    end
```
