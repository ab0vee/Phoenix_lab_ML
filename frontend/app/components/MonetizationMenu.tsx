'use client'

import { useState, useEffect } from 'react'

interface MonetizationMenuProps {
  isDark: boolean
  onClose: () => void
}

type TariffType = 'user' | 'business' | 'custom' | null
type FeatureType = 'rewrite_qwen' | 'rewrite_yandex' | 'summary_qwen' | 'summary_yandex'

interface TariffFeatures {
  rewrite_qwen: boolean
  rewrite_yandex: boolean
  summary_qwen: boolean
  summary_yandex: boolean
}

export default function MonetizationMenu({ isDark, onClose }: MonetizationMenuProps) {
  const [selectedTariff, setSelectedTariff] = useState<TariffType>(null)
  const [customFeatures, setCustomFeatures] = useState<TariffFeatures>({
    rewrite_qwen: false,
    rewrite_yandex: false,
    summary_qwen: false,
    summary_yandex: false
  })

  useEffect(() => {
    // Загружаем текущий тариф из localStorage
    const savedTariff = localStorage.getItem('user_tariff') as TariffType
    const savedCustomFeatures = localStorage.getItem('custom_features')
    
    if (savedTariff) {
      setSelectedTariff(savedTariff)
    }
    
    if (savedCustomFeatures && savedTariff === 'custom') {
      try {
        setCustomFeatures(JSON.parse(savedCustomFeatures))
      } catch (e) {
        console.error('Ошибка загрузки пользовательских функций:', e)
      }
    }
  }, [])

  const handleTariffSelect = (tariff: TariffType) => {
    setSelectedTariff(tariff)
    localStorage.setItem('user_tariff', tariff || '')
    
    if (tariff === 'custom') {
      // Сохраняем пользовательские функции
      localStorage.setItem('custom_features', JSON.stringify(customFeatures))
    } else {
      // Очищаем пользовательские функции для других тарифов
      localStorage.removeItem('custom_features')
    }
  }

  const handleCustomFeatureToggle = (feature: FeatureType) => {
    setCustomFeatures(prev => {
      const updated = { ...prev, [feature]: !prev[feature] }
      localStorage.setItem('custom_features', JSON.stringify(updated))
      return updated
    })
  }

  const handleSubscribe = (tariff: TariffType) => {
    // Здесь будет логика подписки (интеграция с платежной системой)
    alert(`Подписка на тариф "${tariff === 'user' ? 'Пользовательский' : tariff === 'business' ? 'Для бизнеса' : 'Настраиваемый'}" активирована!`)
    handleTariffSelect(tariff)
    onClose()
  }

  return (
    <div className={`settings-menu-overlay ${isDark ? 'dark-theme' : ''}`} onClick={onClose}>
      <div className="auth-menu settings-menu monetization-menu" onClick={(e) => e.stopPropagation()}>
        <button className="auth-menu-close" onClick={onClose}>
          ×
        </button>
        <h2 className="auth-menu-title">Монетизация</h2>
        
        <div className="monetization-content">
          {/* Тариф: Пользовательский */}
          <div className={`tariff-card ${selectedTariff === 'user' ? 'selected' : ''}`}>
            <div className="tariff-header">
              <h3 className="tariff-title">Пользовательский</h3>
              <div className="tariff-price">₽299/мес</div>
            </div>
            <div className="tariff-description">
              Доступ к NLP моделям (бесплатно)
            </div>
            <ul className="tariff-features">
              <li>✓ RUT5 для рерайта</li>
              <li>✓ FLAN-T5 для рерайта</li>
              <li>✓ Gazeta для сокращения</li>
              <li>✗ LLM модели недоступны</li>
            </ul>
            <button 
              className={`tariff-button ${selectedTariff === 'user' ? 'active' : ''}`}
              onClick={() => handleSubscribe('user')}
            >
              {selectedTariff === 'user' ? 'Активен' : 'Подписаться'}
            </button>
          </div>

          {/* Тариф: Для бизнеса */}
          <div className={`tariff-card ${selectedTariff === 'business' ? 'selected' : ''}`}>
            <div className="tariff-header">
              <h3 className="tariff-title">Для бизнеса</h3>
              <div className="tariff-price">₽999/мес</div>
            </div>
            <div className="tariff-description">
              Полный доступ ко всем LLM моделям
            </div>
            <ul className="tariff-features">
              <li>✓ Все NLP модели (бесплатно)</li>
              <li>✓ Qwen для рерайта</li>
              <li>✓ Yandex Алиса для рерайта</li>
              <li>✓ Qwen для сокращения</li>
              <li>✓ Yandex Алиса для сокращения</li>
            </ul>
            <button 
              className={`tariff-button ${selectedTariff === 'business' ? 'active' : ''}`}
              onClick={() => handleSubscribe('business')}
            >
              {selectedTariff === 'business' ? 'Активен' : 'Подписаться'}
            </button>
          </div>

          {/* Тариф: Настраиваемый */}
          <div className={`tariff-card ${selectedTariff === 'custom' ? 'selected' : ''}`}>
            <div className="tariff-header">
              <h3 className="tariff-title">Настраиваемый</h3>
              <div className="tariff-price">От ₽99/функция</div>
            </div>
            <div className="tariff-description">
              Выберите нужные функции отдельно
            </div>
            <div className="custom-features">
              <div className="custom-feature-item">
                <label className="custom-feature-label">
                  <input
                    type="checkbox"
                    checked={customFeatures.rewrite_qwen}
                    onChange={() => handleCustomFeatureToggle('rewrite_qwen')}
                    disabled={selectedTariff !== 'custom'}
                  />
                  <span>Qwen для рерайта - ₽99/мес</span>
                </label>
              </div>
              <div className="custom-feature-item">
                <label className="custom-feature-label">
                  <input
                    type="checkbox"
                    checked={customFeatures.rewrite_yandex}
                    onChange={() => handleCustomFeatureToggle('rewrite_yandex')}
                    disabled={selectedTariff !== 'custom'}
                  />
                  <span>Yandex Алиса для рерайта - ₽99/мес</span>
                </label>
              </div>
              <div className="custom-feature-item">
                <label className="custom-feature-label">
                  <input
                    type="checkbox"
                    checked={customFeatures.summary_qwen}
                    onChange={() => handleCustomFeatureToggle('summary_qwen')}
                    disabled={selectedTariff !== 'custom'}
                  />
                  <span>Qwen для сокращения - ₽99/мес</span>
                </label>
              </div>
              <div className="custom-feature-item">
                <label className="custom-feature-label">
                  <input
                    type="checkbox"
                    checked={customFeatures.summary_yandex}
                    onChange={() => handleCustomFeatureToggle('summary_yandex')}
                    disabled={selectedTariff !== 'custom'}
                  />
                  <span>Yandex Алиса для сокращения - ₽99/мес</span>
                </label>
              </div>
            </div>
            <button 
              className={`tariff-button ${selectedTariff === 'custom' ? 'active' : ''}`}
              onClick={() => {
                if (Object.values(customFeatures).some(v => v)) {
                  handleSubscribe('custom')
                } else {
                  alert('Выберите хотя бы одну функцию')
                }
              }}
            >
              {selectedTariff === 'custom' ? 'Активен' : 'Подписаться'}
            </button>
          </div>

          <div className="tariff-note">
            <p>💡 NLP модели (RUT5, FLAN-T5, Gazeta) остаются бесплатными для всех пользователей</p>
          </div>
        </div>
      </div>
    </div>
  )
}



