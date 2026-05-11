'use client'
import React from 'react'

export function Toaster() {
  return <div id="toaster-container" className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" />
}

export function toast(message, type = 'info') {
  const container = document.getElementById('toaster-container')
  if (!container) return

  const toastElement = document.createElement('div')
  const colors = {
    error: 'bg-red-500 border-red-600',
    success: 'bg-teal-500 border-teal-600',
    info: 'bg-navy-700 border-navy-600'
  }
  
  toastElement.className = `${colors[type] || colors.info} text-white px-4 py-3 rounded-lg shadow-xl border animate-in slide-in-from-right-full transition-all duration-300 opacity-0`
  toastElement.innerText = message
  
  container.appendChild(toastElement)
  
  // Trigger animation
  setTimeout(() => {
    toastElement.classList.remove('opacity-0')
  }, 10)

  // Remove after 3 seconds
  setTimeout(() => {
    toastElement.classList.add('opacity-0')
    setTimeout(() => {
      container.removeChild(toastElement)
    }, 300)
  }, 3000)
}
