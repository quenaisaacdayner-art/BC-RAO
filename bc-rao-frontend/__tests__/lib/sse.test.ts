/**
 * Test suite for sse.ts
 * Tests SSE URL construction for production vs development environments
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { getSSEUrl } from '@/lib/sse'

describe('sse', () => {
  const originalEnv = process.env.NEXT_PUBLIC_API_URL

  afterEach(() => {
    // Restore original environment
    process.env.NEXT_PUBLIC_API_URL = originalEnv
  })

  describe('getSSEUrl', () => {
    it('should return direct backend URL in production (Railway)', () => {
      process.env.NEXT_PUBLIC_API_URL =
        'https://production-production-a9aa.up.railway.app/v1'

      const url = getSSEUrl('/campaigns/test-123/collect/stream')

      expect(url).toBe(
        'https://production-production-a9aa.up.railway.app/v1/campaigns/test-123/collect/stream'
      )
    })

    it('should return Next.js proxy URL in development (localhost)', () => {
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/v1'

      const url = getSSEUrl('/campaigns/test-123/collect/stream')

      expect(url).toBe('/api/campaigns/test-123/collect/stream')
    })

    it('should return Next.js proxy URL when no env var is set', () => {
      delete process.env.NEXT_PUBLIC_API_URL

      const url = getSSEUrl('/campaigns/test-123/collect/stream')

      expect(url).toBe('/api/campaigns/test-123/collect/stream')
    })

    it('should return Next.js proxy URL when env var is empty', () => {
      process.env.NEXT_PUBLIC_API_URL = ''

      const url = getSSEUrl('/campaigns/test-123/collect/stream')

      expect(url).toBe('/api/campaigns/test-123/collect/stream')
    })

    it('should handle paths with leading slash correctly', () => {
      process.env.NEXT_PUBLIC_API_URL = 'https://backend.example.com/v1'

      const url = getSSEUrl('/some/path')

      expect(url).toBe('https://backend.example.com/v1/some/path')
    })

    it('should handle paths without leading slash correctly', () => {
      process.env.NEXT_PUBLIC_API_URL = 'https://backend.example.com/v1'

      const url = getSSEUrl('some/path')

      expect(url).toBe('https://backend.example.com/v1some/path')
    })

    it('should differentiate localhost from production URLs', () => {
      // Production URL (contains localhost but is production)
      process.env.NEXT_PUBLIC_API_URL = 'https://localhost.example.com/v1'

      const urlProd = getSSEUrl('/test')

      // Should use direct connection (not localhost)
      expect(urlProd).toBe('https://localhost.example.com/v1/test')

      // Actual localhost
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/v1'

      const urlDev = getSSEUrl('/test')

      // Should use proxy
      expect(urlDev).toBe('/api/test')
    })

    it('should handle various production backend URLs', () => {
      const productionUrls = [
        'https://api.production.com/v1',
        'https://backend.example.com/v1',
        'https://my-app.herokuapp.com/v1',
        'https://production-abc123.up.railway.app/v1',
      ]

      productionUrls.forEach((backendUrl) => {
        process.env.NEXT_PUBLIC_API_URL = backendUrl

        const url = getSSEUrl('/stream')

        expect(url).toBe(`${backendUrl}/stream`)
        expect(url).not.toContain('/api')
      })
    })

    it('should handle localhost variations for development', () => {
      const localhostUrls = [
        'http://localhost:8000/v1',
        'http://localhost:3000/v1',
        'http://localhost/v1',
      ]

      localhostUrls.forEach((backendUrl) => {
        process.env.NEXT_PUBLIC_API_URL = backendUrl

        const url = getSSEUrl('/stream')

        expect(url).toBe('/api/stream')
        expect(url).not.toContain('localhost')
      })
    })
  })

  describe('SSE URL routing strategy', () => {
    it('should use direct backend connection to avoid Vercel timeout in production', () => {
      // This validates the architectural decision documented in sse.ts
      // Vercel Hobby has 25s timeout, so we connect directly to Railway backend
      process.env.NEXT_PUBLIC_API_URL =
        'https://production-production-a9aa.up.railway.app/v1'

      const url = getSSEUrl('/campaigns/123/collect/stream')

      // Should NOT go through Vercel's /api routes
      expect(url).not.toContain('/api')
      // Should connect directly to Railway
      expect(url).toContain('railway.app')
    })

    it('should use Next.js proxy in development (no timeout issue)', () => {
      process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/v1'

      const url = getSSEUrl('/campaigns/123/collect/stream')

      // Should go through Next.js proxy in development
      expect(url).toContain('/api')
      // Should NOT expose localhost backend URL
      expect(url).not.toContain('localhost')
    })
  })
})
