import React, { useState, useEffect } from 'react'
import type { LayerType } from '../types'
import { Modal } from './Modal'
import styles from './LayerContentModal.module.css'

interface Props {
  layerId: LayerType | null
  layerTitle: string
  layerDescription: string
  layerColor: string
  content: string
  tokenEstimate: number
  onSave: (id: LayerType, content: string) => void
  onClose: () => void
}

const LAYER_BG: Record<LayerType, string> = {
  system:    '#EAF8EF',
  user:      '#EAF1FF',
  history:   '#F3EFFF',
  knowledge: '#EAF9FC',
  tools:     '#FFF5E8',
  state:     '#FDEFFA',
}

export function LayerContentModal({
  layerId,
  layerTitle,
  layerDescription,
  layerColor,
  content,
  tokenEstimate,
  onSave,
  onClose,
}: Props): React.ReactElement | null {
  const [draft, setDraft] = useState(content)

  // Reset draft when a new layer opens
  useEffect(() => {
    setDraft(content)
  }, [layerId, content])

  if (!layerId) return null

  const accentBg = LAYER_BG[layerId] ?? '#F5F6FB'

  const handleSave = () => {
    onSave(layerId, draft)
    onClose()
  }

  const handleCancel = () => {
    setDraft(content) // discard edits
    onClose()
  }

  return (
    <Modal isOpen width="820px" onClose={handleCancel}>
      {/* Header */}
      <div className={styles.header} style={{ borderTop: `3px solid ${layerColor}` }}>
        <div className={styles.headerLeft}>
          <span
            className={styles.badge}
            style={{ background: accentBg, color: layerColor, borderColor: layerColor }}
          >
            {layerTitle.charAt(0)}
          </span>
          <div>
            <div className={styles.title}>{layerTitle}</div>
            <div className={styles.subtitle}>{layerDescription}</div>
          </div>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.tokenBadge}>~{tokenEstimate} tokens</span>
          <button className={styles.closeBtn} onClick={handleCancel} aria-label="Close">✕</button>
        </div>
      </div>

      {/* Body */}
      <div className={styles.body}>
        <textarea
          className={styles.editor}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          spellCheck={false}
          aria-label={`Edit ${layerTitle} content`}
        />
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.charCount}>{draft.length} characters</span>
        <div className={styles.footerActions}>
          <button className={styles.cancelBtn} onClick={handleCancel} type="button">Cancel</button>
          <button
            className={styles.saveBtn}
            onClick={handleSave}
            type="button"
            style={{ background: layerColor }}
          >
            Save
          </button>
        </div>
      </div>
    </Modal>
  )
}
