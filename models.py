from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

DATABASE_URL = "sqlite+aiosqlite:///kuzkabuh.db"
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    inn = Column(String)
    services = Column(String)
    urgent = Column(Boolean, default=False)
    status = Column(String, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
