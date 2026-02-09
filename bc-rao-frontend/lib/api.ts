/**
 * API client for backend communication.
 * Handles requests to FastAPI backend with proper error handling.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1'

interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

interface ApiResponse<T> {
  data?: T
  error?: ApiError
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async post<T>(path: string, body: any, token?: string): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          error: data.error || {
            code: 'UNKNOWN_ERROR',
            message: 'An unexpected error occurred',
          },
        }
      }

      return { data }
    } catch (error) {
      return {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to server',
          details: { error: String(error) },
        },
      }
    }
  }

  async get<T>(path: string, token?: string): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {}

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'GET',
        headers,
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          error: data.error || {
            code: 'UNKNOWN_ERROR',
            message: 'An unexpected error occurred',
          },
        }
      }

      return { data }
    } catch (error) {
      return {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to server',
          details: { error: String(error) },
        },
      }
    }
  }

  async patch<T>(path: string, body: any, token?: string): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body),
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          error: data.error || {
            code: 'UNKNOWN_ERROR',
            message: 'An unexpected error occurred',
          },
        }
      }

      return { data }
    } catch (error) {
      return {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to server',
          details: { error: String(error) },
        },
      }
    }
  }

  async delete<T>(path: string, token?: string): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {}

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'DELETE',
        headers,
      })

      // DELETE might return 204 No Content
      if (response.status === 204) {
        return { data: undefined as T }
      }

      const data = await response.json()

      if (!response.ok) {
        return {
          error: data.error || {
            code: 'UNKNOWN_ERROR',
            message: 'An unexpected error occurred',
          },
        }
      }

      return { data }
    } catch (error) {
      return {
        error: {
          code: 'NETWORK_ERROR',
          message: 'Failed to connect to server',
          details: { error: String(error) },
        },
      }
    }
  }
}

export const apiClient = new ApiClient(API_BASE_URL)
