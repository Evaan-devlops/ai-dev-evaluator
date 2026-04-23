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

const LAYER_ICON_LABELS: Record<LayerType, string> = {
  system:    'System instructions',
  user:      'User input',
  history:   'Conversation history',
  knowledge: 'Retrieved knowledge',
  tools:     'Tool definitions',
  state:     'State and memory',
}

function LayerIcon({ id }: { id: LayerType }): React.ReactElement {
  const common = {
    fill: 'none',
    stroke: 'currentColor',
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    strokeWidth: 1.9,
  }

  switch (id) {
    case 'system':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="M5 8h14M5 16h14M8 5v14M16 5v14" />
        </svg>
      )
    case 'user':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM5 20a7 7 0 0 1 14 0" />
        </svg>
      )
    case 'history':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="M4 12a8 8 0 1 0 2.3-5.6M4 5v5h5M12 8v5l3 2" />
        </svg>
      )
    case 'knowledge':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="M6 6c0-1.7 12-1.7 12 0v12c0 1.7-12 1.7-12 0V6ZM6 12c0 1.7 12 1.7 12 0M6 6c0 1.7 12 1.7 12 0" />
        </svg>
      )
    case 'tools':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="m14.5 6 3.5 3.5M5 19l5.5-5.5M13 5.5l5.5 5.5-7 7H6v-5.5l7-7Z" />
        </svg>
      )
    case 'state':
      return (
        <svg className={styles.layerIcon} viewBox="0 0 24 24" aria-hidden>
          <path {...common} d="M8 4h8v16H8V4ZM5 8h3M5 12h3M5 16h3M16 8h3M16 12h3M16 16h3M11 9h2M11 15h2" />
        </svg>
      )
  }
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
        <div
          className={styles.badge}
          style={{ background: badgeColors.bg, color: badgeColors.text, borderColor: badgeColors.border }}
          aria-label={`${layerIndex + 1}. ${LAYER_ICON_LABELS[id]}`}
          title={LAYER_ICON_LABELS[id]}
        >
          <span className={styles.badgeNumber}>{layerIndex + 1}</span>
          <LayerIcon id={id} />
        </div>

        <button
          className={styles.titleGroup}
          type="button"
          onClick={onViewContent}
          title={`Open ${title} content`}
          aria-label={`Open ${title} content`}
        >
          <span className={styles.title}>{title}</span>
          <span className={styles.description}>{description}</span>
        </button>

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

      {warning && (
        <div className={styles.noteRow}>
          <span className={styles.noteIcon}>!</span>
          <span className={styles.noteText}>{warning}</span>
        </div>
      )}
    </div>
  )
}
