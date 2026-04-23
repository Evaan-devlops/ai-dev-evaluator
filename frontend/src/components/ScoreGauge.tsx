import React from 'react'
import styles from './ScoreGauge.module.css'

interface Props {
  score: number
  max: number
}

function getGaugeColor(score: number, max: number): string {
  const pct = score / max
  if (pct >= 0.85) return '#22C55E'
  if (pct >= 0.65) return '#3B82F6'
  if (pct >= 0.40) return '#F59E0B'
  return '#F43F5E'
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
        <defs>
          <filter id="scoreGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="5" stdDeviation="5" floodColor={color} floodOpacity="0.28" />
          </filter>
        </defs>
        {/* Track */}
        <path
          d={trackPath}
          fill="none"
          stroke="rgba(255,255,255,0.58)"
          strokeWidth={9}
          strokeLinecap="round"
        />
        {/* Fill */}
        {fillPath && (
          <path
            d={fillPath}
            fill="none"
            stroke={color}
            strokeWidth={9}
            strokeLinecap="round"
            filter="url(#scoreGlow)"
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
