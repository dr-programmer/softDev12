from fastapi import FastAPI
from app.database import engine, Base

app = FastAPI(title="Doctor Appointment Booking API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Doctor Appointment Booking API"}
