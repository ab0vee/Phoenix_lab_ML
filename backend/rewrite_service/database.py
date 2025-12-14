"""
Модуль для работы с базой данных
Использует модели из backend/database/models.py
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Импортируем модели из общего модуля
import sys
# Пытаемся найти database в разных местах
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database'),  # ../database
    '/backend/database',  # В Docker контейнере
    os.path.join(os.path.dirname(__file__), '..', 'database'),  # Альтернативный путь
]
for database_path in possible_paths:
    if os.path.exists(database_path) and database_path not in sys.path:
        sys.path.insert(0, database_path)
        break

try:
    from models import User, UserUrl, UrlProcessingResult
except ImportError as e:
    # Если не удалось импортировать, создаем заглушки
    logger.warning(f"Не удалось импортировать модели из backend/database/models.py: {e}")
    User = None
    UserUrl = None
    UrlProcessingResult = None

# Глобальная переменная для engine
_db_engine = None
_SessionLocal = None


def init_db(database_url: Optional[str] = None):
    """Инициализация подключения к БД"""
    global _db_engine, _SessionLocal
    
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'postgresql://phoenix_user:phoenix_password@postgres:5432/phoenix_lab')
    
    try:
        _db_engine = create_engine(database_url, echo=False, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_db_engine)
        logger.info(f"✅ База данных инициализирована: {database_url.split('@')[-1]}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return False


def get_db_session() -> Optional[Session]:
    """Получить сессию БД"""
    if _SessionLocal is None:
        if not init_db():
            return None
    return _SessionLocal()


# ============================================
# Функции для работы с пользователями
# ============================================

def get_or_create_user(username: str, email: Optional[str] = None) -> Optional[User]:
    """Получить пользователя или создать нового (для демо - без пароля)"""
    if not User:  # Проверка, что модели импортированы
        logger.error("Модели БД не импортированы")
        return None
    
    session = get_db_session()
    if not session:
        return None
    
    try:
        # Ищем существующего пользователя
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            # Создаем нового пользователя (для демо используем простой хеш)
            user = User(
                username=username,
                email=email,
                password_hash="demo_hash",  # В продакшене использовать bcrypt
                is_active=True
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"✅ Создан новый пользователь: {username} (ID: {user.id})")
        else:
            logger.info(f"✅ Найден пользователь: {username} (ID: {user.id})")
        
        return user
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Ошибка работы с пользователем: {e}")
        return None
    finally:
        session.close()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    session = get_db_session()
    if not session:
        return None
    
    try:
        return session.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка получения пользователя: {e}")
        return None
    finally:
        session.close()


# ============================================
# Функции для работы с URL
# ============================================

def save_user_url(user_id: int, url: str, title: Optional[str] = None, 
                  description: Optional[str] = None) -> Optional[UserUrl]:
    """Сохранить URL пользователя"""
    session = get_db_session()
    if not session:
        return None
    
    try:
        # Проверяем, не существует ли уже эта ссылка у пользователя
        existing_url = session.query(UserUrl).filter(
            UserUrl.user_id == user_id,
            UserUrl.url == url
        ).first()
        
        if existing_url:
            logger.info(f"✅ URL уже существует: {url}")
            return existing_url
        
        # Создаем новую запись
        user_url = UserUrl(
            user_id=user_id,
            url=url,
            title=title,
            description=description,
            status='active'
        )
        session.add(user_url)
        session.commit()
        session.refresh(user_url)
        logger.info(f"✅ URL сохранен: {url}")
        return user_url
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Ошибка сохранения URL: {e}")
        return None
    finally:
        session.close()


def get_user_urls(user_id: int, status: str = 'active') -> List[UserUrl]:
    """Получить все URL пользователя"""
    session = get_db_session()
    if not session:
        return []
    
    try:
        urls = session.query(UserUrl).filter(
            UserUrl.user_id == user_id,
            UserUrl.status == status
        ).order_by(UserUrl.created_at.desc()).all()
        return urls
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка получения URL: {e}")
        return []
    finally:
        session.close()


def get_url_by_id(url_id: int) -> Optional[UserUrl]:
    """Получить URL по ID"""
    session = get_db_session()
    if not session:
        return None
    
    try:
        return session.query(UserUrl).filter(UserUrl.id == url_id).first()
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка получения URL: {e}")
        return None
    finally:
        session.close()


# ============================================
# Функции для работы с результатами обработки
# ============================================

def save_processing_result(url_id: int, original_text: Optional[str] = None,
                          summarized_text: Optional[str] = None,
                          paraphrased_text: Optional[str] = None,
                          language: Optional[str] = None,
                          processing_time: Optional[float] = None,
                          meta_data: Optional[Dict] = None) -> Optional[UrlProcessingResult]:
    """Сохранить результат обработки URL"""
    session = get_db_session()
    if not session:
        return None
    
    try:
        result = UrlProcessingResult(
            url_id=url_id,
            original_text=original_text,
            summarized_text=summarized_text,
            paraphrased_text=paraphrased_text,
            language=language,
            processing_time=processing_time,
            meta_data=meta_data
        )
        session.add(result)
        
        # Обновляем last_processed_at в user_urls
        user_url = session.query(UserUrl).filter(UserUrl.id == url_id).first()
        if user_url:
            user_url.last_processed_at = datetime.utcnow()
        
        session.commit()
        session.refresh(result)
        logger.info(f"✅ Результат обработки сохранен для URL ID: {url_id}")
        return result
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Ошибка сохранения результата: {e}")
        return None
    finally:
        session.close()


def get_processing_results(url_id: int, limit: int = 10) -> List[UrlProcessingResult]:
    """Получить результаты обработки URL"""
    session = get_db_session()
    if not session:
        return []
    
    try:
        results = session.query(UrlProcessingResult).filter(
            UrlProcessingResult.url_id == url_id
        ).order_by(UrlProcessingResult.created_at.desc()).limit(limit).all()
        return results
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка получения результатов: {e}")
        return []
    finally:
        session.close()


# ============================================
# Функции для получения статистики
# ============================================

def get_user_stats(user_id: int) -> Dict:
    """Получить статистику пользователя"""
    session = get_db_session()
    if not session:
        return {}
    
    try:
        # Количество URL
        url_count = session.query(UserUrl).filter(UserUrl.user_id == user_id).count()
        
        # Количество обработанных URL
        processed_count = session.query(UserUrl).filter(
            UserUrl.user_id == user_id,
            UserUrl.last_processed_at.isnot(None)
        ).count()
        
        # Последний обработанный URL
        last_processed = session.query(UserUrl).filter(
            UserUrl.user_id == user_id,
            UserUrl.last_processed_at.isnot(None)
        ).order_by(UserUrl.last_processed_at.desc()).first()
        
        return {
            'total_urls': url_count,
            'processed_urls': processed_count,
            'last_processed_at': last_processed.last_processed_at.isoformat() if last_processed else None
        }
    except SQLAlchemyError as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        return {}
    finally:
        session.close()

