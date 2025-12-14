'use client'

import { useEffect, useState } from 'react'

interface FallingElement {
  id: number
  left: number
  delay: number
  duration: number
  size: number
}

export default function FallingElements() {
  const [elements, setElements] = useState<FallingElement[]>([])

  useEffect(() => {
    // Создаем 15 падающих элементов
    const newElements: FallingElement[] = Array.from({ length: 15 }, (_, i) => ({
      id: i,
      left: Math.random() * 100, // Случайная позиция по горизонтали (0-100%)
      delay: Math.random() * 5, // Случайная задержка (0-5 секунд)
      duration: 10 + Math.random() * 10, // Длительность падения (10-20 секунд)
      size: 4 + Math.random() * 8, // Размер элемента (4-12px)
    }))
    setElements(newElements)
  }, [])

  return (
    <div className="falling-elements-container">
      {elements.map((element) => (
        <div
          key={element.id}
          className="falling-element"
          style={{
            left: `${element.left}%`,
            animationDelay: `${element.delay}s`,
            animationDuration: `${element.duration}s`,
            width: `${element.size}px`,
            height: `${element.size}px`,
          }}
        />
      ))}
    </div>
  )
}

