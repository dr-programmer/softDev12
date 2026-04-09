from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, doctors

app = FastAPI(title="Doctor Appointment Booking API")

app.include_router(auth.router)
app.include_router(doctors.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Doctor Appointment Booking API"}
