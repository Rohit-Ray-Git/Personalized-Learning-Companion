# src/models/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    learning_style = Column(String)  # e.g., "Visual", "Auditory"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    subject = Column(String)
    score = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)