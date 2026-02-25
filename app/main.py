from fastapi import FastAPI, HTTPException, status, Depends
from app.db.database import engine, Base
from app.models import user

app=FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "PayExpress API running"}

