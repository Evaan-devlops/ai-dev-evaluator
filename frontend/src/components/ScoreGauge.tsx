import React from 'react'
import styles from './ScoreGauge.module.css'

interface Props {
  score: number
  max: number
}

function getGaugeColor(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return '#39B56A'
  if (pct >= 0.65) return '#4C7DFF'
  if (pct >= 0.40) return '#F59E0B'
  return '#EF4444'
}

function getLabel(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return 'Excellent'
  if (pct >= 0.65) return 'Good'
  if (pct >= 0.40) return 'Fair'
  return 'Poor'
}

export function ScoreGauge({ score, max }: Props): React.ReactElement {
  const color = getGaugeColor(score, max)
  const label = getLabel(score, max)
  const pct = score / max

  // Gauge: 240-degree arc from 150° to 390°
  const R = 38
  const cx = 56
  const cy = 52
  const startAngle = 150
  const endAngle = 390
  const totalArc = endAngle - startAngle

  const toRad = (deg: number) => (deg * Math.PI) / 180
  const arcStart = {
    x: cx + R * Math.cos(toRad(startAngle)),
    y: cy + R * Math.sin(toRad(startAngle)),
  }

  const fillEnd = startAngle + totalArc * pct
  const arcEnd = {
    x: cx + R * Math.cos(toRad(fillEnd)),
    y: cy + R * Math.sin(toRad(fillEnd)),
  }
  const fullEnd = {
    x: cx + R * Math.cos(toRad(endAngle)),
    y: cy + R * Math.sin(toRad(endAngle)),
  }

  const largeArc = totalArc * pct > 180 ? 1 : 0
  const fullLargeArc = totalArc > 180 ? 1 : 0

  const trackPath = `M ${arcStart.x} ${arcStart.y} A ${R} ${R} 0 ${fullLargeArc} 1 ${fullEnd.x} ${fullEnd.y}`
  const fillPath = pct > 0
    ? `M ${arcStart.x} ${arcStart.y} A ${R} ${R} 0 ${largeArc} 1 ${arcEnd.x} ${arcEnd.y}`
    : ''

  return (
    <div className={styles.container}>
      <svg width={112} height={80} className={styles.svg} viewBox="0 0 112 80">
        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="#E7EAF3"
          strokeWidth={7}
          strokeLinecap="round"
        />
        {/* Fill */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={color}
            strokeWidth={7}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 600ms ease' }}
          />
        )}
        {/* Score text */}
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          dominantBaseline="middle"
          className={styles.scoreText}
          fill={color}
        >
          {score}
        </text>
        <text
          x={cx}
          y={cy + 12}
          textAnchor="middle"
          dominantBaseline="middle"
          className={styles.denomText}
        >
          /{max}
        </text>
        {/* Label */}
        <text
          x={cx}
          y={70}
          textAnchor="middle"
          dominantBaseline="middle"
          className={styles.labelText}
          fill={color}
        >
          {label}
        </text>
      </svg>
    </div>
  )
}
