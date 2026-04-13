import React from 'react'
import type { ContextLayer } from '../types'
import styles from './TokenBudgetBar.module.css'

interface Props {
  layers: ContextLayer[]
  perLayerTokens: Record<string, number>
  totalTokens: number
  tokenBudgetMax: number
}

const LAYER_COLORS: Record<string, string> = {
  system:    '#67C587',
  user:      '#5B8DEF',
  history:   '#8B7CFF',
  knowledge: '#58C4DD',
  tools:     '#F5B14C',
  state:     '#E88AC6',
}

function formatK(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return String(n)
}

const LAYER_LABELS: Record<string, string> = {
  system:    'System Instructions',
  user:      'User Input',
  history:   'Conversation History',
  knowledge: 'Retrieved Knowledge',
  tools:     'Tool Definitions',
  state:     'State & Memory',
}

export function TokenBudgetBar({
  layers,
  perLayerTokens,
  totalTokens,
  tokenBudgetMax,
}: Props): React.ReactElement {
  const enabledLayers = layers.filter((l) => l.enabled)
  const isOver = totalTokens > tokenBudgetMax
  const usedPct = Math.min(100, (totalTokens / tokenBudgetMax) * 100)

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.cardTitle}>Token Budget</span>
        <span className={`${styles.budgetMeta}${isOver ? ` ${styles.over}` : ''}`}>
          {formatK(totalTokens)}/{formatK(tokenBudgetMax)} · {usedPct.toFixed(1)}% used
        </span>
      </div>

      {/* Segmented bar */}
      <div className={styles.barTrack}>
        {enabledLayers.map((layer) => {
          const tokens = perLayerTokens[layer.id] ?? 0
          const pct = (tokens / tokenBudgetMax) * 100
          return (
            <div
              key={layer.id}
              className={styles.segment}
              style={{
                width: `${pct}%`,
                background: LAYER_COLORS[layer.id] ?? '#888',
              }}
              title={`${layer.title}: ${tokens} tokens`}
            />
          )
        })}
      </div>

      {/* Legend */}
      {enabledLayers.length > 0 && (
        <div className={styles.legend}>
          {enabledLayers.map((layer) => {
            const tokens = perLayerTokens[layer.id] ?? 0
            return (
              <div key={layer.id} className={styles.legendItem}>
                <span
                  className={styles.legendDot}
                  style={{ background: LAYER_COLORS[layer.id] ?? '#888' }}
                />
                <span className={styles.legendLabel}>{LAYER_LABELS[layer.id] ?? layer.title}</span>
                <span className={styles.legendTokens}>~{tokens}</span>
              </div>
            )
          })}
        </div>
      )}

      {isOver && (
        <div className={styles.footer}>
          <span className={styles.overBudget}>⚠ Over budget!</span>
        </div>
      )}
    </div>
  )
}
