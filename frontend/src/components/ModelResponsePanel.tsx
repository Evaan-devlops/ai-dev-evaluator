import React from 'react'
import type { RunResult } from '../types'
import styles from './ModelResponsePanel.module.css'

interface Props {
  result: RunResult
  expanded?: boolean
  collapsed?: boolean
  onToggleCollapsed?: () => void
}

function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function ModelResponsePanel({
  result,
  expanded,
  collapsed,
  onToggleCollapsed,
}: Props): React.ReactElement {
  return (
    <div className={`${styles.card}${expanded && !collapsed ? ` ${styles.cardExpanded}` : ''}${collapsed ? ` ${styles.cardCollapsed}` : ''}`}>
      <div
        className={styles.cardHeader}
        onClick={onToggleCollapsed}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onToggleCollapsed?.()
          }
        }}
        aria-expanded={!collapsed}
      >
        <span className={styles.cardTitle}>Model Response</span>
        <div className={styles.headerRight}>
          <span className={styles.metaChip}>
            {result.provider} / {formatLatency(result.latency_ms)}
          </span>
          <span className={styles.chevron} aria-hidden>
            {collapsed ? '>' : 'v'}
          </span>
        </div>
      </div>
      {!collapsed && (
        <div className={`${styles.responseBody}${expanded ? ` ${styles.responseBodyExpanded}` : ''}`}>
          <pre className={styles.responseText}>{result.llm_response}</pre>
        </div>
      )}
    </div>
  )
}
