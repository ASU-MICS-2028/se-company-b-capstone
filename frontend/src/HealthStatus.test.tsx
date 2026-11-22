import { render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { HealthStatus } from './HealthStatus'

afterEach(() => vi.unstubAllGlobals())

test('shows API and DB status from /api/health', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ status: 'ok', version: '0.1.0', db: 'ok' }),
    }),
  )
  render(<HealthStatus />)
  expect(await screen.findByText('API: ok · DB: ok · v0.1.0')).toBeInTheDocument()
  expect(fetch).toHaveBeenCalledWith('/api/health')
})

test('shows unreachable when the API is down', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
  render(<HealthStatus />)
  expect(await screen.findByText('API: unreachable')).toBeInTheDocument()
})
