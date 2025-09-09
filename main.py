import os
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from dotenv import load_dotenv
from utils.db import init_db, get_session
load_dotenv()
db_url = os.getenv('DATABASE_URL')

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    password: str


class UserCreate(SQLModel):
    name: str
    password: str

class UserRead(SQLModel):
    id: int
    name: str

class Entry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    date: datetime = Field(default_factory=datetime.utcnow)
    gratitude: str
    tasks: str | None = None
    pain_points: str | None = None
    reflection: str | None = None
    
init_db()
    
app = FastAPI(title="Mental Wellness API")

@app.get("/")
def root():
    return {"message": "Mental Wellness API is running"}

@app.post("/users/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(name=user.name, password=user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user