import React from 'react'
import type { RunResult } from '../types'
import { ScoreGauge } from './ScoreGauge'
import { ScoreDimensionBar } from './ScoreDimensionBar'
import styles from './ResultsSidebar.module.css'

interface Props {
  result: RunResult | null
  isRunning: boolean
}

const DIMENSION_LABELS: Record<string, string> = {
  persona:         'Persona Adherence',
  policy:          'Policy Accuracy',
  empathy:         'Empathy & Tone',
  context:         'Context Awareness',
  actionability:   'Actionability',
  personalization: 'Personalization',
  hallucination:   'No Hallucination',
  completeness:    'Completeness',
}

export function ResultsSidebar({ result, isRunning }: Props): React.ReactElement {
  return (
    <div className={styles.sidebar}>
      {/* Panel header */}
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Results</span>
      </div>

      {isRunning && (
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <span className={styles.loadingText}>Running evaluation…</span>
        </div>
      )}

      {!isRunning && !result && (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>📊</div>
          <p className={styles.emptyText}>
            Configure layers and click <strong>Run</strong> to evaluate.
          </p>
        </div>
      )}

      {!isRunning && result && (
        <>
          {/* Score gauge + meta */}
          <div className={styles.scoreCard}>
            <ScoreGauge score={result.quality_score} max={result.score_max} />
            <div className={styles.scoreMeta}>
              <div className={styles.metaItem}>
                <span className={styles.metaLabel}>Run</span>
                <span className={styles.metaValue}>#{result.run_number}</span>
              </div>
              <div className={styles.metaItem}>
                <span className={styles.metaLabel}>Tokens</span>
                <span className={styles.metaValue}>{result.total_tokens.toLocaleString()}</span>
              </div>
              <div className={styles.metaItem}>
                <span className={styles.metaLabel}>Layers</span>
                <span className={styles.metaValue}>{result.active_layers.length}</span>
              </div>
            </div>
          </div>

          {/* Score breakdown */}
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>Score Breakdown</span>
            </div>
            <div className={styles.cardBody}>
              <div className={styles.dimensions}>
                {(Object.entries(result.score_breakdown) as [string, number][]).map(([key, value]) => (
                  <ScoreDimensionBar
                    key={key}
                    label={DIMENSION_LABELS[key] ?? key}
                    score={value}
                    max={5}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Insight */}
          <div className={styles.insightBox}>
            <div className={styles.insightHeader}>
              <span className={styles.insightIcon}>💡</span>
              <span className={styles.insightTitle}>Insight</span>
            </div>
            <p className={styles.insight}>{result.insight}</p>
          </div>
        </>
      )}
    </div>
  )
}
