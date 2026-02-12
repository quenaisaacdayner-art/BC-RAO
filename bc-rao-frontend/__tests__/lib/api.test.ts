/**
 * Test suite for api.ts
 * Tests API client error handling, authentication, and response parsing
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { apiClient } from '@/lib/api'

describe('api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('POST requests', () => {
    it('should include Authorization header when token is provided', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      })
      global.fetch = mockFetch

      await apiClient.post('/test', { data: 'test' }, 'test-token-123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token-123',
          }),
        })
      )
    })

    it('should not include Authorization header when token is not provided', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      })
      global.fetch = mockFetch

      await apiClient.post('/test', { data: 'test' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.any(String),
          }),
        })
      )
    })

    it('should include Content-Type header', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true }),
      })
      global.fetch = mockFetch

      await apiClient.post('/test', { data: 'test' })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('should return data on successful response', async () => {
      const mockData = { id: '123', name: 'Test' }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.post('/test', { data: 'test' })

      expect(result.data).toEqual(mockData)
      expect(result.error).toBeUndefined()
    })

    it('should return error when response is not ok', async () => {
      const mockError = {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Invalid input',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => mockError,
      })

      const result = await apiClient.post('/test', { data: 'test' })

      expect(result.error).toEqual(mockError.error)
      expect(result.data).toBeUndefined()
    })

    it('should return generic error when response has no error object', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({}),
      })

      const result = await apiClient.post('/test', { data: 'test' })

      expect(result.error).toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred',
      })
    })

    it('should return NETWORK_ERROR when fetch throws', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network failure'))

      const result = await apiClient.post('/test', { data: 'test' })

      expect(result.error).toEqual({
        code: 'NETWORK_ERROR',
        message: 'Failed to connect to server',
        details: { error: 'Error: Network failure' },
      })
      expect(result.data).toBeUndefined()
    })

    it('should stringify request body', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })
      global.fetch = mockFetch

      const body = { test: 'data', nested: { value: 123 } }
      await apiClient.post('/test', body)

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify(body),
        })
      )
    })
  })

  describe('GET requests', () => {
    it('should include Authorization header when token is provided', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: 'test' }),
      })
      global.fetch = mockFetch

      await apiClient.get('/test', 'test-token-456')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token-456',
          }),
        })
      )
    })

    it('should not include Content-Type header for GET', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ data: 'test' }),
      })
      global.fetch = mockFetch

      await apiClient.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Content-Type': expect.any(String),
          }),
        })
      )
    })

    it('should return data on successful response', async () => {
      const mockData = { items: [1, 2, 3] }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.get('/test')

      expect(result.data).toEqual(mockData)
      expect(result.error).toBeUndefined()
    })

    it('should return error on failed response', async () => {
      const mockError = {
        error: {
          code: 'NOT_FOUND',
          message: 'Resource not found',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => mockError,
      })

      const result = await apiClient.get('/test')

      expect(result.error).toEqual(mockError.error)
      expect(result.data).toBeUndefined()
    })

    it('should handle network errors', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Timeout'))

      const result = await apiClient.get('/test')

      expect(result.error?.code).toBe('NETWORK_ERROR')
      expect(result.error?.message).toBe('Failed to connect to server')
    })
  })

  describe('PATCH requests', () => {
    it('should include all required headers with token', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ updated: true }),
      })
      global.fetch = mockFetch

      await apiClient.patch('/test', { field: 'value' }, 'token-789')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: 'Bearer token-789',
          }),
          body: JSON.stringify({ field: 'value' }),
        })
      )
    })

    it('should return data on successful update', async () => {
      const mockData = { id: '123', updated_at: '2024-01-01' }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockData,
      })

      const result = await apiClient.patch('/test', { field: 'new' })

      expect(result.data).toEqual(mockData)
      expect(result.error).toBeUndefined()
    })

    it('should handle patch errors', async () => {
      const mockError = {
        error: {
          code: 'CONFLICT',
          message: 'Resource conflict',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => mockError,
      })

      const result = await apiClient.patch('/test', {})

      expect(result.error).toEqual(mockError.error)
    })
  })

  describe('DELETE requests', () => {
    it('should include Authorization header when token is provided', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        status: 204,
      })
      global.fetch = mockFetch

      await apiClient.delete('/test', 'token-delete')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({
            Authorization: 'Bearer token-delete',
          }),
        })
      )
    })

    it('should handle 204 No Content response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        status: 204,
      })

      const result = await apiClient.delete('/test')

      expect(result.data).toBeUndefined()
      expect(result.error).toBeUndefined()
    })

    it('should return data on 200 response with body', async () => {
      const mockData = { deleted_id: '123' }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => mockData,
      })

      const result = await apiClient.delete('/test')

      expect(result.data).toEqual(mockData)
      expect(result.error).toBeUndefined()
    })

    it('should handle delete errors', async () => {
      const mockError = {
        error: {
          code: 'FORBIDDEN',
          message: 'Cannot delete resource',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => mockError,
      })

      const result = await apiClient.delete('/test')

      expect(result.error).toEqual(mockError.error)
    })
  })

  describe('API base URL construction', () => {
    it('should use /api as default base URL', async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({}),
      })
      global.fetch = mockFetch

      await apiClient.get('/campaigns')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/campaigns',
        expect.any(Object)
      )
    })
  })

  describe('Error response edge cases', () => {
    it('should handle malformed error response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ unexpected: 'format' }),
      })

      const result = await apiClient.post('/test', {})

      expect(result.error).toEqual({
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected error occurred',
      })
    })

    it('should handle JSON parse errors', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      const result = await apiClient.get('/test')

      expect(result.error?.code).toBe('NETWORK_ERROR')
      expect(result.error?.details?.error).toContain('Invalid JSON')
    })

    it('should convert non-Error exceptions to strings', async () => {
      global.fetch = vi.fn().mockRejectedValue('string error')

      const result = await apiClient.post('/test', {})

      expect(result.error).toEqual({
        code: 'NETWORK_ERROR',
        message: 'Failed to connect to server',
        details: { error: 'string error' },
      })
    })
  })

  describe('Authentication scenarios', () => {
    it('should handle 401 Unauthorized response', async () => {
      const mockError = {
        error: {
          code: 'UNAUTHORIZED',
          message: 'Invalid or expired token',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => mockError,
      })

      const result = await apiClient.get('/protected', 'expired-token')

      expect(result.error).toEqual(mockError.error)
      expect(result.error?.code).toBe('UNAUTHORIZED')
    })

    it('should handle 403 Forbidden response', async () => {
      const mockError = {
        error: {
          code: 'FORBIDDEN',
          message: 'Insufficient permissions',
        },
      }
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: async () => mockError,
      })

      const result = await apiClient.get('/admin', 'user-token')

      expect(result.error).toEqual(mockError.error)
      expect(result.error?.code).toBe('FORBIDDEN')
    })
  })
})
