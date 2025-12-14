'use client'

import React, { useState, useEffect, useRef } from 'react'
import Image from 'next/image'
import AuthMenu from './components/AuthMenu'
import SettingsMenu from './components/SettingsMenu'
import MonetizationMenu from './components/MonetizationMenu'
import DatabaseMenu from './components/DatabaseMenu'
import FallingElements from './components/FallingElements'
import IconButton from './components/IconButton'

interface Channel {
  id: string
  name: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'
const ML_SERVICE_URL = process.env.NEXT_PUBLIC_ML_SERVICE_URL || 'http://localhost:8000'

export default function Home() {
  const [isDarkTheme, setIsDarkTheme] = useState(false)
  const [selectedStyle, setSelectedStyle] = useState<string | null>(null)
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultText, setResultText] = useState('')
  const [showResult, setShowResult] = useState(false)
  const [showChannels, setShowChannels] = useState(false)
  const [availableChannels, setAvailableChannels] = useState<Channel[]>([])
  const [selectedChannels, setSelectedChannels] = useState<string[]>([])
  const [currentArticleText, setCurrentArticleText] = useState('')
  const [showAuthMenu, setShowAuthMenu] = useState(false)
  const [showSettingsMenu, setShowSettingsMenu] = useState(false)
  const [showDatabaseMenu, setShowDatabaseMenu] = useState(false)
  const [showMonetizationMenu, setShowMonetizationMenu] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [showGif, setShowGif] = useState(false)
  const [gifKey, setGifKey] = useState(0)
  const [summarizeStatus, setSummarizeStatus] = useState<string>('')
  const saveUrlTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  
  // Состояния для изображений
  const [images, setImages] = useState<{
    original: string | null
    pexels: string | null
    generated: string | null
  } | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  
  // Состояния загрузки для каждого компонента
  const [loadingOriginalImage, setLoadingOriginalImage] = useState(false)
  const [loadingPexelsImage, setLoadingPexelsImage] = useState(false)
  const [loadingGeneratedImage, setLoadingGeneratedImage] = useState(false)
  
  // Состояния готовности компонентов
  const [originalImageReady, setOriginalImageReady] = useState(false)
  const [pexelsImageReady, setPexelsImageReady] = useState(false)
  const [generatedImageReady, setGeneratedImageReady] = useState(false)

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light'
    if (savedTheme === 'dark') {
      setIsDarkTheme(true)
      document.body.classList.add('dark-theme')
    }
    
    // Проверяем сохраненного пользователя
    const savedUser = localStorage.getItem('telegram_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        console.error('Ошибка загрузки данных пользователя:', e)
      }
    }
    
    loadChannels()

    // Обработчик события для вставки URL
    const handleInsertUrl = (event: Event) => {
      const customEvent = event as CustomEvent<{ url: string }>
      if (customEvent.detail && customEvent.detail.url) {
        setUrl(customEvent.detail.url)
        // Фокусируемся на поле ввода после вставки
        const urlInput = document.getElementById('article-url') as HTMLTextAreaElement
        if (urlInput) {
          urlInput.focus()
          // Автоматически изменяем высоту textarea
          urlInput.style.height = 'auto'
          urlInput.style.height = urlInput.scrollHeight + 'px'
          // Прокручиваем к полю ввода, если оно не видно
          urlInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
    }

    window.addEventListener('insertUrl', handleInsertUrl)
    return () => {
      window.removeEventListener('insertUrl', handleInsertUrl)
    }
  }, [])

  const handleLogin = (userData: any) => {
    setUser(userData)
    setShowAuthMenu(false)
  }

  const toggleTheme = () => {
    const newTheme = !isDarkTheme
    setIsDarkTheme(newTheme)
    if (newTheme) {
      document.body.classList.add('dark-theme')
      localStorage.setItem('theme', 'dark')
    } else {
      document.body.classList.remove('dark-theme')
      localStorage.setItem('theme', 'light')
    }
  }

  const loadChannels = async () => {
    try {
      console.log('Загрузка каналов из:', `${API_URL}/api/channels`)
      const response = await fetch(`${API_URL}/api/channels`)
      const data = await response.json()
      console.log('Ответ API:', data)
      if (data.success) {
        setAvailableChannels(data.channels)
        console.log('Загружено каналов:', data.channels.length)
      } else {
        console.error('Ошибка API:', data.error)
      }
    } catch (error) {
      console.error('Ошибка загрузки каналов:', error)
      alert('Ошибка подключения к серверу. Убедитесь, что backend сервер запущен.')
    }
  }

  const handleStyleSelect = (style: string) => {
    setSelectedStyle(style)
  }

  // Функция для автоматического сохранения URL в БД
  const saveUrlToDatabase = async (urlToSave: string) => {
    if (!urlToSave.trim()) {
      return
    }

    // Проверяем, что URL валидный
    try {
      new URL(urlToSave)
    } catch {
      return // Невалидный URL, не сохраняем
    }

    // Получаем токен из localStorage (если есть)
    const savedUser = localStorage.getItem('telegram_user')
    if (!savedUser) {
      return // Пользователь не авторизован, не сохраняем
    }

    try {
      const authToken = localStorage.getItem('auth_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`
      }

      const response = await fetch(`${API_URL}/api/save-url`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ url: urlToSave })
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          console.log('✅ URL автоматически сохранен в БД:', urlToSave)
        }
      }
    } catch (error) {
      console.error('Ошибка автоматического сохранения URL:', error)
      // Не показываем ошибку пользователю, это фоновый процесс
    }
  }

  // Функция для определения, является ли ввод URL или текстом
  const isUrl = (input: string): boolean => {
    const trimmed = input.trim()
    // Проверяем, начинается ли строка с http:// или https://
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
      try {
        // Дополнительная проверка через URL конструктор
        new URL(trimmed)
        return true
      } catch {
        return false
      }
    }
    return false
  }

  const handleSubmit = async () => {
    if (!url.trim()) {
      alert('Пожалуйста, введите URL статьи или текст')
      return
    }

    if (!selectedStyle) {
      alert('Пожалуйста, выберите стиль рерайта')
      return
    }

    // Получаем выбранную модель из настроек
    const rewriteModel = localStorage.getItem('rewrite_model') || 'rut5'
    
    // Проверяем, является ли ввод URL или текстом
    const inputIsUrl = isUrl(url)
    
    // Проверка для NLP моделей: они не могут работать с URL, только с текстом
    if (inputIsUrl && (rewriteModel === 'rut5' || rewriteModel === 'flant5')) {
      alert('Модель ' + (rewriteModel === 'rut5' ? 'RUT5' : 'FLAN-T5') + ' предназначена ТОЛЬКО для рерайта готового текста. Введите текст напрямую в поле ввода, а не URL.')
      return
    }

    // Сброс всех состояний
    setLoading(true)
    setShowResult(true) // Показываем секцию результатов сразу
    setShowChannels(false)
    setResultText('')
    setImages(null)
    setSelectedImage(null)
    setOriginalImageReady(false)
    setPexelsImageReady(false)
    setGeneratedImageReady(false)
    
    // Запускаем загрузку для всех компонентов
    setLoadingOriginalImage(true)
    setLoadingPexelsImage(true)
    setLoadingGeneratedImage(true)
    
    // Проверяем доступность модели
    const userTariff = localStorage.getItem('user_tariff')
    const customFeatures = localStorage.getItem('custom_features')
    
    const checkModelAccess = (model: string, type: 'rewrite' | 'summary'): boolean => {
      // NLP модели всегда доступны
      if (model === 'rut5' || model === 'flant5' || model === 'gazeta') {
        return true
      }
      
      // LLM модели требуют подписки
      if (userTariff === 'business') {
        return true // Полный доступ
      }
      
      if (userTariff === 'custom' && customFeatures) {
        try {
          const features = JSON.parse(customFeatures)
          if (type === 'rewrite') {
            return model === 'qwen' ? features.rewrite_qwen : features.rewrite_yandex
          } else {
            return model === 'qwen' ? features.summary_qwen : features.summary_yandex
          }
        } catch (e) {
          return false
        }
      }
      
      return false // Нет доступа
    }
    
    if (!checkModelAccess(rewriteModel, 'rewrite')) {
      alert('Выбранная модель недоступна в вашем тарифе. Перейдите в раздел "Монетизация" для подписки.')
      setLoading(false)
      return
    }
    
    // Маппинг моделей: qwen/yandex -> qwen/yandex, rut5/flant5 -> rut5/flant5
    const provider = rewriteModel
    
    try {
      // Получаем токен из localStorage (если есть)
      const savedUser = localStorage.getItem('telegram_user')
      let authToken = null
      if (savedUser) {
        try {
          const userData = JSON.parse(savedUser)
          // Пытаемся найти токен в localStorage (если сохраняли)
          authToken = localStorage.getItem('auth_token')
        } catch (e) {
          console.error('Ошибка парсинга данных пользователя:', e)
        }
      }
      
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      
      // Добавляем токен в заголовок, если есть
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`
      }
      
      // Формируем тело запроса в зависимости от того, URL это или текст
      const requestBody: any = {
        style: selectedStyle,
        provider: provider,
        username: user?.username || null  // Передаем username, если пользователь авторизован
      }
      
      if (inputIsUrl) {
        // Если это URL, отправляем как обычно
        requestBody.url = url.trim()
      } else {
        // Если это текст, отправляем напрямую
        requestBody.text = url.trim()
      }
      
      const response = await fetch(`${API_URL}/api/rewrite-article`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()

      if (data.success) {
        // Получаем текст и добавляем источник, если был передан URL
        let resultText = data.text || data.rewritten_text || ''
        if (data.url && data.url.trim()) {
          resultText = resultText.trim() + `\n\nИсточник: ${data.url}`
        }
        
        // Показываем текст сразу с анимацией
        setTimeout(() => {
          setCurrentArticleText(resultText)
          setResultText(resultText)
        }, 300)
        
        // Показываем изображения по мере готовности с задержками
        const imagesData = data.images || {}
        let currentImages: { original: string | null, pexels: string | null, generated: string | null } = {
          original: null,
          pexels: null,
          generated: null
        }
        
        // Оригинальное изображение
        if (imagesData.original) {
          setTimeout(() => {
            currentImages.original = imagesData.original
            setImages({ ...currentImages })
            setLoadingOriginalImage(false)
            setOriginalImageReady(true)
            if (!selectedImage) {
              setSelectedImage('original')
            }
          }, 600)
        } else {
          setTimeout(() => {
            setLoadingOriginalImage(false)
          }, 600)
        }
        
        // Pexels изображение
        if (imagesData.pexels) {
          setTimeout(() => {
            currentImages.pexels = imagesData.pexels
            setImages(prev => prev ? { ...prev, pexels: imagesData.pexels } : { ...currentImages, pexels: imagesData.pexels })
            setLoadingPexelsImage(false)
            setPexelsImageReady(true)
            if (!selectedImage && !imagesData.original) {
              setSelectedImage('pexels')
            }
          }, 900)
        } else {
          setTimeout(() => {
            setLoadingPexelsImage(false)
          }, 900)
        }
        
        // Сгенерированное изображение
        if (imagesData.generated) {
          setTimeout(() => {
            currentImages.generated = imagesData.generated
            setImages(prev => prev ? { ...prev, generated: imagesData.generated } : { ...currentImages, generated: imagesData.generated })
            setLoadingGeneratedImage(false)
            setGeneratedImageReady(true)
            if (!selectedImage && !imagesData.original && !imagesData.pexels) {
              setSelectedImage('generated')
            }
          }, 1200)
        } else {
          setTimeout(() => {
            setLoadingGeneratedImage(false)
          }, 1200)
        }
        
        setLoading(false)
      } else {
        alert(`Ошибка: ${data.error}`)
        setLoading(false)
        setLoadingOriginalImage(false)
        setLoadingPexelsImage(false)
        setLoadingGeneratedImage(false)
      }
    } catch (error) {
      console.error('Ошибка рерайта статьи:', error)
      alert('Ошибка подключения к серверу. Убедитесь, что backend сервер запущен.')
      setLoading(false)
      setLoadingOriginalImage(false)
      setLoadingPexelsImage(false)
      setLoadingGeneratedImage(false)
    }
  }

  const handleSocialClick = async (social: string) => {
    console.log('Клик по кнопке:', social)
    if (social === 'telegram') {
      if (!currentArticleText) {
        alert('Сначала обработайте статью')
        return
      }
      
      console.log('Перезагрузка каналов...')
      // Перезагружаем каналы перед показом
      try {
        const response = await fetch(`${API_URL}/api/channels`)
        const data = await response.json()
        console.log('Ответ API:', data)
        
        if (data.success && data.channels && data.channels.length > 0) {
          setAvailableChannels(data.channels)
          console.log('Загружено каналов:', data.channels.length)
          // Убеждаемся, что результат показан
          if (!showResult) {
            console.log('Показываем результат')
            setShowResult(true)
          }
          console.log('Показываем выбор каналов')
          setShowChannels(true)
          setSelectedChannels([]) // Сбрасываем выбор
          console.log('Состояние обновлено: showChannels = true, showResult =', showResult)
        } else {
          alert('Каналы не настроены. Используйте бота для добавления каналов.')
        }
      } catch (error) {
        console.error('Ошибка загрузки каналов:', error)
        alert('Ошибка подключения к серверу. Убедитесь, что backend сервер запущен на порту 5000.')
      }
    } else {
      alert(`Публикация в ${social === 'vk' ? 'Вконтакте' : 'Instagram'}`)
    }
  }

  const handleChannelToggle = (channelId: string) => {
    setSelectedChannels(prev =>
      prev.includes(channelId)
        ? prev.filter(id => id !== channelId)
        : [...prev, channelId]
    )
  }

  const handleSendTelegram = async () => {
    if (selectedChannels.length === 0) {
      alert('Выберите хотя бы один канал')
      return
    }

    try {
      const imageUrlToSend = selectedImage && images && images[selectedImage as keyof typeof images] 
        ? images[selectedImage as keyof typeof images] 
        : null
      
      console.log('Отправка статьи в Telegram:')
      console.log('- Выбранное изображение:', selectedImage)
      console.log('- URL изображения:', imageUrlToSend)
      console.log('- Длина текста:', currentArticleText.length)

      const response = await fetch(`${API_URL}/api/send-article`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          article_text: currentArticleText,
          image_url: imageUrlToSend,
          channels: selectedChannels
        })
      })

      const data = await response.json()

      if (data.success) {
        alert(`Статья отправлена в ${data.sent} из ${data.total} каналов`)
        setShowChannels(false)
        setSelectedChannels([])
      } else {
        alert(`Ошибка: ${data.error}`)
      }
    } catch (error) {
      console.error('Ошибка отправки:', error)
      alert('Ошибка отправки статьи')
    }
  }

  const getStyleName = (style: string) => {
    const styles: Record<string, string> = {
      'scientific': 'Научно-деловой стиль',
      'meme': 'Мемный стиль',
      'casual': 'Повседневный стиль'
    }
    return styles[style] || style
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter') {
      handleSubmit()
    }
  }

  const handleLogoClick = () => {
    // Предотвращаем повторный клик во время проигрывания гифки
    if (showGif) {
      console.log('Гифка уже воспроизводится, игнорируем клик')
      return
    }
    
    console.log('Клик по логотипу, запускаем гифку')
    
    // Сначала скрываем, чтобы сбросить состояние
    setShowGif(false)
    setGifKey(prev => prev + 1)
    
    // Затем показываем гифку через небольшую задержку для правильной перезагрузки
    setTimeout(() => {
      setShowGif(true)
      console.log('Показываем гифку')
    }, 50)
    
    // Возвращаем логотип через 11.24 секунды (полная длительность гифки)
    setTimeout(() => {
      setShowGif(false)
      console.log('Гифка завершена, возвращаем логотип')
    }, 11290) // 11240 + 50 (задержка показа)
  }

  const handleGifLoad = () => {
    console.log('Гифка успешно загружена')
  }

  const handleGifError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('Ошибка загрузки гифки')
    const target = e.target as HTMLImageElement
    // Пробуем загрузить без query параметра
    target.src = '/assets/горение.gif'
  }

  return (
    <>
      <FallingElements />
      <div className="container">
      <div className="header">
        <div className="piar-logo">
          <img src="/piar.png" alt="PIAR" className="piar-image" />
        </div>
        <div className="header-controls">
          <IconButton
            icon={
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M20.59 22C20.59 18.13 16.74 15 12 15C7.26 15 3.41 18.13 3.41 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            }
            label={user ? user.first_name || user.username || 'Профиль' : 'Войти'}
            onClick={() => setShowAuthMenu(true)}
            className="profile-btn"
          />
          <IconButton
            icon={
              isDarkTheme ? (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 1V3M12 21V23M4.22 4.22L5.64 5.64M18.36 18.36L19.78 19.78M1 12H3M21 12H23M4.22 19.78L5.64 18.36M18.36 5.64L19.78 4.22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              ) : (
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              )
            }
            label={isDarkTheme ? 'Светлая тема' : 'Тёмная тема'}
            onClick={toggleTheme}
            className="theme-btn"
          />
          <IconButton
            icon={
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5843 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6643 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.258 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6643 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.01131 9.77251C4.28062 9.5799 4.48571 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29577 4.55324 9.54802 4.34276 9.72569 4.07447C9.90337 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29577 19.6572 9.54802 19.9255 9.72569C20.1938 9.90337 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15V15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            }
            label="Настройки"
            onClick={() => setShowSettingsMenu(true)}
            className="settings-btn"
          />
          <IconButton
            icon={
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 7C4 6.46957 4.21071 5.96086 4.58579 5.58579C4.96086 5.21071 5.46957 5 6 5H18C18.5304 5 19.0391 5.21071 19.4142 5.58579C19.7893 5.96086 20 6.46957 20 7V19C20 19.5304 19.7893 20.0391 19.4142 20.4142C19.0391 20.7893 18.5304 21 18 21H6C5.46957 21 4.96086 20.7893 4.58579 20.4142C4.21071 20.0391 4 19.5304 4 19V7Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M4 7H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M10 11H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M10 15H14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M7 3V7M17 3V7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            }
            label="Журнал"
            onClick={() => setShowDatabaseMenu(true)}
            className="database-btn"
          />
          <IconButton
            icon={
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            }
            label="Монетизация"
            onClick={() => setShowMonetizationMenu(true)}
            className="monetization-btn"
          />
        </div>
        <div 
          className="logo-container"
          onClick={handleLogoClick}
          style={{ 
            cursor: showGif ? 'default' : 'pointer'
          }}
        >
          {showGif ? (
            <img 
              key={gifKey}
              src="/assets/горение.gif"
              alt="Phoenix Burning Animation" 
              className="logo"
              width={120}
              height={120}
              onLoad={handleGifLoad}
              onError={handleGifError}
              style={{ 
                width: '120px', 
                height: '120px', 
                objectFit: 'contain', 
                pointerEvents: 'none',
                display: 'block'
              }}
            />
          ) : (
            <Image 
              src="/logo.png"
              alt="Phoenix Lab Logo" 
              className="logo"
              width={120}
              height={120}
              priority
            />
          )}
        </div>
        <h1>Phoenix Lab</h1>
        <p className="subtitle">AI Рерайт Статей</p>
      </div>

      <div className="main-content">
        <div className="input-section">
          <label htmlFor="article-url">URL статьи или текст</label>
          <textarea
            id="article-url"
            className="url-input"
            placeholder="Введите url или текст"
            value={url}
            onChange={(e) => {
              setUrl(e.target.value)
              // Автоматически изменяем высоту textarea
              e.target.style.height = 'auto'
              e.target.style.height = e.target.scrollHeight + 'px'
              
              // Автоматически сохраняем URL в БД с задержкой (debounce), только если это URL
              const inputValue = e.target.value.trim()
              if (inputValue && (inputValue.startsWith('http://') || inputValue.startsWith('https://'))) {
                if (saveUrlTimeoutRef.current) {
                  clearTimeout(saveUrlTimeoutRef.current)
                }
                saveUrlTimeoutRef.current = setTimeout(() => {
                  saveUrlToDatabase(inputValue)
                }, 2000) // Сохраняем через 2 секунды после окончания ввода
              }
            }}
            onBlur={(e) => {
              // Сохраняем URL при потере фокуса, только если это URL
              const inputValue = e.target.value.trim()
              if (inputValue && (inputValue.startsWith('http://') || inputValue.startsWith('https://'))) {
                saveUrlToDatabase(inputValue)
              }
            }}
            onKeyPress={(e) => {
              // Если нажат Enter без Shift, отправляем форму
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleKeyPress(e)
              }
            }}
            rows={1}
            style={{ 
              resize: 'vertical',
              minHeight: '48px',
              overflow: 'hidden'
            }}
          />
        </div>

        <div className="style-section">
          <label>Стиль рерайта</label>
          <div className="style-buttons">
            <button
              className={`style-btn ${selectedStyle === 'scientific' ? 'active' : ''}`}
              onClick={() => handleStyleSelect('scientific')}
            >
              Научно-деловой стиль
            </button>
            <button
              className={`style-btn ${selectedStyle === 'meme' ? 'active' : ''}`}
              onClick={() => handleStyleSelect('meme')}
            >
              Мемный стиль
            </button>
            <button
              className={`style-btn ${selectedStyle === 'casual' ? 'active' : ''}`}
              onClick={() => handleStyleSelect('casual')}
            >
              Повседневный стиль
            </button>
          </div>
        </div>

        <div className="social-section">
          <label>Публикация в соцсетях</label>
          <div className="social-buttons">
            <button className="social-btn" onClick={() => handleSocialClick('vk')}>
              Вконтакте (В разработке)
            </button>
            <button className="social-btn" onClick={() => handleSocialClick('telegram')}>
              Telegram
            </button>
            <button className="social-btn" onClick={() => handleSocialClick('instagram')}>
              Instagram (В разработке)
            </button>
          </div>
        </div>

        <button className="submit-btn" onClick={handleSubmit} disabled={loading}>
          Рерайт статьи
        </button>

        {loading && (
          <div className="loading show">
            <div className="spinner"></div>
            <p>{summarizeStatus || 'Обработка статьи...'}</p>
          </div>
        )}

        <div className={`result-section ${showResult ? 'show' : ''}`}>
          <div className="result-box">
            <div className="result-title">Результат рерайта:</div>
            
            {/* Текст статьи */}
            {resultText && (
              <div className="result-text fade-in">{resultText}</div>
            )}
            
            {/* Выбор изображения с анимациями загрузки */}
            <div className="image-selection">
              <h3 className="image-selection-title">Выберите изображение для статьи:</h3>
              <div className="image-options">
                {/* Оригинальное изображение */}
                {loadingOriginalImage ? (
                  <div className="image-option skeleton-image">
                    <div className="skeleton-image-placeholder">
                      <div className="spinner"></div>
                    </div>
                    <div className="image-label skeleton-label">Загрузка...</div>
                  </div>
                ) : originalImageReady && images?.original ? (
                  <div 
                    className={`image-option fade-in ${selectedImage === 'original' ? 'selected' : ''}`}
                    onClick={() => setSelectedImage('original')}
                  >
                    <img src={images.original} alt="Оригинальное изображение" />
                    <div className="image-label">Оригинальное</div>
                  </div>
                ) : null}
                
                {/* Pexels изображение */}
                {loadingPexelsImage ? (
                  <div className="image-option skeleton-image">
                    <div className="skeleton-image-placeholder">
                      <div className="spinner"></div>
                    </div>
                    <div className="image-label skeleton-label">Загрузка...</div>
                  </div>
                ) : pexelsImageReady && images?.pexels ? (
                  <div 
                    className={`image-option fade-in ${selectedImage === 'pexels' ? 'selected' : ''}`}
                    onClick={() => setSelectedImage('pexels')}
                  >
                    <img src={images.pexels} alt="Изображение из API" />
                    <div className="image-label">Из API</div>
                  </div>
                ) : null}
                
                {/* Сгенерированное изображение */}
                {loadingGeneratedImage ? (
                  <div className="image-option skeleton-image">
                    <div className="skeleton-image-placeholder">
                      <div className="spinner"></div>
                    </div>
                    <div className="image-label skeleton-label">Генерация...</div>
                  </div>
                ) : generatedImageReady && images?.generated ? (
                  <div 
                    className={`image-option fade-in ${selectedImage === 'generated' ? 'selected' : ''}`}
                    onClick={() => setSelectedImage('generated')}
                  >
                    <img src={images.generated} alt="Сгенерированное изображение" />
                    <div className="image-label">Сгенерированное</div>
                  </div>
                ) : null}
                
                {/* Сообщение, если все изображения загружены, но ничего не найдено */}
                {!loadingOriginalImage && !loadingPexelsImage && !loadingGeneratedImage && 
                 !images?.original && !images?.pexels && !images?.generated && (
                  <div className="no-images-message fade-in">
                    <p>⚠️ Изображения не найдены. Статья будет отправлена без изображения.</p>
                  </div>
                )}
              </div>
              
              {/* Превью выбранного изображения */}
              {selectedImage && images && images[selectedImage as keyof typeof images] && (
                <div className="selected-image-preview fade-in">
                  <p>Выбрано: <strong>{selectedImage === 'original' ? 'Оригинальное' : selectedImage === 'pexels' ? 'Из Pexels' : 'Сгенерированное'}</strong></p>
                  <img 
                    src={images[selectedImage as keyof typeof images]!} 
                    alt="Выбранное изображение" 
                    className="preview-image"
                  />
                </div>
              )}
            </div>
            
            {/* Кнопки действий с результатом */}
            {resultText && (
              <div style={{ marginTop: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button 
                  className="submit-btn fade-in" 
                  onClick={async () => {
                    // Сокращение текста
                    setLoading(true)
                    
                    // Получаем выбранную модель сокращения
                    const summaryModel = localStorage.getItem('summary_model') || 'gazeta'
                    const isNLPModel = summaryModel === 'gazeta'
                    
                    // Проверяем доступность модели
                    const userTariff = localStorage.getItem('user_tariff')
                    const customFeatures = localStorage.getItem('custom_features')
                    
                    const checkSummaryModelAccess = (model: string): boolean => {
                      // NLP модели всегда доступны
                      if (model === 'gazeta') {
                        return true
                      }
                      
                      // LLM модели требуют подписки
                      if (userTariff === 'business') {
                        return true // Полный доступ
                      }
                      
                      if (userTariff === 'custom' && customFeatures) {
                        try {
                          const features = JSON.parse(customFeatures)
                          return model === 'qwen' ? features.summary_qwen : features.summary_yandex
                        } catch (e) {
                          return false
                        }
                      }
                      
                      return false // Нет доступа
                    }
                    
                    if (!checkSummaryModelAccess(summaryModel)) {
                      alert('Выбранная модель недоступна в вашем тарифе. Перейдите в раздел "Монетизация" для подписки.')
                      setLoading(false)
                      return
                    }
                    
                    setSummarizeStatus('Подготовка к сокращению...')
                    
                    try {
                      setSummarizeStatus('Подключение к серверу обработки...')
                      
                      // Проверяем доступность ML Service
                      try {
                        const healthCheck = await fetch(`${ML_SERVICE_URL}/health`, { 
                          method: 'GET',
                          signal: AbortSignal.timeout(5000)
                        })
                        if (!healthCheck.ok) {
                          throw new Error('ML Service недоступен')
                        }
                      } catch (healthError) {
                        setSummarizeStatus('')
                        alert(`ML Service недоступен на ${ML_SERVICE_URL}. Проверьте, что сервис запущен: docker-compose up -d ml_service`)
                        return
                      }
                      
                      // Для NLP моделей показываем сообщение о загрузке модели
                      // Для LLM (Qwen, Yandex) это не нужно - они работают через промпты
                      if (isNLPModel) {
                        setSummarizeStatus('Загрузка модели (первый раз может занять 20-30 секунд)...')
                      } else {
                        setSummarizeStatus('Обработка текста...')
                      }
                      
                      const response = await fetch(`${ML_SERVICE_URL}/api/v1/summarize`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                          text: resultText,
                          target_length: Math.floor(resultText.length * 0.6), // Сокращаем до 60%
                          language: 'ru'
                        }),
                        signal: AbortSignal.timeout(120000) // Таймаут 2 минуты
                      })
                      
                      if (response.ok) {
                        // Для NLP моделей показываем сообщение о времени обработки
                        // Для LLM просто "Обработка..."
                        if (isNLPModel) {
                          setSummarizeStatus('Обработка текста моделью (это может занять 10-30 секунд)...')
                        } else {
                          setSummarizeStatus('Обработка текста...')
                        }
                        const data = await response.json()
                        setSummarizeStatus('Форматирование результата...')
                        
                        // Добавляем источник в конце текста (если был URL)
                        let summaryText = data.summary || data.text || ''
                        if (url && url.trim() && url.startsWith('http')) {
                          summaryText = summaryText.trim() + `\n\nИсточник: ${url}`
                        }
                        
                        setResultText(summaryText)
                        setCurrentArticleText(summaryText)
                        setSummarizeStatus('')
                        // Уведомление убрано по запросу пользователя
                      } else {
                        const errorData = await response.json().catch(() => ({ detail: 'Ошибка сокращения' }))
                        setSummarizeStatus('')
                        alert(`Ошибка сокращения: ${errorData.detail || errorData.error || 'Неизвестная ошибка'}`)
                      }
                    } catch (error: any) {
                      console.error('Ошибка сокращения:', error)
                      setSummarizeStatus('')
                      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
                        alert('Превышено время ожидания. Модель обрабатывает текст, попробуйте еще раз через минуту.')
                      } else {
                        alert(`Ошибка подключения: ${error.message || 'Неизвестная ошибка'}. Проверьте, что ML Service запущен на ${ML_SERVICE_URL}`)
                      }
                    } finally {
                      setLoading(false)
                      setSummarizeStatus('')
                    }
                  }}
                  disabled={loading}
                >
                  {loading ? (summarizeStatus || 'Сокращение...') : 'Сократить'}
                </button>
                {!showChannels ? (
                  <button 
                    className="submit-btn fade-in" 
                    onClick={async () => {
                      if (!currentArticleText) {
                        alert('Сначала обработайте статью')
                        return
                      }
                      
                      // Перезагружаем каналы перед показом
                      try {
                        const response = await fetch(`${API_URL}/api/channels`)
                        const data = await response.json()
                        
                        if (data.success && data.channels && data.channels.length > 0) {
                          setAvailableChannels(data.channels)
                          setShowChannels(true)
                          setSelectedChannels([])
                        } else {
                          alert('Каналы не настроены. Используйте бота для добавления каналов.')
                        }
                      } catch (error) {
                        console.error('Ошибка загрузки каналов:', error)
                        alert('Ошибка подключения к серверу. Убедитесь, что backend сервер запущен.')
                      }
                    }}
                  >
                    Опубликовать в Telegram каналы
                  </button>
                ) : (
                  <div className="channels-selection">
                    <label style={{ display: 'block', marginBottom: '10px', color: '#ffffff' }}>
                      Выберите каналы для отправки:
                    </label>
                    <div className="channels-list">
                      {availableChannels.map((channel) => (
                        <label key={channel.id}>
                          <input
                            type="checkbox"
                            checked={selectedChannels.includes(channel.id)}
                            onChange={() => handleChannelToggle(channel.id)}
                          />
                          {channel.name || channel.id}
                        </label>
                      ))}
                    </div>
                    <button className="submit-btn" onClick={handleSendTelegram} style={{ marginTop: '10px' }}>
                      Отправить в Telegram
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Меню авторизации */}
      {showAuthMenu && (
        <AuthMenu 
          isDark={isDarkTheme} 
          onClose={() => setShowAuthMenu(false)}
          onLogin={handleLogin}
        />
      )}

      {/* Меню настроек */}
      {showSettingsMenu && (
        <SettingsMenu 
          isDark={isDarkTheme} 
          onClose={() => setShowSettingsMenu(false)}
        />
      )}
      {showDatabaseMenu && (
        <DatabaseMenu 
          isDark={isDarkTheme} 
          onClose={() => setShowDatabaseMenu(false)}
        />
      )}
      {showMonetizationMenu && (
        <MonetizationMenu 
          isDark={isDarkTheme} 
          onClose={() => setShowMonetizationMenu(false)}
        />
      )}
      </div>
    </>
  )
}

