import React, { useState } from 'react'
import type { LLMConfig, LLMProvider } from '../store/llmConfigStore'
import { Modal } from './Modal'
import styles from './ConfigureModal.module.css'

interface Props {
  isOpen: boolean
  config: LLMConfig
  onSave: (config: LLMConfig) => void
  onClose: () => void
}

const PROVIDERS: { value: LLMProvider; label: string }[] = [
  { value: 'mock',   label: 'Mock Provider' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'nvidia', label: 'NVIDIA' },
]

const GEMINI_MODELS  = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-pro']
const OPENAI_MODELS  = ['gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini', 'gpt-4o']
const NVIDIA_MODELS  = [
  'meta/llama-3.1-70b-instruct',
  'mistralai/mixtral-8x7b-instruct-v0.1',
  'google/gemma-3-27b-it',
  'openai/gpt-oss-120b',
]

function ApiKeyField({
  label,
  value,
  placeholder,
  helper,
  onChange,
}: {
  label: string
  value: string
  placeholder: string
  helper?: string
  onChange: (v: string) => void
}) {
  const [show, setShow] = useState(false)
  const masked = value ? '•'.repeat(Math.min(value.length, 20)) : ''

  return (
    <div className={styles.field}>
      <label className={styles.label}>{label}</label>
      <div className={styles.inputWrap}>
        <input
          type={show ? 'text' : 'password'}
          className={styles.input}
          value={show ? value : (value ? masked : '')}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          type="button"
          className={styles.eyeBtn}
          onClick={() => setShow((s) => !s)}
          aria-label={show ? 'Hide key' : 'Show key'}
        >
          {show ? '🙈' : '👁'}
        </button>
      </div>
      {helper && <div className={styles.helper}>{helper}</div>}
    </div>
  )
}

function ModelSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (v: string) => void
}) {
  return (
    <div className={styles.field}>
      <label className={styles.label}>{label}</label>
      <select className={styles.select} value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

export function ConfigureModal({ isOpen, config, onSave, onClose }: Props): React.ReactElement | null {
  const [draft, setDraft] = useState<LLMConfig>({ ...config })

  const update = <K extends keyof LLMConfig>(key: K, value: LLMConfig[K]) =>
    setDraft((prev) => ({ ...prev, [key]: value }))

  const handleSave = () => onSave(draft)

  const p = draft.provider

  return (
    <Modal isOpen={isOpen} onClose={onClose} width="680px">
      {/* Header */}
      <div className={styles.header}>
        <div>
          <div className={styles.title}>Configure LLM</div>
          <div className={styles.subtitle}>
            Set API keys and choose the provider and model for response generation and scoring.
          </div>
        </div>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
      </div>

      {/* Body */}
      <div className={styles.body}>
        {/* Provider */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Provider</div>
          <div className={styles.providerRow}>
            {PROVIDERS.map(({ value, label }) => (
              <button
                key={value}
                type="button"
                className={`${styles.providerBtn}${p === value ? ` ${styles.providerBtnActive}` : ''}`}
                onClick={() => update('provider', value)}
              >
                {label}
              </button>
            ))}
          </div>
          <div className={styles.statusLine}>
            Currently using: <strong>{PROVIDERS.find(x => x.value === p)?.label ?? p}</strong>
            {draft.enableLiveProvider && p !== 'mock' && (
              <span className={styles.liveChip}>live</span>
            )}
          </div>
        </div>

        {/* Gemini block */}
        {p === 'gemini' && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>Gemini Configuration</div>
            <ApiKeyField
              label="Gemini API Key"
              value={draft.geminiApiKey}
              placeholder="Enter Gemini API key"
              helper="Required only if Gemini is selected and live provider is enabled."
              onChange={(v) => update('geminiApiKey', v)}
            />
            <ModelSelect
              label="Model"
              value={draft.geminiModel}
              options={GEMINI_MODELS}
              onChange={(v) => update('geminiModel', v)}
            />
          </div>
        )}

        {/* OpenAI block */}
        {p === 'openai' && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>OpenAI Configuration</div>
            <ApiKeyField
              label="OpenAI API Key"
              value={draft.openaiApiKey}
              placeholder="sk-..."
              helper="Required only if OpenAI is selected and live provider is enabled."
              onChange={(v) => update('openaiApiKey', v)}
            />
            <ModelSelect
              label="Model"
              value={draft.openaiModel}
              options={OPENAI_MODELS}
              onChange={(v) => update('openaiModel', v)}
            />
          </div>
        )}

        {/* NVIDIA block */}
        {p === 'nvidia' && (
          <div className={styles.section}>
            <div className={styles.sectionLabel}>NVIDIA Configuration</div>
            <ApiKeyField
              label="NVIDIA API Key"
              value={draft.nvidiaApiKey}
              placeholder="Enter NVIDIA API key"
              helper="Required only if NVIDIA is selected and live provider is enabled."
              onChange={(v) => update('nvidiaApiKey', v)}
            />
            <ModelSelect
              label="Model"
              value={draft.nvidiaModel}
              options={NVIDIA_MODELS}
              onChange={(v) => update('nvidiaModel', v)}
            />
          </div>
        )}

        {/* General settings */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Generation Settings</div>
          <div className={styles.twoCol}>
            <div className={styles.field}>
              <label className={styles.label}>Temperature</label>
              <input
                type="number"
                className={styles.input}
                value={draft.temperature}
                min={0}
                max={2}
                step={0.1}
                onChange={(e) => update('temperature', parseFloat(e.target.value) || 0)}
              />
            </div>
            <div className={styles.field}>
              <label className={styles.label}>Max Output Tokens</label>
              <input
                type="number"
                className={styles.input}
                value={draft.maxOutputTokens}
                min={100}
                max={8000}
                step={100}
                onChange={(e) => update('maxOutputTokens', parseInt(e.target.value, 10) || 1200)}
              />
            </div>
          </div>

          <div className={styles.toggleRow}>
            <div>
              <div className={styles.toggleLabel}>Enable live provider use</div>
              <div className={styles.toggleHelper}>
                When disabled, the app uses mock/demo responses even if keys are saved.
              </div>
            </div>
            <label className={styles.toggle}>
              <input
                type="checkbox"
                checked={draft.enableLiveProvider}
                onChange={(e) => update('enableLiveProvider', e.target.checked)}
              />
              <span className={`${styles.toggleTrack}${draft.enableLiveProvider ? ` ${styles.toggleOn}` : ''}`}>
                <span className={styles.toggleThumb} />
              </span>
            </label>
          </div>
        </div>

        {/* Info notice */}
        <div className={styles.notice}>
          <span className={styles.noticeIcon}>ℹ</span>
          <span className={styles.noticeText}>
            These settings are stored locally and will be used by future versions to generate
            model responses and score breakdown values via the selected provider.
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <button className={styles.cancelBtn} onClick={onClose} type="button">Cancel</button>
        <button className={styles.saveBtn} onClick={handleSave} type="button">Save Keys</button>
      </div>
    </Modal>
  )
}
