import React from 'react'
import styles from './Toolbar.module.css'

interface Props {
  isRunning: boolean
  isAssembling: boolean
  showAssembledPrompt: boolean
  onRun: () => void
  onAssemble: () => void
  onToggleAssembledPrompt: () => void
  onConfigure: () => void
  totalTokens: number
  enabledLayerCount: number
}

export function Toolbar({
  isRunning,
  isAssembling,
  showAssembledPrompt,
  onRun,
  onAssemble,
  onToggleAssembledPrompt,
  onConfigure,
  totalTokens: _totalTokens,
  enabledLayerCount,
}: Props): React.ReactElement {
  return (
    <header className={styles.toolbar}>
      <div className={styles.left}>
        <div className={styles.appIcon}>⬡</div>
        <div className={styles.titleGroup}>
          <span className={styles.appName}>AI Response Evaluator</span>
        </div>
      </div>

      <div className={styles.right}>
        <button className={`${styles.btn} ${styles.btnSecondary}`} onClick={onConfigure} type="button">
          ⚙ Configure
        </button>

        <button
          className={`${styles.btn} ${styles.btnAccent}`}
          onClick={onToggleAssembledPrompt}
          type="button"
        >
          {showAssembledPrompt ? 'Hide Prompt' : 'View Prompt'}
        </button>

        <button
          className={`${styles.btn} ${styles.btnSecondary}`}
          onClick={onAssemble}
          disabled={isAssembling}
          type="button"
        >
          {isAssembling ? 'Assembling…' : 'Assemble'}
        </button>

        <button
          className={`${styles.btn} ${styles.runBtn}`}
          onClick={onRun}
          disabled={isRunning}
          type="button"
        >
          {isRunning ? (
            <>
              <div className={styles.spinner} />
              Running…
            </>
          ) : (
            `Run with ${enabledLayerCount} Layer${enabledLayerCount !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </header>
  )
}
