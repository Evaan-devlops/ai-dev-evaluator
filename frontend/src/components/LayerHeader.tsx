import React from 'react'
import type { LayerType } from '../types'
import styles from './LayerHeader.module.css'

interface Props {
  id: LayerType
  title: string
  description: string
  enabled: boolean
  tokenCount: number
  layerIndex: number
  alwaysOn?: boolean
  warning?: string
  onToggle: () => void
  onViewContent: () => void
}

const BADGE_COLORS: Record<LayerType, { bg: string; text: string; border: string }> = {
  system:    { bg: 'rgba(103,199,122,0.12)', text: '#2d8a4a', border: 'rgba(103,199,122,0.28)' },
  user:      { bg: 'rgba(111,158,255,0.12)', text: '#2856bc', border: 'rgba(111,158,255,0.28)' },
  history:   { bg: 'rgba(141,121,255,0.12)', text: '#5443c4', border: 'rgba(141,121,255,0.28)' },
  knowledge: { bg: 'rgba(85,199,220,0.12)',  text: '#1b7a92', border: 'rgba(85,199,220,0.28)'  },
  tools:     { bg: 'rgba(241,174,89,0.12)',  text: '#8a5210', border: 'rgba(241,174,89,0.28)'  },
  state:     { bg: 'rgba(229,138,182,0.12)', text: '#8c2e72', border: 'rgba(229,138,182,0.28)' },
}

const LAYER_DOTS: Record<LayerType, string> = {
  system:    '#67c77a',
  user:      '#6f9eff',
  history:   '#8d79ff',
  knowledge: '#55c7dc',
  tools:     '#f1ae59',
  state:     '#e58ab6',
}

export function LayerHeader({
  id,
  title,
  description,
  enabled,
  tokenCount,
  layerIndex,
  alwaysOn,
  warning,
  onToggle,
  onViewContent,
}: Props): React.ReactElement {
  const badgeColors = BADGE_COLORS[id] ?? { bg: '#F0F2F8', text: '#667085', border: '#E7EAF3' }
  const dotColor = LAYER_DOTS[id] ?? '#888'

  return (
    <div className={styles.header}>
      <div className={styles.topRow}>
        {/* Numbered badge */}
        <div
          className={styles.badge}
          style={{ background: badgeColors.bg, color: badgeColors.text, borderColor: badgeColors.border }}
        >
          {layerIndex + 1}
        </div>

        {/* Title group */}
        <div className={styles.titleGroup}>
          <div className={styles.title}>{title}</div>
          <div className={styles.description}>{description}</div>
        </div>

        {/* Right: token count + toggle */}
        <div className={styles.rightGroup}>
          {enabled && tokenCount > 0 && (
            <span className={`${styles.tokenCount} ${styles.tokenCountActive}`}>
              ~{tokenCount}
            </span>
          )}
          <label className={`${styles.toggle}${alwaysOn ? ` ${styles.toggleDisabled}` : ''}`}>
            <input
              type="checkbox"
              className={styles.toggleInput}
              checked={enabled}
              onChange={onToggle}
              disabled={alwaysOn}
              aria-label={`Toggle ${title}`}
            />
            <div
              className={`${styles.toggleTrack}${enabled ? ` ${styles.on}` : ''}`}
              style={enabled ? { background: dotColor } : {}}
            >
              <div className={styles.toggleThumb} />
            </div>
          </label>
        </div>
      </div>

      {/* Warning note */}
      {!enabled && warning && (
        <div className={styles.noteRow}>
          <span className={styles.noteIcon}>⚠</span>
          <span className={styles.noteText}>{warning}</span>
        </div>
      )}

      {/* View content trigger */}
      <div className={styles.viewRow}>
        <button className={styles.viewBtn} onClick={onViewContent} type="button">
          <span className={styles.viewIcon}>⊞</span>
          View content
        </button>
      </div>
    </div>
  )
}
