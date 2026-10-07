import { createContext } from 'react'

export type ToastVariant = 'success' | 'error'

export type Toast = {
  id: string
  message: string
  variant: ToastVariant
}

export type ToastContextValue = {
  showToast: (message: string, variant?: ToastVariant) => void
}

export const ToastContext = createContext<ToastContextValue | undefined>(undefined)
