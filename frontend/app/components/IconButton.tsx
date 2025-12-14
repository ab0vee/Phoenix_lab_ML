'use client'

import React from 'react'

interface IconButtonProps {
  icon: React.ReactNode
  label: string
  onClick: () => void
  className?: string
}

export default function IconButton({ icon, label, onClick, className = '' }: IconButtonProps) {
  return (
    <button
      className={`icon-btn ${className}`}
      onClick={onClick}
      aria-label={label}
    >
      <span className="icon-btn-icon">{icon}</span>
      <span className="icon-btn-label">{label}</span>
    </button>
  )
}



