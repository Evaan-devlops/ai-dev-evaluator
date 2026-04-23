import React from 'react'
import { Modal } from './Modal'
import styles from './ContextBriefPanel.module.css'

interface Props {
  isOpen: boolean
  onClose: () => void
}

export function ContextBriefPanel({ isOpen, onClose }: Props): React.ReactElement | null {
  return (
    <Modal isOpen={isOpen} onClose={onClose} width="860px">
      <div className={styles.header}>
        <div className={styles.titleGroup}>
          <span className={styles.infoIcon} aria-hidden>
            i
          </span>
          <div>
            <div className={styles.title}>Context Engineering Brief</div>
            <div className={styles.subtitle}>A quick guide to the scenario, task, and key learning outcome.</div>
          </div>
        </div>
        <button className={styles.closeBtn} type="button" onClick={onClose} aria-label="Close">
          x
        </button>
      </div>

      <div className={styles.content}>
        <p>
          <strong>What is Context Engineering?</strong> When we interact with LLMs, most people focus only on the user prompt
          (what you type). But production LLM applications send much more than just a prompt - they assemble a rich
          <em> context window</em> with system instructions, conversation history, retrieved knowledge, tool definitions, and
          session state. The discipline of designing all the context that goes into an LLM is called <strong>context engineering</strong>.
        </p>
        <p>
          <strong>The Scenario:</strong> A frustrated customer named Marcus contacts NovaTech Electronics about defective
          $1,899 headphones. He's already tried self-service (portal was broken), waited 45 minutes on hold (got disconnected),
          and is now threatening a credit card dispute. He's actually a Platinum-tier customer with $12,400 in lifetime spend.
        </p>
        <p>
          <strong>Your Task:</strong> Toggle the six context layers on/off and run the prompt against a real LLM. An automated
          rubric scores each response across 8 quality dimensions (persona, policy accuracy, empathy, context awareness,
          actionability, personalization, hallucination avoidance, and completeness). Watch how the score changes dramatically
          as you add or remove layers.
        </p>
        <p>
          <strong>Key Insight:</strong> Prompt engineering = optimizing Layer 2 (user input). Context engineering = designing
          all six layers to work together. The difference between a ~15% score and an 85%+ score isn't better prompting - it's
          better context.
        </p>
      </div>
    </Modal>
  )
}
