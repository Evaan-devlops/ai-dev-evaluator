import React from 'react'
import type { ContextLayer } from '../types'
import styles from './AssembledPromptPanel.module.css'

const LAYER_COLORS: Record<string, string> = {
  system: '#59c36a',
  user: '#4f8df7',
  history: '#8b7cf6',
  knowledge: '#57c7d4',
  tools: '#f2a04a',
  state: '#d96aa7',
}

const LAYER_LABELS: Record<string, string> = {
  system: 'SYSTEM INSTRUCTIONS',
  user: 'USER INPUT',
  history: 'CONVERSATION HISTORY',
  knowledge: 'RETRIEVED KNOWLEDGE',
  tools: 'TOOL DEFINITIONS',
  state: 'STATE & MEMORY',
}

interface Props {
  assembledPrompt: string
  layers: ContextLayer[]
  isAssembling: boolean
}

export function AssembledPromptPanel({ assembledPrompt, layers, isAssembling }: Props): React.ReactElement {
  const enabledLayers = layers.filter((l) => l.enabled).sort((a, b) => a.order - b.order)

  if (isAssembling) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Assembling prompt...</div>
      </div>
    )
  }

  if (!assembledPrompt || enabledLayers.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.empty}>
          Enable at least one layer and click "Assemble" to see the prompt.
        </div>
      </div>
    )
  }

  // Split assembled prompt into labeled sections for display
  const sections = enabledLayers.map((layer) => ({
    layer,
    content: layer.content,
    color: LAYER_COLORS[layer.id] ?? '#64748b',
    label: LAYER_LABELS[layer.id] ?? layer.id.toUpperCase(),
  }))

  return (
    <div className={styles.container}>
      {sections.map(({ layer, content, color, label }) => (
        <div key={layer.id} className={styles.section}>
          <div className={styles.sectionHeader} style={{ borderLeftColor: color, color }}>
            === {label} ===
          </div>
          <pre className={styles.content}>{content}</pre>
        </div>
      ))}
    </div>
  )
}
