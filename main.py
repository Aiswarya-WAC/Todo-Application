from fastapi import FastAPI
from auth import router as auth_router
from database import engine, Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
