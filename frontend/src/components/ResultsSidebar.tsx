import React from 'react'
import type { RunResult } from '../types'
import type { EvaluationParameters } from '../store/llmConfigStore'
import { DEFAULT_EVALUATION_PARAMETERS } from '../store/llmConfigStore'
import { ScoreGauge } from './ScoreGauge'
import { ScoreDimensionBar } from './ScoreDimensionBar'
import styles from './ResultsSidebar.module.css'

interface Props {
  result: RunResult | null
  isRunning: boolean
  parameterLabels?: EvaluationParameters
}

export function ResultsSidebar({ result, isRunning, parameterLabels }: Props): React.ReactElement {
  const dimensionLabels = new Map(
    [...DEFAULT_EVALUATION_PARAMETERS, ...(parameterLabels ?? [])].map((parameter) => [parameter.id, parameter.label]),
  )
  const dimensionMax = result?.score_max === 100 ? 10 : 5

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
          <div className={styles.card} title={result.insight}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>Score Breakdown</span>
            </div>
            <div className={styles.cardBody}>
              <div className={styles.dimensions}>
                {(Object.entries(result.score_breakdown) as [string, number][]).map(([key, value]) => (
                  <ScoreDimensionBar
                    key={key}
                    label={dimensionLabels.get(key) ?? key}
                    score={value}
                    max={dimensionMax}
                    title={result.insight}
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
            {result.suggestions && result.suggestions.length > 0 && (
              <div className={styles.suggestionList}>
                {result.suggestions.map((suggestion, index) => (
                  <div key={`${suggestion}-${index}`} className={styles.suggestionItem}>
                    {suggestion}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
