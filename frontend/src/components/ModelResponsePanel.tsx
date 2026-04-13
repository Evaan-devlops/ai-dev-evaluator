import React from 'react'
import type { RunResult } from '../types'
import styles from './ModelResponsePanel.module.css'

interface Props {
  result: RunResult
  expanded?: boolean
}

function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

export function ModelResponsePanel({ result, expanded }: Props): React.ReactElement {
  return (
    <div className={`${styles.card}${expanded ? ` ${styles.cardExpanded}` : ''}`}>
      <div className={styles.cardHeader}>
        <span className={styles.cardTitle}>Model Response</span>
        <span className={styles.metaChip}>
          {result.provider} · {formatLatency(result.latency_ms)}
        </span>
      </div>
      <div className={`${styles.responseBody}${expanded ? ` ${styles.responseBodyExpanded}` : ''}`}>
        <pre className={styles.responseText}>{result.llm_response}</pre>
      </div>
    </div>
  )
}
