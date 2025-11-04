# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:Prabha%40012@localhost:5432/db1"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
