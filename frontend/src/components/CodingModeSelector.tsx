import React from 'react'
import type { CodingMode } from '../store/llmConfigStore'
import styles from './CodingModeSelector.module.css'

interface Props {
  selected: CodingMode
  onChange: (mode: CodingMode) => void
}

const MODES: { id: CodingMode; label: string; icon: string; desc: string }[] = [
  {
    id: 'vibe',
    label: 'Vibe Coding',
    icon: '✦',
    desc: 'Describe intent, let the model figure out the rest',
  },
  {
    id: 'agentic',
    label: 'Agentic Coding',
    icon: '⬡',
    desc: 'Structured, multi-step autonomous execution',
  },
]

export function CodingModeSelector({ selected, onChange }: Props): React.ReactElement {
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.cardTitle}>Coding Mode</span>
      </div>
      <div className={styles.options}>
        {MODES.map((mode) => {
          const active = selected === mode.id
          return (
            <button
              key={mode.id}
              type="button"
              className={`${styles.option}${active ? ` ${styles.optionActive}` : ''}`}
              onClick={() => onChange(mode.id)}
              aria-pressed={active}
            >
              <span className={styles.optionIcon}>{mode.icon}</span>
              <div className={styles.optionText}>
                <span className={styles.optionLabel}>{mode.label}</span>
                <span className={styles.optionDesc}>{mode.desc}</span>
              </div>
              {active && <span className={styles.check}>✓</span>}
            </button>
          )
        })}
      </div>
    </div>
  )
}
