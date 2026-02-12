/**
 * Test suite for use-debounce.ts
 * Tests debounce hook behavior with delays and rapid changes
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useDebounce } from '@/hooks/use-debounce'

describe('useDebounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should return initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500))

    expect(result.current).toBe('initial')
  })

  it('should update debounced value after specified delay', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    expect(result.current).toBe('initial')

    // Update value
    rerender({ value: 'updated', delay: 500 })

    // Immediately after change, should still be initial
    expect(result.current).toBe('initial')

    // Advance timers by delay amount
    vi.advanceTimersByTime(500)

    // Now should be updated
    await waitFor(() => {
      expect(result.current).toBe('updated')
    })
  })

  it('should reset timer on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    // First change
    rerender({ value: 'change1', delay: 500 })
    vi.advanceTimersByTime(300)

    // Second change before first completes
    rerender({ value: 'change2', delay: 500 })
    vi.advanceTimersByTime(300)

    // Still should be initial (only 600ms total, but timer reset)
    expect(result.current).toBe('initial')

    // Third change
    rerender({ value: 'change3', delay: 500 })

    // Complete the full delay from last change
    vi.advanceTimersByTime(500)

    // Should update to latest value
    await waitFor(() => {
      expect(result.current).toBe('change3')
    })
  })

  it('should use specified delay time', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 1000 },
      }
    )

    rerender({ value: 'updated', delay: 1000 })

    // After 500ms, should still be initial
    vi.advanceTimersByTime(500)
    expect(result.current).toBe('initial')

    // After 999ms, should still be initial
    vi.advanceTimersByTime(499)
    expect(result.current).toBe('initial')

    // After 1000ms, should be updated
    vi.advanceTimersByTime(1)
    await waitFor(() => {
      expect(result.current).toBe('updated')
    })
  })

  it('should handle different delay values', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 100 },
      }
    )

    rerender({ value: 'first', delay: 100 })
    vi.advanceTimersByTime(100)

    await waitFor(() => {
      expect(result.current).toBe('first')
    })

    // Change delay duration
    rerender({ value: 'second', delay: 500 })
    vi.advanceTimersByTime(500)

    await waitFor(() => {
      expect(result.current).toBe('second')
    })
  })

  it('should work with different data types', async () => {
    // String
    const { result: stringResult, rerender: rerenderString } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'test', delay: 100 },
      }
    )
    rerenderString({ value: 'updated', delay: 100 })
    vi.advanceTimersByTime(100)
    await waitFor(() => {
      expect(stringResult.current).toBe('updated')
    })

    // Number
    const { result: numberResult, rerender: rerenderNumber } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 0, delay: 100 },
      }
    )
    rerenderNumber({ value: 42, delay: 100 })
    vi.advanceTimersByTime(100)
    await waitFor(() => {
      expect(numberResult.current).toBe(42)
    })

    // Boolean
    const { result: boolResult, rerender: rerenderBool } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: false, delay: 100 },
      }
    )
    rerenderBool({ value: true, delay: 100 })
    vi.advanceTimersByTime(100)
    await waitFor(() => {
      expect(boolResult.current).toBe(true)
    })

    // Object
    const { result: objResult, rerender: rerenderObj } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: { id: 1 }, delay: 100 },
      }
    )
    const newObj = { id: 2 }
    rerenderObj({ value: newObj, delay: 100 })
    vi.advanceTimersByTime(100)
    await waitFor(() => {
      expect(objResult.current).toEqual(newObj)
    })

    // Array
    const { result: arrResult, rerender: rerenderArr } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: [1, 2], delay: 100 },
      }
    )
    const newArr = [3, 4, 5]
    rerenderArr({ value: newArr, delay: 100 })
    vi.advanceTimersByTime(100)
    await waitFor(() => {
      expect(arrResult.current).toEqual(newArr)
    })
  })

  it('should cleanup timer on unmount', () => {
    const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout')

    const { unmount } = renderHook(() => useDebounce('test', 500))

    unmount()

    expect(clearTimeoutSpy).toHaveBeenCalled()
  })

  it('should handle multiple rapid updates correctly', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: '', delay: 300 },
      }
    )

    // Simulate typing "hello"
    const chars = ['h', 'he', 'hel', 'hell', 'hello']

    chars.forEach((char, index) => {
      rerender({ value: char, delay: 300 })
      if (index < chars.length - 1) {
        vi.advanceTimersByTime(50) // Simulate fast typing
      }
    })

    // Value should still be empty (timer keeps resetting)
    expect(result.current).toBe('')

    // Wait for final delay
    vi.advanceTimersByTime(300)

    // Should update to final value
    await waitFor(() => {
      expect(result.current).toBe('hello')
    })
  })

  it('should handle zero delay', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 0 },
      }
    )

    rerender({ value: 'updated', delay: 0 })

    // Even with 0 delay, setTimeout is still async
    vi.advanceTimersByTime(0)

    await waitFor(() => {
      expect(result.current).toBe('updated')
    })
  })

  describe('Real-world use cases', () => {
    it('should debounce search input (typical 500ms delay)', async () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        {
          initialProps: { value: '', delay: 500 },
        }
      )

      // User types quickly
      rerender({ value: 'r', delay: 500 })
      vi.advanceTimersByTime(100)
      rerender({ value: 're', delay: 500 })
      vi.advanceTimersByTime(100)
      rerender({ value: 'rea', delay: 500 })
      vi.advanceTimersByTime(100)
      rerender({ value: 'reac', delay: 500 })
      vi.advanceTimersByTime(100)
      rerender({ value: 'react', delay: 500 })

      // Should still be empty during typing
      expect(result.current).toBe('')

      // Wait for debounce delay
      vi.advanceTimersByTime(500)

      // Should update to final search term
      await waitFor(() => {
        expect(result.current).toBe('react')
      })
    })

    it('should debounce window resize events', async () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        {
          initialProps: { value: { width: 1920, height: 1080 }, delay: 200 },
        }
      )

      // Simulate rapid resize events
      const resizes = [
        { width: 1900, height: 1060 },
        { width: 1880, height: 1040 },
        { width: 1860, height: 1020 },
        { width: 1840, height: 1000 },
      ]

      resizes.forEach((size) => {
        rerender({ value: size, delay: 200 })
        vi.advanceTimersByTime(50)
      })

      // Original value should still be there
      expect(result.current).toEqual({ width: 1920, height: 1080 })

      // Wait for debounce
      vi.advanceTimersByTime(200)

      // Should update to final size
      await waitFor(() => {
        expect(result.current).toEqual({ width: 1840, height: 1000 })
      })
    })

    it('should debounce API call parameters', async () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        {
          initialProps: {
            value: { page: 1, filters: {} },
            delay: 300,
          },
        }
      )

      // User rapidly changes filters
      rerender({
        value: { page: 1, filters: { status: 'active' } },
        delay: 300,
      })
      vi.advanceTimersByTime(100)

      rerender({
        value: { page: 1, filters: { status: 'active', type: 'post' } },
        delay: 300,
      })
      vi.advanceTimersByTime(100)

      // Original params should still be there
      expect(result.current).toEqual({ page: 1, filters: {} })

      // Wait for debounce
      vi.advanceTimersByTime(300)

      // Should update to final params
      await waitFor(() => {
        expect(result.current).toEqual({
          page: 1,
          filters: { status: 'active', type: 'post' },
        })
      })
    })
  })
})
