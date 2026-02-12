/**
 * Global test setup for Vitest
 * Mocks Next.js dependencies and browser APIs
 */

import { vi, beforeAll, afterEach } from 'vitest'

// Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  })),
  useParams: vi.fn(() => ({})),
  useSearchParams: vi.fn(() => ({
    get: vi.fn(),
    getAll: vi.fn(),
    has: vi.fn(),
    entries: vi.fn(),
    keys: vi.fn(),
    values: vi.fn(),
    toString: vi.fn(),
  })),
  usePathname: vi.fn(() => '/'),
  notFound: vi.fn(),
  redirect: vi.fn(),
}))

// Mock Next.js headers
vi.mock('next/headers', () => ({
  cookies: vi.fn(() => ({
    get: vi.fn(),
    set: vi.fn(),
    delete: vi.fn(),
    has: vi.fn(),
    getAll: vi.fn(),
  })),
  headers: vi.fn(() => ({
    get: vi.fn(),
    has: vi.fn(),
    entries: vi.fn(),
    keys: vi.fn(),
    values: vi.fn(),
  })),
}))

// Mock EventSource for SSE testing
class MockEventSource {
  url: string
  readyState: number = 0
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null

  constructor(url: string) {
    this.url = url
    // Simulate connection
    setTimeout(() => {
      this.readyState = 1
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 0)
  }

  close() {
    this.readyState = 2
  }

  addEventListener(event: string, handler: EventListener) {
    if (event === 'open' && !this.onopen) {
      this.onopen = handler as (event: Event) => void
    } else if (event === 'message' && !this.onmessage) {
      this.onmessage = handler as (event: MessageEvent) => void
    } else if (event === 'error' && !this.onerror) {
      this.onerror = handler as (event: Event) => void
    }
  }

  removeEventListener() {
    // No-op for tests
  }
}

// @ts-ignore - Add to global
global.EventSource = MockEventSource as any

// Mock fetch globally
global.fetch = vi.fn()

beforeAll(() => {
  // Setup can be extended here
})

afterEach(() => {
  vi.clearAllMocks()
})
