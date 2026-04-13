import React from 'react'
import type { LayerType } from '../types'
import styles from './ActiveLayerBadges.module.css'

interface Props {
  activeLayers: LayerType[]
  size?: 'sm' | 'md'
}

const BADGE_CONFIG: Record<LayerType, { label: string; dot: string; bg: string; text: string; border: string }> = {
  system:    { label: 'SYS', dot: '#67C587', bg: '#EAF8EF', text: '#1C6F3A', border: '#B8E8CA' },
  user:      { label: 'USR', dot: '#5B8DEF', bg: '#EAF1FF', text: '#1E4FB5', border: '#B3CFF5' },
  history:   { label: 'HIS', dot: '#8B7CFF', bg: '#F3EFFF', text: '#4B3BBF', border: '#C9C2F8' },
  knowledge: { label: 'KNW', dot: '#58C4DD', bg: '#EAF9FC', text: '#1B7A92', border: '#A9DEE9' },
  tools:     { label: 'TLS', dot: '#F5B14C', bg: '#FFF5E8', text: '#995410', border: '#F5D8A8' },
  state:     { label: 'STA', dot: '#E88AC6', bg: '#FDEFFA', text: '#8C2E72', border: '#F0C0E0' },
}

export function ActiveLayerBadges({ activeLayers, size = 'md' }: Props): React.ReactElement {
  return (
    <div className={styles.container}>
      {activeLayers.map((layer) => {
        const cfg = BADGE_CONFIG[layer]
        if (!cfg) return null
        if (size === 'sm') {
          return (
            <span
              key={layer}
              className={`${styles.badge} ${styles.sm}`}
              style={{ background: cfg.bg, borderColor: cfg.border }}
              title={layer}
            >
              <span className={styles.dot} style={{ background: cfg.dot }} />
            </span>
          )
        }
        return (
          <span
            key={layer}
            className={styles.badge}
            style={{ background: cfg.bg, color: cfg.text, borderColor: cfg.border }}
            title={layer}
          >
            {cfg.label}
          </span>
        )
      })}
    </div>
  )
}
