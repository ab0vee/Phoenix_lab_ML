'use client'

import { useState, useEffect } from 'react'

interface DatabaseMenuProps {
  isDark: boolean
  onClose: () => void
}

interface UserUrl {
  url_id: number
  url: string
  url_title: string | null
  url_created_at: string | null
}

interface DatabaseData {
  success: boolean
  data: Array<{
    user_id: number
    username: string
    user_email: string | null
    url_id: number | null
    url: string | null
    url_title: string | null
    url_created_at: string | null
  }>
  total: number
  users_count: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export default function DatabaseMenu({ isDark, onClose }: DatabaseMenuProps) {
  const [data, setData] = useState<DatabaseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedUsername, setSelectedUsername] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const authToken = localStorage.getItem('auth_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`
        console.log('🔑 Токен авторизации найден:', authToken.substring(0, 10) + '...')
      } else {
        console.warn('⚠️ Токен авторизации не найден в localStorage')
      }

      // Получаем username из localStorage
      const savedUser = localStorage.getItem('telegram_user')
      let username = null
      if (savedUser) {
        try {
          const userData = JSON.parse(savedUser)
          username = userData.username || `telegram_${userData.id}`
          console.log('👤 Загрузка данных для пользователя:', username)
        } catch (e) {
          console.error('Ошибка парсинга данных пользователя:', e)
        }
      } else {
        console.warn('⚠️ Данные пользователя не найдены в localStorage')
      }

      const url = username ? `${API_URL}/api/data?username=${encodeURIComponent(username)}` : `${API_URL}/api/data`
      console.log('📡 Запрос к API:', url)
      const response = await fetch(url, { headers })

      if (!response.ok) {
        throw new Error('Ошибка загрузки данных')
      }

      const result = await response.json()
      console.log('📦 Получены данные из API:', result)
      console.log('📊 Всего записей:', result.total)
      console.log('👥 Пользователей:', result.users_count)
      setData(result)
      if (username) {
        setSelectedUsername(username)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка')
      console.error('Ошибка загрузки данных БД:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUseUrl = (url: string) => {
    // Отправляем событие для вставки URL в поле ввода
    const event = new CustomEvent('insertUrl', { 
      detail: { url },
      bubbles: true,
      cancelable: true
    })
    window.dispatchEvent(event)
    onClose()
  }

  const handleCopyUrl = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url)
      alert('URL скопирован в буфер обмена')
    } catch (err) {
      console.error('Ошибка копирования:', err)
      alert('Не удалось скопировать URL')
    }
  }

  // Получаем username текущего пользователя для фильтрации
  const savedUser = localStorage.getItem('telegram_user')
  let currentUsername: string | null = null
  if (savedUser) {
    try {
      const userData = JSON.parse(savedUser)
      currentUsername = userData.username || `telegram_${userData.id}`
    } catch (e) {
      console.error('Ошибка парсинга данных пользователя:', e)
    }
  }

  // Группируем данные по пользователям и фильтруем только текущего пользователя
  const groupedData = data?.data.reduce((acc, item) => {
    // Показываем только данные текущего пользователя
    if (currentUsername && item.username !== currentUsername) {
      return acc
    }
    
    if (!acc[item.username]) {
      acc[item.username] = {
        user_id: item.user_id,
        username: item.username,
        email: item.user_email,
        urls: [] as UserUrl[]
      }
    }
    if (item.url) {
      acc[item.username].urls.push({
        url_id: item.url_id!,
        url: item.url,
        url_title: item.url_title,
        url_created_at: item.url_created_at
      })
    }
    return acc
  }, {} as Record<string, { user_id: number; username: string; email: string | null; urls: UserUrl[] }>) || {}

  const users = Object.values(groupedData)

  return (
    <div className={`settings-menu-overlay ${isDark ? 'dark-theme' : ''}`} onClick={onClose}>
      <div className="auth-menu settings-menu database-menu" onClick={(e) => e.stopPropagation()}>
        <button className="auth-menu-close" onClick={onClose}>
          ×
        </button>
        <h2 className="auth-menu-title">Журнал</h2>

        {loading && (
          <div className="database-loading">
            <p>Загрузка данных...</p>
          </div>
        )}

        {error && (
          <div className="database-error">
            <p>Ошибка: {error}</p>
            <button onClick={fetchData} className="retry-btn">Повторить</button>
          </div>
        )}

        {!loading && !error && (
          <div className="database-content">
            {users.length === 0 ? (
              <div className="database-empty">
                <p>Нет данных</p>
                <p className="database-empty-hint">Обработайте статью, чтобы данные появились здесь</p>
              </div>
            ) : (
              users.map((user) => (
                <div key={user.user_id} className="database-user-section">
                  <h3 className="database-user-name">{user.username}</h3>
                  {user.email && <p className="database-user-email">{user.email}</p>}
                  
                  {user.urls.length === 0 ? (
                    <p className="database-no-urls">Нет сохраненных URL</p>
                  ) : (
                    <div className="database-urls-list">
                      {user.urls.map((urlItem) => (
                        <div key={urlItem.url_id} className="database-url-item">
                          <div className="database-url-info">
                            <p className="database-url-title">{urlItem.url_title || 'Без названия'}</p>
                            <p className="database-url-link">{urlItem.url}</p>
                            {urlItem.url_created_at && (
                              <p className="database-url-date">
                                {new Date(urlItem.url_created_at).toLocaleString('ru-RU')}
                              </p>
                            )}
                          </div>
                          <div className="database-url-actions">
                            <button
                              className="database-use-btn"
                              onClick={() => handleUseUrl(urlItem.url)}
                              title="Использовать этот URL"
                            >
                              Использовать
                            </button>
                            <button
                              className="database-copy-btn"
                              onClick={() => handleCopyUrl(urlItem.url)}
                              title="Скопировать URL"
                            >
                              Копировать
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

