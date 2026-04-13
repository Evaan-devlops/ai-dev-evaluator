import React from 'react'
import type { ContextLayer, LayerType } from '../types'
import { LayerHeader } from './LayerHeader'
import styles from './LayerCard.module.css'

interface Props {
  layer: ContextLayer
  layerIndex: number
  tokenCount: number
  onToggle: (id: LayerType) => void
  onViewContent: (id: LayerType) => void
}

export function LayerCard({
  layer,
  layerIndex,
  tokenCount,
  onToggle,
  onViewContent,
}: Props): React.ReactElement {
  return (
    <div
      className={`${styles.card}${layer.enabled ? ` ${styles.enabled}` : ` ${styles.disabled}`}`}
      style={{ animationDelay: `${layerIndex * 40}ms` }}
    >
      <LayerHeader
        id={layer.id}
        title={layer.title}
        description={layer.description}
        enabled={layer.enabled}
        tokenCount={tokenCount}
        layerIndex={layerIndex}
        alwaysOn={layer.always_on}
        warning={layer.warning}
        onToggle={() => onToggle(layer.id)}
        onViewContent={() => onViewContent(layer.id)}
      />
    </div>
  )
}
