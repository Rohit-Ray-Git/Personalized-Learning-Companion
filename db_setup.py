# db_setup.py
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    learning_style = Column(String)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String)
    score = Column(Float)
    phase = Column(String)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def setup_database():
    engine = create_engine("sqlite:///learning_companion.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session

if __name__ == "__main__":
    engine, Session = setup_database()
    print("Database setup complete.")