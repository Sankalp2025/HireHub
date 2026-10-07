import axios from 'axios'
import { getAccessToken } from './auth'

export type ApiErrorShape = {
  code: string
  message: string
}

export type ApiResponse<T> = {
  data: T | null
  error: ApiErrorShape | null
}

export type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const accessToken = getAccessToken()

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

export function postFormData<T>(url: string, formData: FormData) {
  // Let the browser set its own multipart boundary instead of the instance's
  // default JSON content type.
  return api.post<T>(url, formData, { headers: { 'Content-Type': undefined } })
}

export function getApiErrorMessage(error: unknown, fallbackMessage: string) {
  if (axios.isAxiosError<ApiResponse<unknown>>(error)) {
    return error.response?.data?.error?.message ?? fallbackMessage
  }

  if (error instanceof Error) {
    return error.message
  }

  return fallbackMessage
}
