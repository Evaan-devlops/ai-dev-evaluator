import React, { useRef } from 'react'
import styles from './Toolbar.module.css'

interface Props {
  isRunning: boolean
  isAssembling: boolean
  showAssembledPrompt: boolean
  onRun: () => void
  onAssemble: () => void
  onToggleAssembledPrompt: () => void
  onConfigure: () => void
  onConfigurePrd: () => void
  onUploadDocument: (file: File) => void
  totalTokens: number
  enabledLayerCount: number
  hasPrd: boolean
  isUploadingDocument?: boolean
  uploadStatus?: { ok: boolean; message: string } | null
}

export function Toolbar({
  isRunning,
  isAssembling,
  showAssembledPrompt,
  onRun,
  onAssemble,
  onToggleAssembledPrompt,
  onConfigure,
  onConfigurePrd,
  onUploadDocument,
  totalTokens: _totalTokens,
  enabledLayerCount,
  hasPrd,
  isUploadingDocument = false,
  uploadStatus = null,
}: Props): React.ReactElement {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onUploadDocument(file)
      // Reset so same file can be re-uploaded
      e.target.value = ''
    }
  }

  return (
    <header className={styles.toolbar}>
      <div className={styles.left}>
        <div className={styles.appIcon}>⬡</div>
        <div className={styles.titleGroup}>
          <span className={styles.appName}>AI Response Improver</span>
        </div>
      </div>

      <div className={styles.right}>
        {/* Document upload */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md,.markdown"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button
          className={`${styles.btn} ${styles.btnUpload}${isUploadingDocument ? ` ${styles.btnUploading}` : ''}`}
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploadingDocument}
          type="button"
          title={uploadStatus ? uploadStatus.message : 'Upload document to RAG / ingestion API'}
          aria-label="Upload document"
        >
          {isUploadingDocument ? '↑' : '+'}
        </button>

        {uploadStatus && (
          <span
            className={uploadStatus.ok ? styles.uploadOk : styles.uploadErr}
            title={uploadStatus.message}
          >
            {uploadStatus.ok ? '✓ Uploaded' : '✕ Upload failed'}
          </span>
        )}

        <button className={`${styles.btn} ${styles.btnSecondary}`} onClick={onConfigure} type="button">
          ⚙ Configure
        </button>

        <button className={`${styles.btn} ${styles.btnSecondary}${hasPrd ? ` ${styles.btnPrdActive}` : ''}`} onClick={onConfigurePrd} type="button">
          PRD
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
