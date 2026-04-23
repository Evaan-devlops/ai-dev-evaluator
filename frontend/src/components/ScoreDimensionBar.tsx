import React from 'react'
import styles from './ScoreDimensionBar.module.css'

interface Props {
  label: string
  score: number
  max?: number
  color?: string
  title?: string
}

function getBarColor(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return '#22C55E'
  if (pct >= 0.65) return '#3B82F6'
  if (pct >= 0.40) return '#F59E0B'
  return '#F43F5E'
}

function getBarGradient(color: string): string {
  return `linear-gradient(90deg, ${color} 0%, color-mix(in srgb, ${color} 72%, white) 100%)`
}

export function ScoreDimensionBar({ label, score, max = 5, color, title }: Props): React.ReactElement {
  const pct = Math.min(100, (score / max) * 100)
  const barColor = color ?? getBarColor(score, max)

  return (
    <div className={styles.row} title={title}>
      <span className={styles.label}>{label}</span>
      <div className={styles.barTrack}>
        <div
          className={styles.barFill}
          style={{ width: `${pct}%`, background: getBarGradient(barColor), ['--bar-color' as string]: barColor }}
        />
      </div>
      <span className={styles.score} style={{ color: barColor }}>
        {score}/{max}
      </span>
    </div>
  )
}
