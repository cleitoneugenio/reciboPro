import { applyTemplate, DEFAULT_TEMPLATE, formatarData, valorPorExtenso } from '@shared/utils'
import type { Worker, CompanyConfig } from '@shared/types'

interface Props {
  worker: Worker
  company: CompanyConfig
  date?: Date
  template?: string
  title?: string
}

export default function ReceiptPreview({ worker, company, date = new Date(), template, title }: Props) {
  const addressLine = [company.address, company.city].filter(Boolean).join(' — ')
  const body = applyTemplate(template || DEFAULT_TEMPLATE, worker, company, date).replace(/\s+/g, ' ').trim()

  const showName    = company.headerShowName    !== false
  const showCnpj    = company.headerShowCnpj    !== false
  const showAddress = company.headerShowAddress !== false
  const hasHeader   = showName || showCnpj || showAddress

  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      border: '0.5px solid #d0d0d0',
      fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      fontSize: '9px', color: '#111', overflow: 'hidden',
    }}>
      {hasHeader && (
        <div style={{ padding: '10px 12px 8px' }}>
          {showName && (
            <div style={{ fontWeight: 700, fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.03em' }}>
              {company.name}
            </div>
          )}
          {showCnpj && (
            <div style={{ color: '#666', fontSize: '7.5px', marginTop: showName ? '3px' : '0' }}>CNPJ: {company.cnpj}</div>
          )}
          {showAddress && (
            <div style={{ color: '#666', fontSize: '7.5px', marginTop: (showName || showCnpj) ? '1px' : '0' }}>{addressLine}</div>
          )}
        </div>
      )}

      {hasHeader && <Divider />}

      {/* Título — centralizado ou com valor inline */}
      {company.highlightValue && company.highlightValuePosition === 'title' ? (
        <div style={{ padding: '6px 12px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <span style={{ fontWeight: 700, fontSize: `${company.highlightValueSize ?? 8}px`, letterSpacing: '0.06em' }}>
            {(title || 'RECIBO DE PRESTAÇÃO DE SERVIÇO').toUpperCase()}
          </span>
          <span style={{ fontSize: `${company.highlightValueSize ?? 8}px`, fontWeight: 700, color: '#111', flexShrink: 0, marginLeft: '8px' }}>
            {worker.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </span>
        </div>
      ) : (
        <div style={{ padding: '6px 12px', textAlign: 'center', fontWeight: 700, fontSize: '8px', letterSpacing: '0.06em' }}>
          {(title || 'RECIBO DE PRESTAÇÃO DE SERVIÇO').toUpperCase()}
        </div>
      )}

      <Divider />

      {/* Caixa de valor em destaque (posição 'box') */}
      {company.highlightValue && company.highlightValuePosition !== 'title' && (
        <div style={{ margin: '8px 12px 0', padding: '7px 10px', background: '#f5f5f5', borderRadius: '3px', border: '0.5px solid #e0e0e0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '7px', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#888' }}>Valor</span>
          <span style={{ fontSize: `${company.highlightValueSize ?? 12}px`, fontWeight: 700, color: '#111' }}>
            {worker.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </span>
        </div>
      )}

      {/* Corpo */}
      {company.highlightValue
        ? <HighlightedBody body={body} valueStr={valorPorExtenso(worker.total)} />
        : <div style={{ padding: '12px 12px 0', fontSize: '9px', lineHeight: 1.65, textAlign: 'justify' }}>{body}</div>
      }

      <div style={{ padding: '7px 12px 0', fontSize: '8px', color: '#555' }}>
        {company.city}, {formatarData(date)}.
      </div>

      <div style={{ marginTop: 'auto', paddingTop: `${(company.signatureSpacing ?? 44) * 0.77}px`, paddingBottom: '14px', paddingLeft: '12px', paddingRight: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{ width: '54%', borderTop: '0.5px solid #333', marginBottom: '6px' }} />
        <div style={{ fontSize: '8px' }}>{worker.name}</div>
      </div>
    </div>
  )
}

function HighlightedBody({ body, valueStr }: { body: string; valueStr: string }) {
  const idx = body.indexOf(valueStr)
  const style = { padding: '12px 12px 0', fontSize: '9px', lineHeight: 1.65, textAlign: 'justify' } as const
  if (idx === -1) return <div style={style}>{body}</div>
  return (
    <div style={style}>
      {body.slice(0, idx)}
      <span style={{ fontWeight: 700 }}>{valueStr}</span>
      {body.slice(idx + valueStr.length)}
    </div>
  )
}

function Divider() {
  return <div style={{ height: '0.5px', background: '#d0d0d0', flexShrink: 0 }} />
}
