from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    password: str
    

class Entry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    date: datetime = Field(default_factory=datetime.utcnow)
    gratitude: str
    tasks: str | None = None
    pain_points: str | None = None
    reflection: str | None = None
    
