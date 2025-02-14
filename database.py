from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) #allows multiple threads ro use same db
# session maker is a factory for database sessions 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#declarative_base is a base class for defining ORM Models  ,
#  Any model (table) created must inherit from 'Base' class
Base = declarative_base()

def get_db():
    db = SessionLocal()  # Creates a new database session
    try:
        yield db  # Provides the session for use
    finally:
        db.close()  # Closes the session after use
