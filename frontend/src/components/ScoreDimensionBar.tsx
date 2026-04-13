import React from 'react'
import styles from './ScoreDimensionBar.module.css'

interface Props {
  label: string
  score: number
  max?: number
  color?: string
}

function getBarColor(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return '#39B56A'
  if (pct >= 0.65) return '#4C7DFF'
  if (pct >= 0.40) return '#F59E0B'
  return '#EF4444'
}

export function ScoreDimensionBar({ label, score, max = 5, color }: Props): React.ReactElement {
  const pct = Math.min(100, (score / max) * 100)
  const barColor = color ?? getBarColor(score, max)

  return (
    <div className={styles.row}>
      <span className={styles.label}>{label}</span>
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <span className={styles.score} style={{ color: barColor }}>
        {score}/{max}
      </span>
    </div>
  )
}
