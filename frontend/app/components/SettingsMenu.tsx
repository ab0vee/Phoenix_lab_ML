'use client'

import { useState, useEffect } from 'react'

interface SettingsMenuProps {
  isDark: boolean
  onClose: () => void
}

type RewriteModel = 'qwen' | 'yandex' | 'rut5' | 'flant5'
type SummaryModel = 'qwen' | 'yandex' | 'gazeta'

export default function SettingsMenu({ isDark, onClose }: SettingsMenuProps) {
  const [rewriteModel, setRewriteModel] = useState<RewriteModel>('qwen')
  const [summaryModel, setSummaryModel] = useState<SummaryModel>('gazeta')

  useEffect(() => {
    // Загружаем сохраненные настройки из localStorage
    const savedRewriteModel = localStorage.getItem('rewrite_model') as RewriteModel
    const savedSummaryModel = localStorage.getItem('summary_model') as SummaryModel
    
    if (savedRewriteModel) {
      // Проверяем доступность модели
      if (checkModelAccess(savedRewriteModel, 'rewrite')) {
        setRewriteModel(savedRewriteModel)
      } else {
        // Если модель недоступна, сбрасываем на доступную (NLP)
        setRewriteModel('rut5')
        localStorage.setItem('rewrite_model', 'rut5')
      }
    }
    if (savedSummaryModel) {
      // Проверяем доступность модели
      if (checkModelAccess(savedSummaryModel, 'summary')) {
        setSummaryModel(savedSummaryModel)
      } else {
        // Если модель недоступна, сбрасываем на доступную (NLP)
        setSummaryModel('gazeta')
        localStorage.setItem('summary_model', 'gazeta')
      }
    }
  }, [])

  const checkModelAccess = (model: RewriteModel | SummaryModel, type: 'rewrite' | 'summary'): boolean => {
    const userTariff = localStorage.getItem('user_tariff')
    const customFeatures = localStorage.getItem('custom_features')
    
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

  const handleRewriteModelChange = (model: RewriteModel) => {
    if (!checkModelAccess(model, 'rewrite')) {
      alert('Эта модель недоступна в вашем тарифе. Перейдите в раздел "Монетизация" для подписки.')
      return
    }
    setRewriteModel(model)
    localStorage.setItem('rewrite_model', model)
  }

  const handleSummaryModelChange = (model: SummaryModel) => {
    if (!checkModelAccess(model, 'summary')) {
      alert('Эта модель недоступна в вашем тарифе. Перейдите в раздел "Монетизация" для подписки.')
      return
    }
    setSummaryModel(model)
    localStorage.setItem('summary_model', model)
  }

  return (
    <div className={`settings-menu-overlay ${isDark ? 'dark-theme' : ''}`} onClick={onClose}>
      <div className="auth-menu settings-menu" onClick={(e) => e.stopPropagation()}>
        <button className="auth-menu-close" onClick={onClose}>
          ×
        </button>
        <h2 className="auth-menu-title">Настройки моделей</h2>
        
        <div className="settings-content">
          {/* Настройки рерайта */}
          <div className="settings-section">
            <h3 className="settings-section-title">РЕРАЙТ</h3>
            <p className="settings-section-description">
              Выберите модель для рерайта статей
            </p>
            <div className="settings-options">
              <button
                className={`settings-option ${rewriteModel === 'qwen' ? 'active' : ''}`}
                onClick={() => handleRewriteModelChange('qwen')}
                title="Высокое качество рерайта, понимание контекста, поддержка разных стилей"
              >
                <span className="option-name">Qwen</span>
                <span className="option-badge">LLM</span>
              </button>
              <button
                className={`settings-option ${rewriteModel === 'yandex' ? 'active' : ''}`}
                onClick={() => handleRewriteModelChange('yandex')}
                title="Русскоязычная модель, отличное понимание контекста, быстрая обработка"
              >
                <span className="option-name">Yandex Алиса</span>
                <span className="option-badge">LLM</span>
              </button>
              <button
                className={`settings-option ${rewriteModel === 'rut5' ? 'active' : ''}`}
                onClick={() => handleRewriteModelChange('rut5')}
                title="Быстрая обработка, работает офлайн, оптимизирована для русского языка"
              >
                <span className="option-name">RUT5</span>
                <span className="option-badge nlp">RU NLP</span>
              </button>
              <button
                className={`settings-option ${rewriteModel === 'flant5' ? 'active' : ''}`}
                onClick={() => handleRewriteModelChange('flant5')}
                title="Быстрая обработка, работает офлайн, оптимизирована для английского языка"
              >
                <span className="option-name">FLAN-T5</span>
                <span className="option-badge nlp">EN NLP</span>
              </button>
            </div>
          </div>

          {/* Настройки сокращения */}
          <div className="settings-section">
            <h3 className="settings-section-title">СОКРАЩЕНИЕ</h3>
            <p className="settings-section-description">
              Выберите модель для сокращения текстов
            </p>
            <div className="settings-options">
              <button
                className={`settings-option ${summaryModel === 'qwen' ? 'active' : ''} ${!checkModelAccess('qwen', 'summary') ? 'disabled' : ''}`}
                onClick={() => handleSummaryModelChange('qwen')}
                title={checkModelAccess('qwen', 'summary') ? "Высокое качество сокращения, сохранение ключевых моментов, понимание контекста" : "Требуется подписка"}
                disabled={!checkModelAccess('qwen', 'summary')}
              >
                <span className="option-name">Qwen</span>
                <span className="option-badge">LLM</span>
                {!checkModelAccess('qwen', 'summary') && <span className="option-lock">🔒</span>}
              </button>
              <button
                className={`settings-option ${summaryModel === 'yandex' ? 'active' : ''} ${!checkModelAccess('yandex', 'summary') ? 'disabled' : ''}`}
                onClick={() => handleSummaryModelChange('yandex')}
                title={checkModelAccess('yandex', 'summary') ? "Русскоязычная модель, отличное понимание контекста, сохранение смысла" : "Требуется подписка"}
                disabled={!checkModelAccess('yandex', 'summary')}
              >
                <span className="option-name">Yandex Алиса</span>
                <span className="option-badge">LLM</span>
                {!checkModelAccess('yandex', 'summary') && <span className="option-lock">🔒</span>}
              </button>
              <button
                className={`settings-option ${summaryModel === 'gazeta' ? 'active' : ''}`}
                onClick={() => handleSummaryModelChange('gazeta')}
                title="Быстрое сокращение, работает офлайн, оптимизирована для новостных текстов"
              >
                <span className="option-name">Gazeta</span>
                <span className="option-badge nlp">NLP</span>
              </button>
            </div>
          </div>

          {/* Информация о выбранных моделях */}
          <div className="settings-info">
            <p className="settings-info-text">
              <strong>Текущие настройки:</strong>
            </p>
            <p className="settings-info-text">
              Рерайт: <strong>{rewriteModel === 'qwen' ? 'Qwen' : rewriteModel === 'yandex' ? 'Yandex Алиса' : rewriteModel === 'rut5' ? 'RUT5 (RU NLP)' : 'FLAN-T5 (EN NLP)'}</strong>
            </p>
            <p className="settings-info-text">
              Сокращение: <strong>{summaryModel === 'qwen' ? 'Qwen' : summaryModel === 'yandex' ? 'Yandex Алиса' : 'Gazeta (NLP)'}</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

