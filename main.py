import os
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime
from dotenv import load_dotenv
from utils.db import init_db, get_session
from fastapi import Body
from agents.coordinator import coordinator_agent

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
    tasks: str | None = None
    pain_points: str | None = None
    raw_thoughts: str

class EntryCreate(SQLModel):
    tasks: str | None = None
    pain_points: str | None = None
    raw_thoughts: str

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

@app.post("/entries/")
def create_entry(userid : int, entry: EntryCreate, session: Session = Depends(get_session)):
    
    user = session.exec(select(User).where(User.id == userid)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = datetime.utcnow().date()
    existing_entry = session.exec(
        select(Entry).where(
            Entry.user_id == userid,
            Entry.date >= datetime.combine(today, datetime.min.time()),
            Entry.date <= datetime.combine(today, datetime.max.time())
        )
    ).first()

    if existing_entry:
        raise HTTPException(status_code=400, detail="User has already created an entry today")
    
    db_entry = Entry(
        user_id=userid,
        tasks=entry.tasks,
        pain_points=entry.pain_points,
        raw_thoughts=entry.raw_thoughts
    )
    
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry
    
@app.get("/entries/{entry_id}")
def fetch_entries(entry_id: int, session: Session = Depends(get_session)):
    entry = session.get(Entry, entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail= "Entry not found")
    return entry 

@app.get("/users/{user_id}/entries")
def get_user_entries(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="No User Found")
    
    entries = session.exec(select(Entry).where(Entry.user_id == user_id)).all()
    if not entries:
        raise HTTPException(status_code=404, detail="No Entries Found")
    
    return entries

@app.get("/users/{user_id}/entries/today")
def get_today_entry(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="No User Found")
    
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    
    query = select(Entry).where(
        (Entry.user_id == user_id) & 
        (Entry.date >= start) & 
        (Entry.date <= end)
    )
    today_entry = session.exec(query).first()
    
    if not today_entry:
        raise HTTPException(status_code=404, detail="No Entry Found For Today")
    
    return today_entry

coordinator = coordinator_agent()

@app.post("/entries/{entry_id}/analyze")
def analysis_endpoint(entry_id: int, session = Depends(get_session)):
    
    entry = session.get(Entry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # Gather content to send to the coordinator
    entry_content = {
        "tasks": entry.tasks,
        "pain_points": entry.pain_points,
        "raw_thoughts": entry.raw_thoughts
    }
    
    # Call the coordinator agent
    analysis = coordinator.handle(entry_content)
    
    return {
        "entry_id": entry.id,
        "date": entry.date,
        "content": entry_content,
        "analysis": analysis
    }

@app.put("/entries/{entry_id}")
def update_entry(entry_id: int, entry: EntryCreate, session: Session = Depends(get_session)):
    db_entry = session.get(Entry, entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db_entry.tasks = entry.tasks
    db_entry.pain_points = entry.pain_points
    db_entry.raw_thoughts = entry.raw_thoughts
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    return db_entry

@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, session: Session = Depends(get_session)):
    db_entry = session.get(Entry, entry_id)
    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    session.delete(db_entry)
    session.commit()
    return {"message": "Entry deleted successfully"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}
