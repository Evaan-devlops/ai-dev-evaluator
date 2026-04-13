import React from 'react'
import type { RunHistoryItem } from '../types'
import { ActiveLayerBadges } from './ActiveLayerBadges'
import styles from './RunHistoryTable.module.css'

interface Props {
  runHistory: RunHistoryItem[]
  selectedRunId: number | null
  onSelectRun: (runId: number) => void
}

function scoreColor(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return '#39B56A'
  if (pct >= 0.65) return '#4C7DFF'
  if (pct >= 0.40) return '#F59E0B'
  return '#EF4444'
}

export function RunHistoryTable({ runHistory, selectedRunId, onSelectRun }: Props): React.ReactElement {
  if (runHistory.length === 0) {
    return (
      <div className={styles.empty}>
        <div className={styles.emptyIcon}>📋</div>
        <p className={styles.emptyText}>
          No runs yet. Configure layers and click Run to get started.
        </p>
      </div>
    )
  }

  const sorted = [...runHistory].reverse()

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>#</th>
            <th>Active Layers</th>
            <th>Score</th>
            <th>Tokens</th>
            <th>Latency</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((item) => (
            <tr
              key={item.run_id}
              className={`${styles.row}${selectedRunId === item.run_id ? ` ${styles.selected}` : ''}`}
              onClick={() => onSelectRun(item.run_id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onSelectRun(item.run_id)}
            >
              <td className={styles.runNum}>#{item.run_number}</td>
              <td className={styles.layersCell}>
                <ActiveLayerBadges activeLayers={item.active_layers} size="sm" />
              </td>
              <td className={styles.scoreCell}>
                <span style={{ color: scoreColor(item.quality_score, item.score_max) }}>
                  {item.quality_score}/{item.score_max}
                </span>
              </td>
              <td className={styles.metaCell}>{item.total_tokens.toLocaleString()}</td>
              <td className={styles.metaCell}>{item.latency_ms}ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
