import React, { useState } from 'react'
import { useWorkbenchStore } from '../../store/workbenchStore'
import { useLLMConfigStore } from '../../store/llmConfigStore'
import { WorkbenchLayout } from '../../components/WorkbenchLayout'
import { Toolbar } from '../../components/Toolbar'
import { ContextBriefPanel } from '../../components/ContextBriefPanel'
import { LayerCard } from '../../components/LayerCard'
import { TokenBudgetBar } from '../../components/TokenBudgetBar'
import { AssembledPromptPanel } from '../../components/AssembledPromptPanel'
import { ResultsSidebar } from '../../components/ResultsSidebar'
import { RunHistoryTable } from '../../components/RunHistoryTable'
import { ModelResponsePanel } from '../../components/ModelResponsePanel'
import { LayerContentModal } from '../../components/LayerContentModal'
import { ConfigureModal } from '../../components/ConfigureModal'
import { uploadDocument } from '../../api/documentsApi'
import type { LayerType } from '../../types'
import styles from './WorkbenchPage.module.css'

export function WorkbenchPage(): React.ReactElement {
  const {
    layers,
    tokenBudgetMax,
    assembledPrompt,
    perLayerTokens,
    totalTokens,
    runHistory,
    selectedRun,
    isRunning,
    isAssembling,
    showAssembledPrompt,
    error,
    toggleLayer,
    updateLayerContent,
    setShowAssembledPrompt,
    assemble,
    run,
    selectRun,
    clearError,
  } = useWorkbenchStore()

  const { config: llmConfig, isConfigureOpen, configureInitialSection, openConfigure, openConfigurePrd, closeConfigure, saveConfig } = useLLMConfigStore()

  const [openLayerModalId, setOpenLayerModalId] = useState<LayerType | null>(null)
  const [historyCollapsed, setHistoryCollapsed] = useState(false)
  const [isBriefOpen, setIsBriefOpen] = useState(false)
  const [modelResponseCollapsed, setModelResponseCollapsed] = useState(false)
  const [isUploadingDocument, setIsUploadingDocument] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{ ok: boolean; message: string } | null>(null)

  const sortedLayers = [...layers].sort((a, b) => a.order - b.order)
  const enabledLayerCount = layers.filter((l) => l.enabled).length
  const selectedRunId = selectedRun?.run_id ?? null

  const handleRun = async () => { await run() }
  const handleAssemble = async () => { await assemble(); setShowAssembledPrompt(true) }
  const handleSelectRun = (runId: number) => { void selectRun(runId) }
  const handleUploadDocument = async (file: File) => {
    setIsUploadingDocument(true)
    setUploadStatus(null)
    try {
      const result = await uploadDocument(file, llmConfig)
      if (result.document_id) {
        saveConfig({ ...llmConfig, ragDocumentId: result.document_id })
      }
      setUploadStatus({
        ok: result.ok,
        message: result.message || `Uploaded ${file.name}`,
      })
    } catch (error) {
      setUploadStatus({
        ok: false,
        message: (error as Error).message,
      })
    } finally {
      setIsUploadingDocument(false)
    }
  }

  const openLayer = openLayerModalId
    ? layers.find((l) => l.id === openLayerModalId) ?? null
    : null

  const toolbar = (
    <Toolbar
      isRunning={isRunning}
      isAssembling={isAssembling}
      showAssembledPrompt={showAssembledPrompt}
      onRun={handleRun}
      onAssemble={handleAssemble}
      onToggleAssembledPrompt={() => setShowAssembledPrompt(!showAssembledPrompt)}
      onConfigure={openConfigure}
      onConfigurePrd={openConfigurePrd}
      onUploadDocument={handleUploadDocument}
      totalTokens={totalTokens}
      enabledLayerCount={enabledLayerCount}
      hasPrd={llmConfig.prd.trim().length > 0}
      isUploadingDocument={isUploadingDocument}
      uploadStatus={uploadStatus}
    />
  )

  const leftPanel = (
    <>
      <div className={styles.panelHeader}>
        <span className={styles.panelTitle}>Context Layers</span>
        <div className={styles.panelHeaderRight}>
          <span className={styles.panelSub}>{enabledLayerCount}/6 active</span>
          <button
            className={styles.headerBtn}
            onClick={() => setIsBriefOpen(true)}
            type="button"
            title="Open context engineering brief"
          >
            Brief
          </button>
        </div>
      </div>

      {sortedLayers.map((layer, idx) => (
        <LayerCard
          key={layer.id}
          layer={layer}
          layerIndex={idx}
          tokenCount={perLayerTokens[layer.id] ?? layer.token_estimate}
          onToggle={(id: LayerType) => toggleLayer(id)}
          onViewContent={(id: LayerType) => setOpenLayerModalId(id)}
        />
      ))}
    </>
  )

  const middlePanel = (
    <>
      {error && (
        <div className={styles.errorBanner}>
          <span className={styles.errorIcon}>⚠</span>
          <span className={styles.errorText}>{error}</span>
          <button className={styles.errorClose} onClick={clearError} aria-label="Dismiss">✕</button>
        </div>
      )}

      <TokenBudgetBar
        layers={sortedLayers}
        perLayerTokens={perLayerTokens}
        totalTokens={totalTokens}
        tokenBudgetMax={tokenBudgetMax}
      />

      {showAssembledPrompt && (
        <div className={styles.promptSection}>
          <div className={styles.promptSectionHeader}>
            <span className={styles.promptSectionTitle}>Assembled Prompt</span>
            <button
              className={styles.closeBtn}
              onClick={() => setShowAssembledPrompt(false)}
              aria-label="Close"
            >
              ✕
            </button>
          </div>
          <AssembledPromptPanel
            assembledPrompt={assembledPrompt}
            layers={sortedLayers}
            isAssembling={isAssembling}
          />
        </div>
      )}

      {/* Model Response + Run History */}
      <div className={styles.responseHistoryGroup}>
        {selectedRun && !isRunning && (
          <ModelResponsePanel
            result={selectedRun}
            expanded={historyCollapsed}
            collapsed={modelResponseCollapsed}
            onToggleCollapsed={() => setModelResponseCollapsed((collapsed) => !collapsed)}
          />
        )}

        <div className={`${styles.historySection}${historyCollapsed ? ` ${styles.historySectionCollapsed}` : ''}`}>
          {/* Entire header row is clickable to toggle */}
          <div
            className={styles.historySectionHeader}
            style={historyCollapsed ? { borderBottom: 'none' } : undefined}
            onClick={() => setHistoryCollapsed((c) => !c)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setHistoryCollapsed((c) => !c)}
            aria-expanded={!historyCollapsed}
          >
            <span className={styles.sectionTitle}>Run History</span>
            <div className={styles.historySectionRight}>
              <span className={styles.sectionSub}>
                {runHistory.length} {runHistory.length === 1 ? 'run' : 'runs'}
              </span>
              <span className={styles.chevron} aria-hidden>
                {historyCollapsed ? '›' : '⌄'}
              </span>
            </div>
          </div>

          {historyCollapsed ? (
            <div className={styles.collapsedHint}>Click to expand run history</div>
          ) : (
            <RunHistoryTable
              runHistory={runHistory}
              selectedRunId={selectedRunId}
              onSelectRun={handleSelectRun}
            />
          )}
        </div>
      </div>
    </>
  )

  const rightPanel = (
    <ResultsSidebar
      result={selectedRun}
      isRunning={isRunning}
      parameterLabels={llmConfig.prdParameters}
    />
  )

  return (
    <>
      <WorkbenchLayout
        toolbar={toolbar}
        leftPanel={leftPanel}
        middlePanel={middlePanel}
        rightPanel={rightPanel}
      />

      <ContextBriefPanel
        isOpen={isBriefOpen}
        onClose={() => setIsBriefOpen(false)}
      />

      {openLayer && (
        <LayerContentModal
          layerId={openLayer.id}
          layerTitle={openLayer.title}
          layerDescription={openLayer.description}
          layerColor={openLayer.color}
          content={openLayer.content}
          tokenEstimate={perLayerTokens[openLayer.id] ?? openLayer.token_estimate}
          onSave={updateLayerContent}
          onClose={() => setOpenLayerModalId(null)}
        />
      )}

      <ConfigureModal
        isOpen={isConfigureOpen}
        config={llmConfig}
        onSave={saveConfig}
        onClose={closeConfigure}
        initialSection={configureInitialSection}
      />
    </>
  )
}
