import { useEffect, useState } from 'react'
import type { CompanyConfig } from '../../shared/types'
import Onboarding from './pages/Onboarding'
import Main from './pages/Main'
import Settings from './pages/Settings'

type Route = 'loading' | 'onboarding' | 'main' | 'settings'

export default function App() {
  const [route, setRoute] = useState<Route>('loading')
  const [company, setCompany] = useState<CompanyConfig | null>(null)

  useEffect(() => {
    window.api.config.get()
      .then((res) => {
        if (res.success && res.data) {
          setCompany(res.data)
          setRoute('main')
        } else {
          setRoute('onboarding')
        }
      })
      .catch(() => setRoute('onboarding'))
  }, [])

  if (route === 'loading') {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner />
      </div>
    )
  }

  if (route === 'onboarding') {
    return (
      <Onboarding
        onDone={(config) => {
          setCompany(config)
          setRoute('main')
        }}
      />
    )
  }

  if (route === 'settings' && company) {
    return (
      <Settings
        current={company}
        onSaved={(config) => {
          setCompany(config)
          setRoute('main')
        }}
        onBack={() => setRoute('main')}
      />
    )
  }

  return <Main company={company!} onOpenSettings={() => setRoute('settings')} />
}

function Spinner() {
  return (
    <div
      className="h-4 w-4 rounded-full border-2 border-[--color-border] border-t-[--color-accent]"
      style={{ animation: 'spin 0.7s linear infinite' }}
    />
  )
}
