# db_setup.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    learning_style = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    subject = Column(String)
    score = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

def setup_database(db_path="sqlite:///data/learning_companion.db"):
    """Set up SQLite database."""
    os.makedirs("data", exist_ok=True)
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session

if __name__ == "__main__":
    engine, Session = setup_database()
    session = Session()
    # Add a test user
    test_user = UserProfile(name="Test User", learning_style="Visual")
    session.add(test_user)
    session.commit()
    print(f"Added test user with ID: {test_user.id}")
    session.close()