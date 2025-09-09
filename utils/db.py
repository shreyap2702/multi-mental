import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
load_dotenv()
db_url = os.getenv('DATABASE_URL')

engine = create_engine(db_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)

