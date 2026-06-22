import { useEffect, useState, createContext, useContext, useCallback, useRef } from 'react'

interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

const ToastContext = createContext<{ toast: (msg: string, type?: ToastItem['type']) => void }>({ toast: () => {} })

export function useToast() { return useContext(ToastContext) }

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(0)

  const toast = useCallback((message: string, type: ToastItem['type'] = 'info') => {
    const id = ++nextId.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[9999] space-y-2 pointer-events-none">
        {toasts.map(t => <ToastMessage key={t.id} item={t} />)}
      </div>
    </ToastContext.Provider>
  )
}

function ToastMessage({ item }: { item: ToastItem }) {
  const [visible, setVisible] = useState(false)
  useEffect(() => { requestAnimationFrame(() => setVisible(true)) }, [])

  const icon = { success: '✓', error: '✕', info: 'ℹ' }[item.type]
  const colors = {
    success: 'border-success/30 text-success',
    error: 'border-error/30 text-error',
    info: 'border-accent/30 text-accent',
  }

  return (
    <div className={`pointer-events-auto flex items-center gap-2.5 px-4 py-3 bg-surface-1 border rounded-lg shadow-lg text-[13px] transition-all duration-200 ${colors[item.type]} ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}>
      <span className="text-[14px] font-bold">{icon}</span>
      <span className="text-text-primary">{item.message}</span>
    </div>
  )
}
