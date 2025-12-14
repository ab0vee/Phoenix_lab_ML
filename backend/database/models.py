"""
SQLAlchemy модели для работы с базой данных
Опционально: можно использовать для ORM вместо прямых SQL запросов
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Связи
    urls = relationship("UserUrl", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class UserUrl(Base):
    """Модель ссылки пользователя"""
    __tablename__ = 'user_urls'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default='active', index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_processed_at = Column(DateTime, nullable=True)
    meta_data = Column('metadata', JSON, nullable=True)  # metadata - зарезервированное имя в SQLAlchemy
    
    # Связи
    user = relationship("User", back_populates="urls")
    processing_results = relationship("UrlProcessingResult", back_populates="url", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserUrl(id={self.id}, url='{self.url[:50]}...', user_id={self.user_id})>"


class UrlProcessingResult(Base):
    """Модель результата обработки ссылки"""
    __tablename__ = 'url_processing_results'
    
    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey('user_urls.id', ondelete='CASCADE'), nullable=False, index=True)
    original_text = Column(Text, nullable=True)
    summarized_text = Column(Text, nullable=True)
    paraphrased_text = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    processing_time = Column(Integer, nullable=True)  # в секундах
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    meta_data = Column('metadata', JSON, nullable=True)  # metadata - зарезервированное имя в SQLAlchemy
    
    # Связи
    url = relationship("UserUrl", back_populates="processing_results")
    
    def __repr__(self):
        return f"<UrlProcessingResult(id={self.id}, url_id={self.url_id})>"


class UserSession(Base):
    """Модель сессии пользователя"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Связи
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


# Функции для работы с БД
def get_engine(database_url: str):
    """Создать engine для подключения к БД"""
    return create_engine(database_url, echo=False)


def get_session(engine):
    """Создать сессию для работы с БД"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


# Пример использования:
if __name__ == "__main__":
    from config import settings
    
    # Создать engine
    engine = get_engine(settings.database_url)
    
    # Создать все таблицы (если их еще нет)
    # Base.metadata.create_all(bind=engine)
    
    # Пример работы с БД
    session = get_session(engine)
    
    try:
        # Получить всех пользователей
        users = session.query(User).all()
        print(f"Найдено пользователей: {len(users)}")
        
        # Получить ссылки пользователя
        if users:
            user = users[0]
            print(f"Ссылки пользователя {user.username}: {len(user.urls)}")
    
    finally:
        session.close()

