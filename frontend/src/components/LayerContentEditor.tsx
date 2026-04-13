import React from 'react'
import type { LayerType } from '../types'
import styles from './LayerContentEditor.module.css'

interface Props {
  layerId: LayerType
  content: string
  tokenEstimate: number
  onContentChange: (content: string) => void
}

export function LayerContentEditor({
  content,
  tokenEstimate,
  onContentChange,
}: Props): React.ReactElement {
  return (
    <div className={styles.editorWrap}>
      <textarea
        className={styles.textarea}
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        spellCheck={false}
      />
      <div className={styles.footer}>
        <span className={styles.tokenEstimate}>~{tokenEstimate} tokens</span>
        <span className={styles.hint}>Edit content to adjust token usage</span>
      </div>
    </div>
  )
}
