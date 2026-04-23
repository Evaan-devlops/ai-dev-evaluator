/**
 * Client-side fallback demo data.
 * Used when the backend is unavailable on initial load so the UI
 * never shows a blank / 0-layer screen.
 */
import type { ContextLayer, RunHistoryItem, RunResult } from '../types'

const SYSTEM_CONTENT = `You are Alex, a Senior Resolution Specialist at NovaTech Electronics. You have 8 years of experience and authority to approve resolutions up to $2,000 without manager approval.

CORE RULES:
- Always lead with empathy BEFORE offering solutions
- Use the customer's first name naturally in conversation
- Never say "I can't" or "that's not possible" — always frame what you CAN do
- Acknowledge every frustration the customer mentions before moving forward
- Take personal ownership: use "I will" not "the team will"
- If the customer has had a bad experience, explicitly apologize for it
- Introduce yourself by name and role in your first message
- When you have policy details, cite specific numbers (return windows in days, dollar amounts)
- When proposing a resolution, state exactly what actions you will take and how
- Reference the customer's tier status, history, and profile when personalizing your response`

const USER_CONTENT = `No! The portal just gave me some error — it wouldn't let me submit anything. So I called your support line and sat on hold for 45 MINUTES before I got disconnected. This is now my third attempt to get this resolved. I'm absolutely livid — these are $1,899 headphones that I need for my professional work and the left ear is crackling after barely a month. I'm about to dispute this on my credit card if someone doesn't fix this RIGHT NOW.`

const HISTORY_CONTENT = `[user]: Hi, I need help with a defective product. Order number NVT-2024-91847.

[assistant]: I'd be happy to help you with order NVT-2024-91847. I can see this is for the NovaSound Pro 3000 headphones purchased on January 15th. What issue are you experiencing?

[user]: The left ear has developed a crackling sound. I already tried the troubleshooting steps on your website — reset the headphones, updated firmware, tried different audio sources. Nothing works. It's clearly a hardware defect.

[assistant]: Thank you for trying those troubleshooting steps, Marcus. The crackling in the left ear after firmware updates and resets does sound like a hardware issue. Let me look into the best resolution options for you. I see you also attempted to use our self-service return portal — were you able to submit a return request there?`

const KNOWLEDGE_CONTENT = `## NovaTech Return & Warranty Policy (Effective Jan 2024)

### Standard Return Windows
- General electronics: 30-day return window
- Audio products (headphones, speakers, earbuds): 45-day return window
- Accessories: 14-day return window

### Defective Product Policy
- Products confirmed defective within warranty: free replacement shipped BEFORE customer returns original unit
- Expedited shipping may be approved for professional-use customers
- Agents may provide up to $20 service credit for severe inconvenience cases

### Portal Incident Notice
- Self-service portal currently has a bug affecting returns for some pre-February orders
- Workaround: all pre-Feb return requests must be processed manually by an agent
- Affected customers should receive an apology and a $15 inconvenience credit

### Platinum Customer Override
- Platinum customers may receive a 90-day resolution accommodation review for high-value audio products, subject to account standing and defect validation`

const TOOLS_CONTENT = `### lookup_order(order_id: string)
Look up full order details including items, pricing, dates, and current status.
Returns: order details, shipping info, payment method, and return eligibility.

### process_replacement(order_id: string, item_sku: string, shipping_priority: "standard" | "express" | "overnight")
Initiate a replacement shipment for a defective item. Ships BEFORE customer returns original.
Returns: replacement order ID, tracking number, estimated delivery date.

### issue_service_credit(customer_id: string, amount: number, reason: string)
Add a service credit to the customer's NovaTech account for future purchases.
Returns: credit confirmation, new account balance.

### escalate_to_supervisor(case_id: string, reason: string, priority: "normal" | "urgent")
Escalate the case to a supervisor with full context. Use only when resolution exceeds your authority.
Returns: escalation ticket ID, estimated callback time.`

const STATE_CONTENT = `## Customer Profile: Marcus Rivera
- Customer ID: CUST-8847231
- Tier: Platinum (since 2021)
- Lifetime spend: $12,400 across 23 orders
- Average satisfaction rating: 4.8/5 (from 15 post-interaction surveys)
- Professional usage note: audio production professional; uses equipment for paid client work
- Previous support history: 1 prior support case in 2023, resolved same-day, rated 5/5
- Account standing: excellent payment history, no disputes, no abuse flags`

export const FALLBACK_LAYERS: ContextLayer[] = [
  {
    id: 'system',
    title: 'System Instructions',
    description: 'Who the model is, how it should behave, what rules to follow',
    enabled: true,
    content: SYSTEM_CONTENT,
    token_estimate: 300,
    order: 0,
    collapsed: false,
    color: '#67C587',
    warning: 'Generic bot voice, no persona, no empathy-first rule, no agent identity',
    always_on: false,
  },
  {
    id: 'user',
    title: 'User Input',
    description: 'The current message from the customer (always on)',
    enabled: true,
    content: USER_CONTENT,
    token_estimate: 110,
    order: 1,
    collapsed: false,
    color: '#5B8DEF',
    always_on: true,
  },
  {
    id: 'history',
    title: 'Conversation History',
    description: 'Prior turns maintaining coherence and avoiding repetition',
    enabled: true,
    content: HISTORY_CONTENT,
    token_estimate: 400,
    order: 2,
    collapsed: true,
    color: '#8B7CFF',
    warning: 'Suggests self-service again, forgets order #, ignores prior troubleshooting',
    always_on: false,
  },
  {
    id: 'knowledge',
    title: 'Retrieved Knowledge',
    description: 'RAG results: policies, docs, database records',
    enabled: false,
    content: KNOWLEDGE_CONTENT,
    token_estimate: 600,
    order: 3,
    collapsed: true,
    color: '#58C4DD',
    warning: 'Hallucinating 30-day policy (actual: 45-day audio, 90-day Platinum override)',
    always_on: false,
  },
  {
    id: 'tools',
    title: 'Tool Definitions',
    description: 'Available tools the model can call to take action',
    enabled: false,
    content: TOOLS_CONTENT,
    token_estimate: 300,
    order: 4,
    collapsed: true,
    color: '#F5B14C',
    always_on: false,
  },
  {
    id: 'state',
    title: 'State & Memory',
    description: 'Persistent facts: customer profile, session context, metadata',
    enabled: false,
    content: STATE_CONTENT,
    token_estimate: 200,
    order: 5,
    collapsed: true,
    color: '#E88AC6',
    warning: 'One-size-fits-all response, ignores Platinum tier and professional use case',
    always_on: false,
  },
]

export const FALLBACK_HISTORY: RunHistoryItem[] = [
  { run_id: 1, run_number: 1, active_layers: ['user'], quality_score: 45, score_max: 100, total_tokens: 110, latency_ms: 8200 },
  { run_id: 2, run_number: 2, active_layers: ['system', 'user'], quality_score: 58, score_max: 100, total_tokens: 410, latency_ms: 5900 },
  { run_id: 3, run_number: 3, active_layers: ['system', 'user', 'history'], quality_score: 70, score_max: 100, total_tokens: 810, latency_ms: 5700 },
  { run_id: 4, run_number: 4, active_layers: ['system', 'user', 'history', 'knowledge', 'tools'], quality_score: 75, score_max: 100, total_tokens: 1610, latency_ms: 8200 },
  { run_id: 5, run_number: 5, active_layers: ['system', 'user', 'history', 'knowledge', 'tools', 'state'], quality_score: 85, score_max: 100, total_tokens: 1810, latency_ms: 8900 },
]

export const FALLBACK_BEST_RUN: RunResult = {
  run_id: 5,
  run_number: 5,
  quality_score: 85,
  score_max: 100,
  score_breakdown: {
    persona: 10,
    policy: 6,
    empathy: 10,
    context: 10,
    actionability: 10,
    personalization: 10,
    hallucination: 4,
    completeness: 8,
  },
  insight:
    'Full context produces a highly personalized, policy-accurate, actionable response. ' +
    'Marcus is addressed by name, Platinum tier acknowledged, professional use case noted, ' +
    'and specific tool calls are proposed. The model leverages all available signals optimally.',
  llm_response:
    "Marcus, I'm really sorry you've had to make a third attempt to get this resolved, especially " +
    'after the portal error and that 45-minute hold followed by a disconnect. I understand how ' +
    "unacceptable that is, particularly for a $1,899 headset you rely on for professional work.\n\n" +
    "I'm Alex, a Senior Resolution Specialist at NovaTech, and I'm going to take ownership of this from here.\n\n" +
    "Here's what I will do:\n" +
    '1. I will process a replacement for your NovaSound Pro 3000 as a defective-item replacement.\n' +
    '2. I will request expedited shipping because this affects your professional work.\n' +
    '3. I will add a $15 inconvenience credit due to the portal issue and failed support attempt.\n' +
    '4. I will make sure this is handled manually so you do not need to retry the self-service portal.\n\n' +
    "Because this is an audio product and the issue appeared within the applicable support window, " +
    "you are eligible for resolution review under our current policy. Since you're also a Platinum " +
    "customer with strong account standing, I'll use that context while processing the case.",
  latency_ms: 8900,
  total_tokens: 1810,
  active_layers: ['system', 'user', 'history', 'knowledge', 'tools', 'state'],
  timestamp: new Date().toISOString(),
  provider: 'mock-provider',
}
