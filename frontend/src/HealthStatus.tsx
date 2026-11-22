import { useEffect, useState } from 'react'

type Health = { status: string; version: string; db: string }

export function HealthStatus() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setError(true))
  }, [])

  if (error) return <p role="status">API: unreachable</p>
  if (!health) return <p role="status">API: checking…</p>
  return (
    <p role="status">
      API: {health.status} · DB: {health.db} · v{health.version}
    </p>
  )
}
