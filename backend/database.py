import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+psycopg2://monitor:monitor@postgres:5432/monitoring")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine,autocommit=False,autoflush=False)
Base=declarative_base()

class User(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True)
    username=Column(String(80),unique=True,index=True,nullable=False)
    password_hash=Column(String(255),nullable=False)
    role=Column(String(20),nullable=False)

class Audit(Base):
    __tablename__="audit_logs"
    id=Column(Integer,primary_key=True)
    timestamp=Column(DateTime,default=datetime.utcnow,index=True)
    username=Column(String(80),nullable=False)
    role=Column(String(20),nullable=False)
    action=Column(String(100),nullable=False)
    details=Column(Text,default="")

class Maintenance(Base):
    __tablename__="maintenance_windows"
    id=Column(Integer,primary_key=True)
    server=Column(String(255),nullable=False,index=True)
    start=Column(DateTime,nullable=False)
    end=Column(DateTime,nullable=False)
    reason=Column(String(300),nullable=False)
    created_by=Column(String(80),nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
