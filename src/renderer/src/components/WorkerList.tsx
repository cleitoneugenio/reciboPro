import { useState } from 'react'
import type { Worker } from '@shared/types'

interface Props {
  workers: Worker[]
  selected: Set<number>
  onToggle: (id: number) => void
  onSelectAll: (ids: number[]) => void
  onDeselectAll: (ids: number[]) => void
}

export default function WorkerList({ workers, selected, onToggle, onSelectAll, onDeselectAll }: Props) {
  const [search, setSearch] = useState('')

  const visible = search.trim()
    ? workers.filter((w) => w.name.toLowerCase().includes(search.trim().toLowerCase()))
    : workers

  const allVisibleSelected = visible.length > 0 && visible.every((w) => selected.has(w.id))
  const someVisibleSelected = visible.some((w) => selected.has(w.id)) && !allVisibleSelected

  const total = workers
    .filter((w) => selected.has(w.id))
    .reduce((sum, w) => sum + w.total, 0)

  function handleToggleVisible() {
    if (allVisibleSelected) {
      onDeselectAll(visible.map((w) => w.id))
    } else {
      onSelectAll(visible.map((w) => w.id))
    }
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden" style={{ minHeight: 0 }}>
      {/* Search */}
      <div style={{ flexShrink: 0, position: 'relative', marginBottom: '8px' }}>
        <svg
          width="13" height="13" viewBox="0 0 13 13" fill="none"
          stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
          style={{ position: 'absolute', left: '9px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)', pointerEvents: 'none' }}
        >
          <circle cx="5.5" cy="5.5" r="4" />
          <line x1="8.5" y1="8.5" x2="12" y2="12" />
        </svg>
        <input
          type="text"
          placeholder="Filtrar funcionários..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '7px 28px 7px 28px',
            fontSize: '11px',
            color: 'var(--color-text)',
            outline: 'none',
            fontFamily: 'var(--font-sans)',
            boxSizing: 'border-box',
          }}
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            style={{
              position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--color-text-muted)', fontSize: '15px', lineHeight: 1,
              display: 'flex', alignItems: 'center', padding: 0,
            }}
          >
            ×
          </button>
        )}
      </div>

      {/* Summary bar */}
      <div
        className="flex shrink-0 items-center justify-between px-3 py-2"
        style={{
          background: 'var(--color-deep)',
          borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
          border: '1px solid var(--color-border)',
          borderBottom: 'none',
        }}
      >
        <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>
          {selected.size} selecionados{search && visible.length !== workers.length ? ` · ${visible.length} visíveis` : ''}
        </span>
        <span style={{ color: 'var(--color-accent)', fontSize: '11px', fontWeight: 600 }}>
          {total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
        </span>
      </div>

      {/* Header */}
      <div
        className="flex shrink-0 cursor-pointer items-center gap-3 px-3 py-2"
        style={{
          background: 'var(--color-surface-elevated)',
          border: '1px solid var(--color-border)',
          borderBottom: '1px solid var(--color-border-subtle)',
        }}
        onClick={handleToggleVisible}
      >
        <Checkbox checked={allVisibleSelected} indeterminate={someVisibleSelected} />
        <span style={{ flex: 1, fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
          Funcionário
        </span>
        <span style={{ fontSize: '10px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
          Total
        </span>
      </div>

      {/* Rows */}
      <div
        className="flex-1 overflow-y-auto"
        style={{ border: '1px solid var(--color-border)', borderTop: 'none', borderRadius: '0 0 var(--radius-md) var(--radius-md)' }}
      >
        {visible.map((worker, i) => {
          const checked = selected.has(worker.id)
          return (
            <label
              key={worker.id}
              className="flex cursor-pointer items-center gap-3 px-3 py-2.5"
              style={{
                background: checked ? 'rgba(34,197,94,0.04)' : 'var(--color-surface)',
                borderBottom: i < visible.length - 1 ? '1px solid var(--color-border-subtle)' : 'none',
                borderLeft: checked ? '2px solid var(--color-accent)' : '2px solid transparent',
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-hover)' }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = checked ? 'rgba(34,197,94,0.04)' : 'var(--color-surface)' }}
            >
              <Checkbox checked={checked} onChange={() => onToggle(worker.id)} />
              <span style={{ flex: 1, fontSize: '12px', color: checked ? 'var(--color-text)' : 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {worker.name}
              </span>
              <span style={{ fontSize: '11px', fontWeight: checked ? 600 : 400, color: checked ? 'var(--color-accent)' : 'var(--color-text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                {worker.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </label>
          )
        })}
        {visible.length === 0 && (
          <div style={{ padding: '20px', textAlign: 'center', fontSize: '11px', color: 'var(--color-text-muted)' }}>
            Nenhum resultado para &ldquo;{search}&rdquo;
          </div>
        )}
      </div>

      {/* Quick actions */}
      <div className="flex shrink-0 gap-4 pt-2">
        <button
          onClick={() => onSelectAll(visible.map((w) => w.id))}
          style={{ fontSize: '11px', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--color-accent)' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--color-text-muted)' }}
        >
          Selecionar todos
        </button>
        <button
          onClick={() => onDeselectAll(visible.map((w) => w.id))}
          style={{ fontSize: '11px', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
          onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--color-primary-mid)' }}
          onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = 'var(--color-text-muted)' }}
        >
          Desmarcar todos
        </button>
      </div>
    </div>
  )
}

function Checkbox({ checked, indeterminate, onChange }: {
  checked: boolean
  indeterminate?: boolean
  onChange?: () => void
}) {
  return (
    <span
      role="checkbox"
      aria-checked={indeterminate ? 'mixed' : checked}
      onClick={(e) => { e.stopPropagation(); onChange?.() }}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '15px',
        height: '15px',
        borderRadius: '3px',
        border: `1px solid ${checked || indeterminate ? 'var(--color-accent)' : 'var(--color-border-strong)'}`,
        background: checked || indeterminate ? 'var(--color-accent)' : 'transparent',
        flexShrink: 0,
        cursor: 'pointer',
      }}
    >
      {indeterminate ? (
        <span style={{ display: 'block', width: '8px', height: '1.5px', background: 'white', borderRadius: '1px' }} />
      ) : checked ? (
        <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
          <path d="M1 3.5L3.2 5.5L8 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : null}
    </span>
  )
}
