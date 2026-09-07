import { useState, useCallback, useEffect } from 'react'
import type { CompanyConfig, Worker } from '@shared/types'
import WorkerList from '../components/WorkerList'
import ReceiptPreview from '../components/ReceiptPreview'

type Status = 'idle' | 'loading' | 'ready' | 'generating' | 'done' | 'error'

const MESES_PT = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']

function todayValue(): string {
  return new Date().toISOString().split('T')[0]!
}

function parseDate(value: string): Date {
  return new Date(value + 'T12:00:00')
}

interface Props {
  company: CompanyConfig
  onOpenSettings: () => void
}

export default function Main({ company, onOpenSettings }: Props) {
  const [filePath, setFilePath] = useState<string | null>(null)
  const [sheets, setSheets] = useState<string[]>([])
  const [activeSheet, setActiveSheet] = useState<string | null>(null)
  const [workers, setWorkers] = useState<Worker[]>([])
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [status, setStatus] = useState<Status>('idle')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [lastPdf, setLastPdf] = useState<string | null>(null)
  const [pageIndex, setPageIndex] = useState(0)
  const [receiptsPerPage, setReceiptsPerPage] = useState(2)
  const [receiptDate, setReceiptDate] = useState(todayValue)
  const [recentFiles, setRecentFiles] = useState<string[]>([])
  const [showAbout, setShowAbout] = useState(false)
  const [appVersion, setAppVersion] = useState('')

  const date = parseDate(receiptDate)
  const selectedWorkers = workers.filter((w) => selected.has(w.id))
  const pageCount = Math.ceil(selectedWorkers.length / receiptsPerPage) || 0
  const pageWorkers = selectedWorkers.slice(pageIndex * receiptsPerPage, (pageIndex + 1) * receiptsPerPage)

  useEffect(() => { setPageIndex(0) }, [receiptsPerPage])

  useEffect(() => {
    if (pageCount > 0 && pageIndex >= pageCount) setPageIndex(pageCount - 1)
  }, [pageCount, pageIndex])

  useEffect(() => {
    void window.api.recent.get().then((res) => {
      if (res.success) setRecentFiles(res.data)
    })
    void window.api.app.getVersion().then((res) => {
      if (res.success) setAppVersion(res.data)
    })
  }, [])

  async function loadFile(path: string) {
    setStatus('loading')
    setErrorMsg(null)
    const sheetsRes = await window.api.excel.readSheets(path)
    if (!sheetsRes.success) { setStatus('error'); setErrorMsg(sheetsRes.error); return }
    const first = sheetsRes.data[0] ?? null
    if (!first) { setStatus('error'); setErrorMsg('Planilha sem abas ou arquivo inválido'); return }
    setFilePath(path)
    setSheets(sheetsRes.data)
    setActiveSheet(first)
    setPageIndex(0)
    void window.api.recent.add(path).then(() =>
      window.api.recent.get().then((res) => { if (res.success) setRecentFiles(res.data) })
    )
    await loadWorkers(path, first)
  }

  async function loadWorkers(path: string, sheet: string) {
    setStatus('loading')
    const res = await window.api.excel.readWorkers(path, sheet)
    if (!res.success) { setStatus('error'); setErrorMsg(res.error); return }
    setWorkers(res.data)
    setSelected(new Set(res.data.map((w) => w.id)))
    setPageIndex(0)
    setStatus('ready')
  }

  async function openFile() {
    const res = await window.api.dialog.openXlsx()
    if (!res.success || !res.data) return
    await loadFile(res.data)
  }

  async function loadSample() {
    const res = await window.api.excel.samplePath()
    if (!res.success || !res.data) return
    await loadFile(res.data)
  }

  async function generate() {
    const toGenerate = workers.filter((w) => selected.has(w.id))
    if (toGenerate.length === 0) return
    const month = MESES_PT[date.getMonth()]
    const suggestedName = `recibos_${month}_${date.getFullYear()}.pdf`
    const saveRes = await window.api.dialog.savePdf(suggestedName)
    if (!saveRes.success || !saveRes.data) return
    setStatus('generating')
    const res = await window.api.pdf.generate({ workers: toGenerate, outputPath: saveRes.data, company, receiptsPerPage, date })
    if (!res.success) { setStatus('error'); setErrorMsg(res.error); return }
    setLastPdf(saveRes.data)
    setStatus('done')
  }

  const extractPath = useCallback((e: React.DragEvent): string | null => {
    e.preventDefault()
    e.stopPropagation()
    const file = e.dataTransfer.files[0]
    if (!file) return null
    return window.api.getPathForFile(file)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    const path = extractPath(e)
    if (path) void loadFile(path)
  }, [extractPath])

  // Prevent Electron from navigating to the dropped file at document level
  useEffect(() => {
    const prevent = (e: DragEvent) => { e.preventDefault(); e.stopPropagation() }
    document.addEventListener('dragover', prevent)
    document.addEventListener('drop', prevent)
    return () => {
      document.removeEventListener('dragover', prevent)
      document.removeEventListener('drop', prevent)
    }
  }, [])

  const [panelOver, setPanelOver] = useState(false)

  const handlePanelDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.dataTransfer.types.includes('Files')) setPanelOver(true)
  }, [])

  const handlePanelDragLeave = useCallback((e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setPanelOver(false)
  }, [])

  const handlePanelDrop = useCallback((e: React.DragEvent) => {
    setPanelOver(false)
    const path = extractPath(e)
    if (path) void loadFile(path)
  }, [extractPath])

  const fileName = filePath?.split(/[/\\]/).pop() ?? null
  const hasContent = status === 'ready' || status === 'generating' || status === 'done' || status === 'error'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--color-bg)' }}>

      {showAbout && <AboutModal version={appVersion} onClose={() => setShowAbout(false)} />}

      {/* Titlebar */}
      <div
        style={{
          height: '40px', display: 'flex', alignItems: 'center',
          paddingLeft: '16px', paddingRight: '12px', flexShrink: 0,
          background: 'var(--color-deep)', WebkitAppRegion: 'drag',
        } as React.CSSProperties}
      >
        <Wordmark />
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setShowAbout(true)}
          style={{
            WebkitAppRegion: 'no-drag',
            width: '24px', height: '24px',
            borderRadius: '50%', border: '1px solid rgba(255,255,255,0.12)',
            background: 'transparent', color: 'rgba(255,255,255,0.35)',
            cursor: 'pointer', fontSize: '12px', fontWeight: 600,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: 'var(--font-sans)', transition: 'color 150ms, border-color 150ms',
          } as React.CSSProperties}
          onMouseEnter={(e) => { const b = e.currentTarget; b.style.color = 'rgba(255,255,255,0.7)'; b.style.borderColor = 'rgba(255,255,255,0.3)' }}
          onMouseLeave={(e) => { const b = e.currentTarget; b.style.color = 'rgba(255,255,255,0.35)'; b.style.borderColor = 'rgba(255,255,255,0.12)' }}
          title="Sobre o ReciboPro"
        >
          i
        </button>
      </div>

      {/* Tab bar */}
      <div style={{
        height: '38px', flexShrink: 0,
        display: 'flex', alignItems: 'stretch',
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--color-deep)',
        paddingLeft: '4px',
      }}>
        <TabBtn active>Principal</TabBtn>
        <TabBtn active={false} onClick={onOpenSettings}>Configurações</TabBtn>
      </div>

      {/* Layout duas colunas */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ── Painel esquerdo ──────────────────────────── */}
        <div
          onDragOver={handlePanelDragOver}
          onDragLeave={handlePanelDragLeave}
          onDrop={handlePanelDrop}
          style={{
            width: '300px', minWidth: '300px',
            display: 'flex', flexDirection: 'column',
            padding: '16px', gap: '12px',
            borderRight: `1px solid ${panelOver ? 'var(--color-accent-border)' : 'var(--color-border)'}`,
            background: panelOver ? 'var(--color-accent-muted)' : 'var(--color-bg)',
            overflow: 'hidden',
            transition: 'background 120ms ease, border-color 120ms ease',
          }}>

          {/* Planilha */}
          <div>
            <FieldLabel>Planilha</FieldLabel>
            {status === 'idle'
              ? (
                <>
                  <Dropzone onOpenFile={() => void openFile()} onDrop={handleDrop} />
                  <button type="button" onClick={() => void loadSample()}
                    style={{
                      marginTop: '8px', width: '100%', padding: '6px',
                      background: 'none', border: 'none',
                      fontSize: '11px', fontFamily: 'var(--font-sans)',
                      color: 'var(--color-text-muted)', cursor: 'pointer',
                    }}
                  >
                    ou{' '}
                    <span style={{ color: 'var(--color-accent)', fontWeight: 600 }}>
                      carregar exemplo
                    </span>
                  </button>
                </>
              )
              : <FileChip fileName={fileName} onChangeFile={() => void openFile()} />
            }
          </div>

          {/* Aba */}
          {sheets.length > 1 && (
            <div>
              <FieldLabel>Aba</FieldLabel>
              <select
                value={activeSheet ?? ''}
                onChange={(e) => {
                  const sheet = e.target.value
                  setActiveSheet(sheet)
                  if (filePath) void loadWorkers(filePath, sheet)
                }}
                style={{
                  width: '100%', background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '7px 10px', fontSize: '11px',
                  color: 'var(--color-text)', outline: 'none', cursor: 'pointer',
                }}
              >
                {sheets.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}

          {/* Data do recibo */}
          <div>
            <FieldLabel>Data do recibo</FieldLabel>
            <input
              type="date"
              value={receiptDate}
              onChange={(e) => setReceiptDate(e.target.value || todayValue())}
              style={{
                width: '100%', background: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '7px 10px', fontSize: '12px',
                color: 'var(--color-text)', outline: 'none',
                colorScheme: 'dark', fontFamily: 'var(--font-sans)',
                boxSizing: 'border-box',
              } as React.CSSProperties}
            />
          </div>

          {/* Loading */}
          {status === 'loading' && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
              <Spinner />
              <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Lendo planilha...
              </span>
            </div>
          )}

          {/* Lista de funcionários */}
          {hasContent && workers.length > 0 && (
            <WorkerList
              workers={workers}
              selected={selected}
              onToggle={(id) => {
                setSelected((prev) => {
                  const next = new Set(prev)
                  next.has(id) ? next.delete(id) : next.add(id)
                  return next
                })
              }}
              onSelectAll={(ids) => setSelected((prev) => new Set([...prev, ...ids]))}
              onDeselectAll={(ids) => setSelected((prev) => {
                const next = new Set(prev)
                ids.forEach((id) => next.delete(id))
                return next
              })}
            />
          )}

          {/* Error */}
          {status === 'error' && errorMsg && (
            <div style={{ borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: '11px', color: 'var(--color-error)', background: 'var(--color-error-muted)' }}>
              {errorMsg}
            </div>
          )}

          {/* Sucesso */}
          {status === 'done' && lastPdf && (
            <div style={{ borderRadius: 'var(--radius-md)', padding: '8px 12px', fontSize: '11px', color: 'var(--color-accent)', background: 'var(--color-accent-muted)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', animation: 'slideUp 0.25s ease' }}>
              <span>PDF gerado com sucesso.</span>
              <button onClick={() => void window.api.shell.openPath(lastPdf)}
                style={{ fontSize: '11px', color: 'var(--color-accent)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, fontFamily: 'var(--font-sans)', padding: 0 }}>
                Abrir
              </button>
            </div>
          )}

          {/* CTA */}
          {hasContent && workers.length > 0 && (
            <GenBtn
              disabled={selected.size === 0 || status === 'generating'}
              onClick={() => void generate()}
            >
              {status === 'generating' ? 'Gerando...' : 'Gerar Recibos'}
            </GenBtn>
          )}

        </div>

        {/* ── Painel direito — Prévia ───────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--color-deep)', overflow: 'hidden' }}>

          {/* Header da prévia */}
          <div style={{
            height: '40px', flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '0 16px',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
          }}>
            <span style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
              Prévia
            </span>
            {pageCount > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <NavBtn onClick={() => setPageIndex((i) => Math.max(0, i - 1))} disabled={pageIndex === 0}>←</NavBtn>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', minWidth: '52px', textAlign: 'center' }}>
                  {pageIndex + 1} / {pageCount}
                </span>
                <NavBtn onClick={() => setPageIndex((i) => Math.min(pageCount - 1, i + 1))} disabled={pageIndex === pageCount - 1}>→</NavBtn>
              </div>
            )}
          </div>

          {/* Body da prévia */}
          <div style={{ flex: 1, overflow: 'auto', display: 'flex', alignItems: pageWorkers.length > 0 ? 'flex-start' : 'stretch', justifyContent: 'center', padding: pageWorkers.length > 0 ? '28px 24px' : '0' }}>
            {pageWorkers.length > 0
              ? <A4Page workers={pageWorkers} count={receiptsPerPage} company={company} date={date} />
              : <EmptyPreview onOpenFile={() => void openFile()} onOpenRecent={(p) => void loadFile(p)} recentFiles={recentFiles} />
            }
          </div>

          {/* Footer — recibos por folha */}
          <div style={{
            flexShrink: 0,
            borderTop: '1px solid var(--color-border)',
            padding: '10px 16px',
            display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px',
            background: 'var(--color-surface)',
          }}>
            <span style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
              Recibos por folha
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <NavBtn onClick={() => setReceiptsPerPage((n) => Math.max(1, n - 1))} disabled={receiptsPerPage <= 1}>−</NavBtn>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text)', minWidth: '18px', textAlign: 'center', fontFamily: 'var(--font-sans)' }}>
                {receiptsPerPage}
              </span>
              <NavBtn onClick={() => setReceiptsPerPage((n) => n + 1)} disabled={false}>+</NavBtn>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ──────────────────────────────────────────────────────────

function Wordmark() {
  return (
    <span style={{ fontFamily: 'var(--font-sans)', fontSize: '16px', lineHeight: 1, WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
      <span style={{ fontWeight: 300, color: 'white' }}>recibo</span>
      <span style={{ fontWeight: 800, color: '#22C55E' }}>pro</span>
    </span>
  )
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <p style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '6px' }}>
      {children}
    </p>
  )
}

function Dropzone({ onOpenFile, onDrop }: { onOpenFile: () => void; onDrop: (e: React.DragEvent) => void }) {
  const [over, setOver] = useState(false)
  return (
    <button onClick={onOpenFile}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { setOver(false); onDrop(e) }}
      style={{
        width: '100%', minHeight: '72px',
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
        borderRadius: 'var(--radius-md)',
        border: `1px dashed ${over ? 'var(--color-accent-border)' : 'var(--color-border)'}`,
        background: over ? 'var(--color-accent-muted)' : 'var(--color-surface)',
        cursor: 'pointer', padding: '14px',
        fontFamily: 'var(--font-sans)',
        color: over ? 'var(--color-accent)' : 'var(--color-text-muted)',
      }}
    >
      <IconExcel />
      <div style={{ textAlign: 'left' }}>
        <div style={{ fontSize: '11px', fontWeight: 500, color: over ? 'var(--color-accent)' : 'var(--color-text-secondary)' }}>Selecionar planilha</div>
        <div style={{ fontSize: '10px', marginTop: '2px' }}>Arraste ou clique · .xlsx</div>
      </div>
    </button>
  )
}

function FileChip({ fileName, onChangeFile }: { fileName: string | null; onChangeFile: () => void }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '7px 10px' }}>
      <IconExcel />
      <span style={{ flex: 1, fontSize: '11px', color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{fileName}</span>
      <button onClick={onChangeFile}
        style={{ fontSize: '10px', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontFamily: 'var(--font-sans)', flexShrink: 0 }}>
        Trocar
      </button>
    </div>
  )
}

function GenBtn({ children, disabled, onClick }: { children: React.ReactNode; disabled: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        width: '100%', padding: '11px',
        borderRadius: 'var(--radius-md)', border: 'none',
        background: !disabled ? 'var(--color-primary)' : 'var(--color-surface-elevated)',
        color: !disabled ? 'white' : 'var(--color-text-muted)',
        fontSize: '13px', fontWeight: 700,
        cursor: disabled ? 'not-allowed' : 'pointer',
        letterSpacing: '0.03em', fontFamily: 'var(--font-sans)',
        transition: 'filter 150ms ease, background 150ms ease',
      }}
      onMouseEnter={(e) => { if (!disabled) (e.currentTarget as HTMLElement).style.filter = 'brightness(1.12)' }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.filter = '' }}
    >
      {children}
    </button>
  )
}

function NavBtn({ children, onClick, disabled }: { children: React.ReactNode; onClick: () => void; disabled: boolean }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        width: '26px', height: '26px', borderRadius: '6px',
        background: 'var(--color-surface)', border: '1px solid var(--color-border)',
        color: disabled ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
        cursor: disabled ? 'default' : 'pointer', fontSize: '13px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: 'var(--font-sans)',
      }}>
      {children}
    </button>
  )
}

function A4Page({ workers, count, company, date }: { workers: Worker[]; count: number; company: CompanyConfig; date: Date }) {
  const W = 460
  const H = Math.round(W * 1.4142)
  const PAD_V = 24, PAD_H = 28
  const GAP = count > 1 ? 8 : 0
  const slotH = Math.floor((H - PAD_V * 2 - GAP * (count - 1)) / count)

  return (
    <div style={{
      width: `${W}px`, height: `${H}px`,
      background: 'white',
      boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
      borderRadius: '2px',
      padding: `${PAD_V}px ${PAD_H}px`,
      flexShrink: 0,
      display: 'flex', flexDirection: 'column',
      gap: `${GAP}px`,
    }}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} style={{ height: `${slotH}px`, flexShrink: 0, overflow: 'hidden' }}>
          {workers[i] && (
            <ReceiptPreview
              worker={workers[i]}
              company={company}
              date={date}
              title={company.receiptTitle}
              template={company.receiptTemplate}
            />
          )}
        </div>
      ))}
    </div>
  )
}

function EmptyPreview({ onOpenFile, onOpenRecent, recentFiles }: {
  onOpenFile: () => void
  onOpenRecent: (path: string) => void
  recentFiles: string[]
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px', flex: 1, paddingBottom: '40px' }}>
      {/* App icon */}
      <svg width="88" height="88" viewBox="0 0 256 256" fill="none" style={{ flexShrink: 0, filter: 'drop-shadow(0 8px 24px rgba(15,31,77,0.5))' }}>
        <defs>
          <linearGradient id="iconBg" x1="0" y1="0" x2="256" y2="256" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#2563EB" />
            <stop offset="100%" stopColor="#1B4ECC" />
          </linearGradient>
        </defs>
        <rect width="256" height="256" rx="56" fill="url(#iconBg)" />
        <g transform="rotate(-8 128 128)">
          <rect x="72" y="60" width="108" height="130" rx="8" fill="#4A7BE0" />
          <line x1="72" y1="88" x2="180" y2="88" stroke="#6A97E8" strokeWidth="1.5" />
          <line x1="72" y1="108" x2="180" y2="108" stroke="#6A97E8" strokeWidth="1.5" />
          <line x1="72" y1="128" x2="180" y2="128" stroke="#6A97E8" strokeWidth="1.5" />
          <line x1="72" y1="148" x2="180" y2="148" stroke="#6A97E8" strokeWidth="1.5" />
          <line x1="116" y1="68" x2="116" y2="190" stroke="#6A97E8" strokeWidth="1.5" />
          <line x1="148" y1="68" x2="148" y2="190" stroke="#6A97E8" strokeWidth="1.5" />
        </g>
        <rect x="80" y="52" width="104" height="130" rx="8" fill="white" />
        <rect x="80" y="52" width="104" height="26" rx="8" fill="#22C55E" />
        <rect x="80" y="66" width="104" height="12" fill="#22C55E" />
        <text x="132" y="70" textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fontWeight="400" fontSize="10" fill="white">
          recibo<tspan fontWeight="700">pro</tspan>
        </text>
        <rect x="96" y="94" width="72" height="6" rx="3" fill="#8FB3F0" />
        <rect x="96" y="108" width="55" height="6" rx="3" fill="#C0D4F5" />
        <rect x="96" y="122" width="65" height="6" rx="3" fill="#C0D4F5" />
        <rect x="96" y="136" width="45" height="6" rx="3" fill="#D6E5FF" />
        <line x1="96" y1="162" x2="168" y2="162" stroke="#8FB3F0" strokeWidth="1.5" />
        <circle cx="192" cy="128" r="16" fill="#22C55E" />
        <path d="M185 128 L197 128 M192 122 L199 128 L192 134" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>

      {/* Heading */}
      <div style={{ textAlign: 'center' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-0.3px', color: 'var(--color-text)', margin: 0, lineHeight: 1.2 }}>
          Bem-vindo ao recibo<span style={{ color: '#22C55E', fontWeight: 800 }}>pro</span>
        </h2>
        <p style={{ marginTop: '8px', fontSize: '13px', color: 'var(--color-text-muted)', lineHeight: 1.6, maxWidth: '260px' }}>
          Selecione ou arraste sua planilha e gere recibos em segundos.
        </p>
      </div>

      {/* CTA */}
      <button
        onClick={onOpenFile}
        style={{
          padding: '10px 24px',
          borderRadius: 'var(--radius-md)', border: 'none',
          background: 'var(--color-primary)',
          color: 'white', fontSize: '13px', fontWeight: 600,
          cursor: 'pointer', fontFamily: 'var(--font-sans)',
          letterSpacing: '0.01em', transition: 'filter 150ms ease',
        }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.filter = 'brightness(1.12)' }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.filter = '' }}
      >
        Carregar planilha
      </button>

      {/* Recentes */}
      {recentFiles.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%', maxWidth: '260px' }}>
          <span style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '2px' }}>
            Recentes
          </span>
          {recentFiles.map((p) => (
            <button
              key={p}
              onClick={() => onOpenRecent(p)}
              style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                background: 'var(--color-surface)', border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)', padding: '7px 10px',
                cursor: 'pointer', fontFamily: 'var(--font-sans)', width: '100%', textAlign: 'left',
                transition: 'background 120ms ease',
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-hover)' }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--color-surface)' }}
            >
              <IconExcel />
              <span style={{ flex: 1, fontSize: '11px', color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {p.split(/[/\\]/).pop()}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function TabBtn({ children, active, onClick }: { children: React.ReactNode; active: boolean; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '0 16px',
        background: 'none', border: 'none',
        borderBottom: active ? '2px solid var(--color-primary)' : '2px solid transparent',
        color: active ? 'var(--color-text)' : 'var(--color-text-muted)',
        fontSize: '13px', fontWeight: active ? 600 : 400,
        cursor: onClick ? 'pointer' : 'default',
        fontFamily: 'var(--font-sans)',
        transition: 'color 150ms ease, border-color 150ms ease',
        flexShrink: 0,
      }}
      onMouseEnter={(e) => { if (!active && onClick) (e.currentTarget as HTMLElement).style.color = 'var(--color-text-secondary)' }}
      onMouseLeave={(e) => { if (!active) (e.currentTarget as HTMLElement).style.color = 'var(--color-text-muted)' }}
    >
      {children}
    </button>
  )
}

function Spinner() {
  return (
    <div style={{ width: '16px', height: '16px', borderRadius: '50%', border: '2px solid var(--color-border)', borderTopColor: 'var(--color-primary)', animation: 'spin 0.7s linear infinite' }} />
  )
}

function IconExcel() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" style={{ flexShrink: 0, color: 'inherit' }}>
      <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.2" />
      <line x1="2" y1="6" x2="14" y2="6" stroke="currentColor" strokeWidth="1" />
      <line x1="6" y1="6" x2="6" y2="14" stroke="currentColor" strokeWidth="1" />
    </svg>
  )
}

function AboutModal({ version, onClose }: { version: string; onClose: () => void }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        backdropFilter: 'blur(4px)',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: '12px',
          padding: '32px 36px',
          width: '340px',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: '0',
          boxShadow: '0 24px 64px rgba(0,0,0,0.5)',
        }}
      >
        {/* Icon */}
        <svg width="56" height="56" viewBox="0 0 256 256" fill="none" style={{ marginBottom: '16px' }}>
          <defs>
            <linearGradient id="aiBg" x1="0" y1="0" x2="256" y2="256" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#2563EB" />
              <stop offset="100%" stopColor="#1B4ECC" />
            </linearGradient>
          </defs>
          <rect width="256" height="256" rx="56" fill="url(#aiBg)" />
          <rect x="80" y="52" width="104" height="130" rx="8" fill="white" />
          <rect x="80" y="52" width="104" height="26" rx="8" fill="#22C55E" />
          <rect x="80" y="66" width="104" height="12" fill="#22C55E" />
          <text x="132" y="70" textAnchor="middle" fontFamily="Inter, system-ui, sans-serif" fontWeight="400" fontSize="10" fill="white">recibo<tspan fontWeight="700">pro</tspan></text>
          <rect x="96" y="94" width="72" height="6" rx="3" fill="#8FB3F0" />
          <rect x="96" y="108" width="55" height="6" rx="3" fill="#C0D4F5" />
          <rect x="96" y="122" width="65" height="6" rx="3" fill="#C0D4F5" />
          <rect x="96" y="136" width="45" height="6" rx="3" fill="#D6E5FF" />
          <line x1="96" y1="162" x2="168" y2="162" stroke="#8FB3F0" strokeWidth="1.5" />
        </svg>

        {/* Wordmark */}
        <div style={{ fontSize: '22px', fontWeight: 300, color: 'var(--color-text)', letterSpacing: '-0.3px', marginBottom: '4px' }}>
          recibo<span style={{ fontWeight: 800, color: '#22C55E' }}>pro</span>
        </div>

        {version && (
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '20px' }}>
            versão {version}
          </div>
        )}

        <div style={{ width: '100%', height: '1px', background: 'var(--color-border)', marginBottom: '20px' }} />

        <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: 1.65, textAlign: 'center', margin: '0 0 8px' }}>
          Gerador de recibos de prestação de serviço para Windows.
        </p>
        <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', lineHeight: 1.6, textAlign: 'center', margin: '0 0 24px' }}>
          Este aplicativo processa arquivos localmente. Nenhum dado é coletado, transmitido ou armazenado fora do seu computador.
        </p>

        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '24px', textAlign: 'center' }}>
          © 2025 HigherMind
        </div>

        <button
          onClick={onClose}
          style={{
            padding: '9px 28px',
            borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)',
            background: 'var(--color-surface-elevated)',
            color: 'var(--color-text-secondary)',
            fontSize: '12px', fontWeight: 500,
            cursor: 'pointer', fontFamily: 'var(--font-sans)',
            transition: 'background 150ms ease',
          }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-hover)' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-elevated)' }}
        >
          Fechar
        </button>
      </div>
    </div>
  )
}
