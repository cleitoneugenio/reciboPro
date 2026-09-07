import { useState } from 'react'
import type { CompanyConfig, Worker } from '@shared/types'
import { DEFAULT_TEMPLATE, formatCNPJ } from '@shared/utils'
import ReceiptPreview from '../components/ReceiptPreview'

interface Props {
  current: CompanyConfig
  onSaved: (config: CompanyConfig) => void
  onBack: () => void
}

const MOCK_WORKER: Worker = { id: 0, name: 'João da Silva', total: 395 }

export default function Settings({ current, onSaved, onBack }: Props) {
  const [form, setForm] = useState({
    ...current,
    headerShowName:    current.headerShowName    ?? true,
    headerShowCnpj:    current.headerShowCnpj    ?? true,
    headerShowAddress: current.headerShowAddress ?? true,
    receiptTitle: current.receiptTitle ?? '',
    receiptTemplate: current.receiptTemplate ?? '',
    signatureSpacing: current.signatureSpacing ?? 44,
    highlightValue: current.highlightValue ?? false,
    highlightValueSize: current.highlightValueSize ?? 12,
    highlightValuePosition: current.highlightValuePosition ?? 'box',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previewCount, setPreviewCount] = useState(1)

  const isValid = form.name.trim().length > 0 && form.cnpj.length >= 18 && form.city.trim().length > 0
  const isDirty = JSON.stringify(form) !== JSON.stringify(current)

  // Live company config derived from form for preview
  const previewCompany: CompanyConfig = {
    name: form.name || 'Nome da empresa',
    cnpj: form.cnpj || '00.000.000/0000-00',
    address: form.address,
    city: form.city || 'Cidade',
    headerShowName:    form.headerShowName,
    headerShowCnpj:    form.headerShowCnpj,
    headerShowAddress: form.headerShowAddress,
    receiptTitle: form.receiptTitle || undefined,
    receiptTemplate: form.receiptTemplate || undefined,
    signatureSpacing: form.signatureSpacing,
    highlightValue: form.highlightValue || undefined,
    highlightValueSize: form.highlightValue ? form.highlightValueSize : undefined,
    highlightValuePosition: form.highlightValue ? form.highlightValuePosition : undefined,
  }

  async function handleSave() {
    if (!isValid || !isDirty) return
    setSaving(true)
    setError(null)
    const config: CompanyConfig = {
      name: form.name.trim(), cnpj: form.cnpj,
      address: form.address.trim(), city: form.city.trim(),
      headerShowName:    form.headerShowName,
      headerShowCnpj:    form.headerShowCnpj,
      headerShowAddress: form.headerShowAddress,
      receiptTitle: form.receiptTitle.trim() || undefined,
      receiptTemplate: form.receiptTemplate.trim() || undefined,
      signatureSpacing: form.signatureSpacing,
      highlightValue: form.highlightValue || undefined,
      highlightValueSize: form.highlightValue ? form.highlightValueSize : undefined,
      highlightValuePosition: form.highlightValue ? form.highlightValuePosition : undefined,
    }
    const res = await window.api.config.set(config)
    setSaving(false)
    if (res.success) onSaved(config)
    else setError(res.error)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--color-bg)' }}>
      {/* Titlebar */}
      <div style={{ height: '40px', flexShrink: 0, background: 'var(--color-deep)', WebkitAppRegion: 'drag', display: 'flex', alignItems: 'center', paddingLeft: '16px' } as React.CSSProperties}>
        <Wordmark />
      </div>

      {/* Body — two columns */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* Left — form panel */}
        <div style={{ width: '380px', flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--color-border-subtle)' }}>
          {/* Panel header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 18px 10px', flexShrink: 0 }}>
            <button onClick={onBack}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '26px', height: '26px', borderRadius: 'var(--radius-md)', background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)', cursor: 'pointer', flexShrink: 0 }}>
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 2L4 6.5L8 11" />
              </svg>
            </button>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)' }}>Configurações</span>
          </div>

          {/* Scrollable fields */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '4px 18px 18px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <Field label="Nome" value={form.name} onChange={(v) => setForm((f) => ({ ...f, name: v }))} placeholder="GF Muniz Artefactos de Cerâmica" />
              <Field label="CNPJ" value={form.cnpj} onChange={(v) => setForm((f) => ({ ...f, cnpj: formatCNPJ(v) }))} placeholder="00.000.000/0000-00" />
              <Field label="Endereço" value={form.address} onChange={(v) => setForm((f) => ({ ...f, address: v }))} placeholder="Rua das Flores, 123" />
              <Field label="Cidade / UF" value={form.city} onChange={(v) => setForm((f) => ({ ...f, city: v }))} placeholder="São Paulo - SP" />

              <HeaderToggles
                showName={form.headerShowName}
                showCnpj={form.headerShowCnpj}
                showAddress={form.headerShowAddress}
                onChange={(key, val) => setForm((f) => ({ ...f, [key]: val }))}
              />

              <Field
                label="Título do recibo"
                value={form.receiptTitle}
                onChange={(v) => setForm((f) => ({ ...f, receiptTitle: v }))}
                placeholder="RECIBO DE PRESTAÇÃO DE SERVIÇO"
              />

              <SingleToggle
                label="Valor em destaque"
                checked={form.highlightValue}
                onChange={(v) => setForm((f) => ({ ...f, highlightValue: v }))}
              />

              {form.highlightValue && (
                <>
                  <SegmentedControl
                    label="Posição do valor"
                    options={[
                      { value: 'box',   label: 'Caixa separada' },
                      { value: 'title', label: 'Junto ao título' },
                    ]}
                    value={form.highlightValuePosition}
                    onChange={(v) => setForm((f) => ({ ...f, highlightValuePosition: v as 'box' | 'title' }))}
                  />
                  <SpacingField
                    label="Tamanho da fonte do valor"
                    value={form.highlightValueSize}
                    min={8} max={20}
                    onChange={(v) => setForm((f) => ({ ...f, highlightValueSize: v }))}
                  />
                </>
              )}

              <TemplateField value={form.receiptTemplate} onChange={(v) => setForm((f) => ({ ...f, receiptTemplate: v }))} />

              <SpacingField
                label="Espaço antes da assinatura"
                value={form.signatureSpacing}
                min={10} max={120}
                onChange={(v) => setForm((f) => ({ ...f, signatureSpacing: v }))}
              />

              {error && (
                <div style={{ borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: '11px', color: 'var(--color-error)', background: 'var(--color-error-muted)' }}>
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Save footer */}
          <div style={{ flexShrink: 0, borderTop: '1px solid var(--color-border-subtle)', padding: '14px 18px' }}>
            <button onClick={() => void handleSave()} disabled={!isValid || !isDirty || saving}
              style={{
                width: '100%', padding: '11px',
                borderRadius: 'var(--radius-md)', border: 'none',
                background: isValid && isDirty && !saving ? 'var(--color-primary)' : 'var(--color-surface-elevated)',
                color: isValid && isDirty && !saving ? 'white' : 'var(--color-text-muted)',
                fontSize: '13px', fontWeight: 700,
                cursor: !isValid || !isDirty || saving ? 'not-allowed' : 'pointer',
                letterSpacing: '0.03em', fontFamily: 'var(--font-sans)',
              }}>
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </div>

        {/* Right — live preview */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--color-deep)', overflow: 'hidden' }}>
          {/* Counter — fixo no topo */}
          <div style={{
            flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
            padding: '10px 16px',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
          }}>
            <button
              onClick={() => setPreviewCount((n) => Math.max(1, n - 1))}
              style={{ width: '26px', height: '26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: 'var(--color-surface-elevated)', color: 'var(--color-text)', fontSize: '15px', cursor: previewCount <= 1 ? 'not-allowed' : 'pointer', opacity: previewCount <= 1 ? 0.35 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              −
            </button>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', minWidth: '80px', textAlign: 'center' }}>
              {previewCount} {previewCount === 1 ? 'recibo/folha' : 'recibos/folha'}
            </span>
            <button
              onClick={() => setPreviewCount((n) => n + 1)}
              style={{ width: '26px', height: '26px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: 'var(--color-surface-elevated)', color: 'var(--color-text)', fontSize: '15px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              +
            </button>
          </div>

          {/* A4 sheet — scrollável */}
          <div style={{ flex: 1, overflow: 'auto', display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '24px' }}>
            <PreviewA4 count={previewCount} company={previewCompany} />
          </div>
        </div>
      </div>
    </div>
  )
}

function PreviewA4({ count, company }: { count: number; company: CompanyConfig }) {
  const W = 460
  const H = Math.round(W * 1.4142)
  const PAD_V = 24, PAD_H = 28
  const GAP = count > 1 ? 8 : 0
  const slotH = Math.floor((H - PAD_V * 2 - GAP * (count - 1)) / count)
  return (
    <div style={{
      width: `${W}px`,
      height: `${H}px`,
      background: 'white',
      boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
      borderRadius: '2px',
      padding: `${PAD_V}px ${PAD_H}px`,
      flexShrink: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: `${GAP}px`,
    }}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} style={{ height: `${slotH}px`, flexShrink: 0, overflow: 'hidden' }}>
          <ReceiptPreview
            worker={MOCK_WORKER}
            company={company}
            template={company.receiptTemplate}
            title={company.receiptTitle}
          />
        </div>
      ))}
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

const PLACEHOLDERS: { tag: string; desc: string }[] = [
  { tag: '[nome]', desc: 'Nome do funcionário' },
  { tag: '[total]', desc: 'Valor por extenso' },
  { tag: '[empresa]', desc: 'Nome da empresa' },
  { tag: '[cnpj]', desc: 'CNPJ' },
  { tag: '[cidade]', desc: 'Cidade' },
  { tag: '[endereco]', desc: 'Endereço' },
  { tag: '[data]', desc: 'Data do recibo' },
]

function HeaderToggles({ showName, showCnpj, showAddress, onChange }: {
  showName: boolean; showCnpj: boolean; showAddress: boolean
  onChange: (key: 'headerShowName' | 'headerShowCnpj' | 'headerShowAddress', val: boolean) => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        Cabeçalho do recibo
      </label>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
      }}>
        <ToggleRow label="Nome da empresa" checked={showName} onChange={(v) => onChange('headerShowName', v)} />
        <div style={{ height: '1px', background: 'var(--color-border-subtle)' }} />
        <ToggleRow label="CNPJ" checked={showCnpj} onChange={(v) => onChange('headerShowCnpj', v)} />
        <div style={{ height: '1px', background: 'var(--color-border-subtle)' }} />
        <ToggleRow label="Endereço" checked={showAddress} onChange={(v) => onChange('headerShowAddress', v)} last />
      </div>
    </div>
  )
}

function ToggleRow({ label, checked, onChange, last = false }: {
  label: string; checked: boolean; onChange: (v: boolean) => void; last?: boolean
}) {
  return (
    <div
      onClick={() => onChange(!checked)}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '9px 12px',
        cursor: 'pointer',
        borderRadius: last ? '0 0 var(--radius-md) var(--radius-md)' : undefined,
      }}
    >
      <span style={{ fontSize: '12px', color: 'var(--color-text)' }}>{label}</span>
      <div style={{
        width: '32px', height: '18px',
        borderRadius: '9px',
        background: checked ? 'var(--color-primary)' : 'var(--color-border)',
        position: 'relative',
        transition: 'background 0.15s',
        flexShrink: 0,
      }}>
        <div style={{
          position: 'absolute',
          top: '3px',
          left: checked ? '17px' : '3px',
          width: '12px', height: '12px',
          borderRadius: '50%',
          background: 'white',
          transition: 'left 0.15s',
        }} />
      </div>
    </div>
  )
}

function SpacingField({ label, value, min, max, onChange }: {
  label: string; value: number; min: number; max: number; onChange: (v: number) => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        {label}
      </label>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={() => onChange(Math.max(min, value - 4))}
          style={{ width: '30px', height: '30px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          −
        </button>
        <div style={{ flex: 1, height: '6px', background: 'var(--color-border)', borderRadius: '3px', position: 'relative', cursor: 'pointer' }}
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect()
            const ratio = (e.clientX - rect.left) / rect.width
            onChange(Math.round(min + ratio * (max - min)))
          }}>
          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${((value - min) / (max - min)) * 100}%`, background: 'var(--color-primary)', borderRadius: '3px', transition: 'width 0.1s' }} />
        </div>
        <button
          onClick={() => onChange(Math.min(max, value + 4))}
          style={{ width: '30px', height: '30px', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '16px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          +
        </button>
        <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', width: '28px', textAlign: 'right', flexShrink: 0 }}>{value}</span>
      </div>
    </div>
  )
}

function TemplateField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [focused, setFocused] = useState(false)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        Texto do recibo
      </label>
      <textarea
        value={value}
        placeholder="Deixe em branco para usar o texto padrão..."
        rows={5}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          background: 'var(--color-surface)',
          border: `1px solid ${focused ? 'var(--color-primary-border)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '8px 10px', fontSize: '11px',
          color: 'var(--color-text)', outline: 'none',
          fontFamily: 'var(--font-sans)',
          lineHeight: 1.6, resize: 'vertical', maxHeight: '200px',
        }}
      />
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
        {PLACEHOLDERS.map(({ tag, desc }) => (
          <span
            key={tag}
            title={desc}
            style={{
              fontFamily: 'monospace', fontSize: '9px',
              background: 'var(--color-surface-elevated)',
              border: '1px solid var(--color-border)',
              borderRadius: '3px', padding: '2px 6px',
              color: 'var(--color-text-secondary)',
              cursor: 'default', userSelect: 'none',
            }}
          >
            {tag}
          </span>
        ))}
      </div>
    </div>
  )
}

function SingleToggle({ label, checked, onChange }: {
  label: string; checked: boolean; onChange: (v: boolean) => void
}) {
  return (
    <div
      onClick={() => onChange(!checked)}
      style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: '9px 12px',
        cursor: 'pointer',
      }}
    >
      <span style={{ fontSize: '12px', color: 'var(--color-text)' }}>{label}</span>
      <div style={{
        width: '32px', height: '18px', borderRadius: '9px',
        background: checked ? 'var(--color-primary)' : 'var(--color-border)',
        position: 'relative', transition: 'background 0.15s', flexShrink: 0,
      }}>
        <div style={{
          position: 'absolute', top: '3px',
          left: checked ? '17px' : '3px',
          width: '12px', height: '12px', borderRadius: '50%',
          background: 'white', transition: 'left 0.15s',
        }} />
      </div>
    </div>
  )
}

function SegmentedControl({ label, options, value, onChange }: {
  label: string
  options: { value: string; label: string }[]
  value: string
  onChange: (v: string) => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        {label}
      </label>
      <div style={{ display: 'flex', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
        {options.map((opt, i) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            style={{
              flex: 1,
              padding: '8px 10px',
              border: 'none',
              borderLeft: i > 0 ? '1px solid var(--color-border)' : 'none',
              background: value === opt.value ? 'var(--color-primary)' : 'transparent',
              color: value === opt.value ? 'white' : 'var(--color-text-secondary)',
              fontSize: '11px',
              fontWeight: value === opt.value ? 600 : 400,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              transition: 'background 0.15s, color 0.15s',
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function Field({ label, value, onChange, placeholder }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string
}) {
  const [focused, setFocused] = useState(false)
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
      <label style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
        {label}
      </label>
      <input type="text" value={value} placeholder={placeholder}
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
