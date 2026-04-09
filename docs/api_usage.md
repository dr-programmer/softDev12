# Ползване на API-а

## Общ преглед

API-ят използва JSON формат за входни и изходни данни. Всички заявки (без регистрация и вход) изискват JWT автентикация чрез `Authorization: Bearer <token>` хедър.

Базов URL: `http://localhost:8000`

---

## Автентикация

### POST /api/auth/register/doctor — Регистрация на лекар

**Входни данни:**
```json
{
  "email": "dr.smith@example.com",
  "password": "securepass",
  "name": "Д-р Смит",
  "address": "ул. Медицинска 123",
  "working_hours": [
    {"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
    {"day_of_week": 0, "start_time": "13:00", "end_time": "17:00"},
    {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}
  ]
}
```

`day_of_week`: 0 = Понеделник, 1 = Вторник, ..., 6 = Неделя. Могат да се зададат няколко интервала за един ден (за моделиране на обедна почивка).

**Изходни данни (201 Created):**
```json
{
  "id": 1,
  "email": "dr.smith@example.com",
  "name": "Д-р Смит",
  "address": "ул. Медицинска 123",
  "role": "doctor",
  "working_hours": [
    {"day_of_week": 0, "start_time": "09:00", "end_time": "12:00"},
    {"day_of_week": 0, "start_time": "13:00", "end_time": "17:00"},
    {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"}
  ]
}
```

**Грешки:**
- `409 Conflict` — имейлът вече е регистриран

---

### POST /api/auth/register/patient — Регистрация на пациент

**Входни данни:**
```json
{
  "email": "patient@example.com",
  "password": "securepass",
  "name": "Иван Иванов",
  "phone": "+359888123456",
  "doctor_id": 1
}
```

**Изходни данни (201 Created):**
```json
{
  "id": 2,
  "email": "patient@example.com",
  "name": "Иван Иванов",
  "phone": "+359888123456",
  "doctor_id": 1,
  "role": "patient"
}
```

**Грешки:**
- `409 Conflict` — имейлът вече е регистриран
- `404 Not Found` — лекарят не е намерен

---

### POST /api/auth/login — Вход

**Входни данни:**
```json
{
  "email": "dr.smith@example.com",
  "password": "securepass"
}
```

**Изходни данни (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Грешки:**
- `401 Unauthorized` — грешен имейл или парола

**Използване на токена:** Добавете хедър `Authorization: Bearer <access_token>` към всички следващи заявки.

---

## Управление на работно време (изисква лекарска автентикация)

### PUT /api/doctors/me/working-hours — Промяна на работното време

**Входни данни:**
```json
{
  "working_hours": [
    {"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"},
    {"day_of_week": 0, "start_time": "13:00", "end_time": "16:00"}
  ]
}
```

**Изходни данни (200 OK):**
```json
{
  "message": "Working hours updated",
  "working_hours": [...]
}
```

**Грешки:**
- `401 Unauthorized` — липсва или невалиден токен
- `403 Forbidden` — потребителят не е лекар

---

### POST /api/doctors/me/schedule-changes/temporary — Временна промяна

Не може да има повече от 1 активна временна промяна.

**Входни данни:**
```json
{
  "effective_date": "2026-05-01",
  "end_date": "2026-05-03",
  "working_hours": [
    {"day_of_week": 3, "start_time": "10:00", "end_time": "14:00"}
  ]
}
```

**Изходни данни (201 Created):**
```json
{
  "id": 1,
  "doctor_id": 1,
  "change_type": "temporary",
  "effective_date": "2026-05-01",
  "end_date": "2026-05-03",
  "working_hours": [...]
}
```

**Грешки:**
- `409 Conflict` — вече съществува временна промяна
- `422 Unprocessable Entity` — крайната дата е преди началната

---

### POST /api/doctors/me/schedule-changes/permanent — Постоянна промяна

Началната дата трябва да е поне 1 седмица в бъдещето.

**Входни данни:**
```json
{
  "effective_date": "2026-05-15",
  "working_hours": [
    {"day_of_week": 0, "start_time": "09:00", "end_time": "13:00"}
  ]
}
```

**Изходни данни (201 Created):**
```json
{
  "id": 2,
  "doctor_id": 1,
  "change_type": "permanent",
  "effective_date": "2026-05-15",
  "end_date": null,
  "working_hours": [...]
}
```

**Грешки:**
- `422 Unprocessable Entity` — датата е по-рано от 1 седмица в бъдещето

---

## Посещения (изисква автентикация)

### POST /api/appointments/ — Създаване на посещение

Само пациенти могат да създават посещения. Лекарят се определя автоматично (личният лекар на пациента).

**Условия:**
- Посещението трябва да е поне 24 часа в бъдещето
- Посещението трябва да е изцяло в работното време на лекаря
- Не трябва да се припокрива с други активни посещения при същия лекар
- Началото и краят трябва да са в един и същи ден

**Входни данни:**
```json
{
  "start_time": "2026-05-05T10:00:00",
  "end_time": "2026-05-05T10:30:00"
}
```

**Изходни данни (201 Created):**
```json
{
  "id": 1,
  "doctor_id": 1,
  "patient_id": 2,
  "start_time": "2026-05-05T10:00:00",
  "end_time": "2026-05-05T10:30:00",
  "status": "active"
}
```

**Грешки:**
- `400 Bad Request` — нарушено условие (24ч, работно време, грешни часове)
- `403 Forbidden` — потребителят не е пациент
- `409 Conflict` — припокриване с друго посещение

---

### DELETE /api/appointments/{id} — Отмяна на посещение

Може да се отмени от пациента или лекаря. Не може да се отмени по-късно от 12 часа преди началото.

**Изходни данни (200 OK):**
```json
{
  "id": 1,
  "doctor_id": 1,
  "patient_id": 2,
  "start_time": "2026-05-05T10:00:00",
  "end_time": "2026-05-05T10:30:00",
  "status": "cancelled"
}
```

**Грешки:**
- `400 Bad Request` — вече е отменено, или по-малко от 12ч до началото
- `403 Forbidden` — потребителят не е свързан с посещението
- `404 Not Found` — посещението не е намерено

---

### GET /api/appointments/ — Преглед на посещения

Връща всички посещения на текущия потребител (като пациент или лекар).

**Изходни данни (200 OK):**
```json
[
  {
    "id": 1,
    "doctor_id": 1,
    "patient_id": 2,
    "start_time": "2026-05-05T10:00:00",
    "end_time": "2026-05-05T10:30:00",
    "status": "active"
  }
]
```

---

## HTTP кодове за грешки

| Код | Описание |
|-----|----------|
| 400 | Невалидна заявка (нарушено бизнес правило) |
| 401 | Неоторизиран достъп (липсва или невалиден токен) |
| 403 | Забранен достъп (грешна роля) |
| 404 | Ресурсът не е намерен |
| 409 | Конфликт (дубликат или припокриване) |
| 422 | Невалидни данни (грешен формат или неизпълнено условие) |

Всички грешки връщат JSON в следния формат:
```json
{
  "detail": "Описателно съобщение за грешката"
}
```
