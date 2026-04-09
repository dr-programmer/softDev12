from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import auth, doctors, patients


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Doctor Appointment Booking API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)


@app.get("/")
def root():
    return {"message": "Doctor Appointment Booking API"}
