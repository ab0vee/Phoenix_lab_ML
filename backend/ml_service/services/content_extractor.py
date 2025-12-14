"""Сервис для извлечения контента из URL"""
import trafilatura
import httpx
from typing import Dict, Optional
from langdetect import detect
import logging

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Извлечение контента из веб-страниц"""
    
    async def extract_from_url(self, url: str) -> Dict:
        """
        Извлечение текста из URL
        
        Args:
            url: URL страницы
            
        Returns:
            Dict с текстом, заголовком, языком
        """
        try:
            # Загрузка страницы с увеличенным таймаутом для медленных сайтов
            timeout = httpx.Timeout(60.0, connect=10.0)  # 60 сек на запрос, 10 сек на подключение
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text
            
            # Извлечение текста с помощью trafilatura
            extracted = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=False,
                include_images=False,
                include_links=False
            )
            
            if not extracted:
                # Fallback: попытка через readability
                from readability import Document
                doc = Document(html_content)
                extracted = doc.summary()
                # Удаление HTML тегов
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(extracted, 'html.parser')
                extracted = soup.get_text()
            
            if not extracted:
                raise ValueError("Не удалось извлечь текст из страницы")
            
            # Ограничение размера (защита от очень больших страниц)
            max_length = 50000
            if len(extracted) > max_length:
                extracted = extracted[:max_length] + "..."
            
            # Определение языка
            try:
                language = detect(extracted)
            except:
                language = "ru"  # По умолчанию русский
            
            # Извлечение заголовка
            try:
                metadata = trafilatura.extract_metadata(html_content)
                title = metadata.title if metadata and hasattr(metadata, 'title') else ''
            except Exception as e:
                logger.warning(f"Не удалось извлечь заголовок: {e}")
                title = ''
            
            return {
                "text": extracted.strip(),
                "title": title or '',
                "language": language,
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении контента из {url}: {str(e)}")
            raise ValueError(f"Не удалось извлечь контент: {str(e)}")

