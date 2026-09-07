import { useState } from 'react'
import type { CompanyConfig } from '@shared/types'
import { formatCNPJ } from '@shared/utils'

interface Props {
  onDone: (config: CompanyConfig) => void
}

export default function Onboarding({ onDone }: Props) {
  const [form, setForm] = useState({ name: '', cnpj: '', address: '', city: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isValid = form.name.trim().length > 0 && form.cnpj.length >= 18 && form.city.trim().length > 0

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid || saving) return
    setSaving(true)
    setError(null)
    const config: CompanyConfig = {
      name: form.name.trim(), cnpj: form.cnpj,
      address: form.address.trim(), city: form.city.trim(),
    }
    const res = await window.api.config.set(config)
    setSaving(false)
    if (res.success) onDone(config)
    else setError(res.error)
  }

  async function handleDemo() {
    if (saving) return
    setSaving(true)
    setError(null)
    const config: CompanyConfig = {
      name: 'Empresa Demonstração Ltda',
      cnpj: '00.000.000/0001-91',
      address: 'Av. Exemplo, 100',
      city: 'São Paulo - SP',
    }
    const res = await window.api.config.set(config)
    setSaving(false)
    if (res.success) onDone(config)
    else setError(res.error)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--color-bg)' }}>
      {/* drag region */}
      <div style={{ height: '40px', flexShrink: 0, background: 'var(--color-deep)', WebkitAppRegion: 'drag', display: 'flex', alignItems: 'center', paddingLeft: '16px' } as React.CSSProperties}>
        <Wordmark />
      </div>

      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px' }}>
        <div style={{ width: '100%', maxWidth: '360px' }}>

          <div style={{ marginBottom: '28px' }}>
            <p style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--color-accent)', marginBottom: '8px' }}>
              Configuração inicial
            </p>
            <h1 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text)', letterSpacing: '-0.3px', lineHeight: 1.2 }}>
              Dados da empresa
            </h1>
            <p style={{ marginTop: '6px', fontSize: '12px', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              Aparecem em todos os recibos. Pode alterar a qualquer momento.
            </p>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Field label="Nome" value={form.name} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="GF Muniz Artefactos de Cerâmica" autoFocus />
            <Field label="CNPJ" value={form.cnpj} onChange={(v) => setForm((f) => ({ ...f, cnpj: formatCNPJ(v) }))} placeholder="00.000.000/0000-00" />
            <Field label="Endereço" value={form.address} onChange={(v) => setForm((f) => ({ ...f, address: v }))} placeholder="Rua das Flores, 123" />
            <Field label="Cidade / UF" value={form.city} onChange={(v) => setForm((f) => ({ ...f, city: v }))} placeholder="São Paulo - SP" />

            {error && (
              <div style={{ borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: '11px', color: 'var(--color-error)', background: 'var(--color-error-muted)' }}>
                {error}
              </div>
            )}

            <button type="submit" disabled={!isValid || saving}
              style={{
                marginTop: '4px', width: '100%', padding: '11px',
                borderRadius: 'var(--radius-md)', border: 'none',
                background: isValid && !saving ? 'var(--color-primary)' : 'var(--color-surface-elevated)',
                color: isValid && !saving ? 'white' : 'var(--color-text-muted)',
                fontSize: '13px', fontWeight: 700,
                cursor: !isValid || saving ? 'not-allowed' : 'pointer',
                letterSpacing: '0.03em', fontFamily: 'var(--font-sans)',
              }}
            >
              {saving ? 'Salvando...' : 'Continuar'}
            </button>
          </form>

          <div style={{ marginTop: '18px', textAlign: 'center' }}>
            <button type="button" onClick={() => void handleDemo()} disabled={saving}
              style={{
                background: 'none', border: 'none', padding: '4px',
                fontSize: '11px', fontFamily: 'var(--font-sans)',
                color: 'var(--color-text-muted)',
                cursor: saving ? 'not-allowed' : 'pointer',
              }}
            >
              Apenas testando?{' '}
              <span style={{ color: 'var(--color-accent)', fontWeight: 600 }}>
                Carregar dados de exemplo
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Wordmark() {
  return (
    <span style={{ fontFamily: 'var(--font-sans)', fontSize: '16px', lineHeight: 1, WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
      <span style={{ fontWeight: 300, color: 'white' }}>recibo</span>
      <span style={{ fontWeight: 800, color: '#22C55E' }}>pro</span>
    </span>
  )
}

function Field({ label, value, onChange, placeholder, autoFocus }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; autoFocus?: boolean
}) {
  const [focused, setFocused] = useState(false)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        {label}
      </label>
      <input
        type="text" value={value} placeholder={placeholder} autoFocus={autoFocus}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          background: 'var(--color-surface)',
          border: `1px solid ${focused ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '8px 10px', fontSize: '12px',
          color: 'var(--color-text)', outline: 'none',
          fontFamily: 'var(--font-sans)',
        }}
      />
    </div>
  )
}
