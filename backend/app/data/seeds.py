from __future__ import annotations

SYSTEM_CONTENT = """You are Alex, a Senior Resolution Specialist at NovaTech Electronics. You have 8 years of experience and authority to approve resolutions up to $2,000 without manager approval.

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
- Reference the customer's tier status, history, and profile when personalizing your response"""

USER_CONTENT = """No! The portal just gave me some error — it wouldn't let me submit anything. So I called your support line and sat on hold for 45 MINUTES before I got disconnected. This is now my third attempt to get this resolved. I'm absolutely livid — these are $1,899 headphones that I need for my professional work and the left ear is crackling after barely a month. I'm about to dispute this on my credit card if someone doesn't fix this RIGHT NOW."""

HISTORY_CONTENT = """[user]: Hi, I need help with a defective product. Order number NVT-2024-91847.

[assistant]: I'd be happy to help you with order NVT-2024-91847. I can see this is for the NovaSound Pro 3000 headphones purchased on January 15th. What issue are you experiencing?

[user]: The left ear has developed a crackling sound. I already tried the troubleshooting steps on your website — reset the headphones, updated firmware, tried different audio sources. Nothing works. It's clearly a hardware defect.

[assistant]: Thank you for trying those troubleshooting steps, Marcus. The crackling in the left ear after firmware updates and resets does sound like a hardware issue. Let me look into the best resolution options for you. I see you also attempted to use our self-service return portal — were you able to submit a return request there?

[user]: No! The portal gave me an error every single time. I've tried four times over the past two days.

[assistant]: I completely understand your frustration, Marcus. Let me check the portal status and your account to find the best path forward for you."""

KNOWLEDGE_CONTENT = """## NovaTech Return & Warranty Policy (Effective Jan 2024)

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
- Platinum customers may receive a 90-day resolution accommodation review for high-value audio products, subject to account standing and defect validation"""

TOOLS_CONTENT = """### lookup_order(order_id: string)
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
Returns: escalation ticket ID, estimated callback time."""

STATE_CONTENT = """## Customer Profile: Marcus Rivera
- Customer ID: CUST-8847231
- Tier: Platinum (since 2021)
- Lifetime spend: $12,400 across 23 orders
- Average satisfaction rating: 4.8/5 (from 15 post-interaction surveys)
- Professional usage note: audio production professional; uses equipment for paid client work
- Previous support history: 1 prior support case in 2023, resolved same-day, rated 5/5
- Account standing: excellent payment history, no disputes, no abuse flags"""


DEFAULT_LAYERS = [
    {
        "id": "system",
        "title": "System Instructions",
        "description": "Who the model is, how it should behave, what rules to follow",
        "enabled": True,
        "content": SYSTEM_CONTENT,
        "token_estimate": 300,
        "order": 0,
        "collapsed": False,
        "color": "#59c36a",
    },
    {
        "id": "user",
        "title": "User Input",
        "description": "The current message from the customer (always on)",
        "enabled": True,
        "content": USER_CONTENT,
        "token_estimate": 110,
        "order": 1,
        "collapsed": False,
        "color": "#4f8df7",
    },
    {
        "id": "history",
        "title": "Conversation History",
        "description": "Prior turns maintaining coherence and avoiding repetition",
        "enabled": True,
        "content": HISTORY_CONTENT,
        "token_estimate": 400,
        "order": 2,
        "collapsed": True,
        "color": "#8b7cf6",
    },
    {
        "id": "knowledge",
        "title": "Retrieved Knowledge",
        "description": "RAG results: policies, docs, database records",
        "enabled": True,
        "content": KNOWLEDGE_CONTENT,
        "token_estimate": 600,
        "order": 3,
        "collapsed": True,
        "color": "#57c7d4",
    },
    {
        "id": "tools",
        "title": "Tool Definitions",
        "description": "Available tools the model can call to take action",
        "enabled": True,
        "content": TOOLS_CONTENT,
        "token_estimate": 300,
        "order": 4,
        "collapsed": True,
        "color": "#f2a04a",
    },
    {
        "id": "state",
        "title": "State & Memory",
        "description": "Persistent facts: customer profile, session context, metadata",
        "enabled": True,
        "content": STATE_CONTENT,
        "token_estimate": 200,
        "order": 5,
        "collapsed": True,
        "color": "#d96aa7",
    },
]


_RESPONSE_USER_ONLY = (
    "I'm sorry to hear you're having trouble. Please try our self-service portal at "
    "support.novatech.com, or contact the team by email at support@novatech.com. "
    "If the issue persists, you can also call 1-800-NOVATECH during business hours."
)

_RESPONSE_SYSTEM_USER = (
    "Hi there! I'm Alex, a Senior Resolution Specialist at NovaTech Electronics, and I want "
    "to personally take ownership of this for you right now.\n\n"
    "What you've been through is completely unacceptable — three attempts, a portal that failed "
    "every time, 45 minutes on hold, and a disconnection. I am so sorry. That's not the experience "
    "you deserved, especially when you rely on this equipment professionally.\n\n"
    "I'm going to make sure we resolve this for you today. Let me pull up your account and "
    "find the fastest path forward."
)

_RESPONSE_SYSTEM_USER_KNOWLEDGE = (
    "Hi there! I'm Alex, a Senior Resolution Specialist at NovaTech Electronics. "
    "I'm so sorry for everything you've had to go through — the portal failures, the 45-minute hold, "
    "the disconnection. None of that should have happened, and I take personal responsibility for "
    "making this right today.\n\n"
    "I want to address the portal issue directly: we have a known bug affecting returns for some "
    "pre-February orders — your order likely falls in that window, which is why you've been seeing "
    "errors. I sincerely apologize. You've been fighting a system problem that was entirely our fault. "
    "I'll process your replacement manually right now.\n\n"
    "For your headphones, since this is a confirmed hardware defect, our policy provides a 45-day "
    "return window (not the standard 30 days for audio products), and we use an advanced replacement "
    "workflow — meaning your replacement ships before you send back the original. You're also entitled "
    "to a $15 inconvenience credit for the portal issue, which I'll apply to your account."
)

_RESPONSE_5_LAYERS = (
    "Hi there! I'm Alex, a Senior Resolution Specialist at NovaTech Electronics.\n\n"
    "I'm deeply sorry for the experience you've had — the portal failing four times, 45 minutes on "
    "hold, a disconnection, and now a third attempt. None of that is acceptable, and I take personal "
    "ownership of making this right today.\n\n"
    "Here's exactly what I'm doing right now:\n\n"
    "1. I'm running lookup_order('NVT-2024-91847') to pull your full order details and confirm "
    "warranty and defect status.\n"
    "2. Since this is a confirmed hardware defect, I'm initiating process_replacement with express "
    "shipping — you'll receive a replacement in 1–2 business days. A prepaid return label will be "
    "emailed within the hour. You keep using the original until the new one arrives.\n"
    "3. I'm issuing a $15 service credit via issue_service_credit for the portal issue, plus an "
    "additional $10 for the disconnection. Both will be applied to your account immediately.\n\n"
    "You don't need to do anything else. The replacement is already in motion."
)

_RESPONSE_ALL_LAYERS = (
    "Marcus, I'm really sorry you've had to make a third attempt to get this resolved, especially "
    "after the portal error and that 45-minute hold followed by a disconnect. I understand how "
    "unacceptable that is, particularly for a $1,899 headset you rely on for professional work.\n\n"
    "I'm Alex, a Senior Resolution Specialist at NovaTech, and I'm going to take ownership of this "
    "from here.\n\n"
    "Here's what I will do:\n"
    "1. I will process a replacement for your NovaSound Pro 3000 as a defective-item replacement.\n"
    "2. I will request expedited shipping because this affects your professional work.\n"
    "3. I will add a $15 inconvenience credit due to the portal issue and failed support attempt.\n"
    "4. I will make sure this is handled manually so you do not need to retry the self-service portal.\n\n"
    "Because this is an audio product and the issue appeared within the applicable support window, "
    "you are eligible for resolution review under our current policy. Since you're also a Platinum "
    "customer with strong account standing, I'll use that context while processing the case.\n\n"
    "If you'd like, I can also show the exact tool actions that would be triggered in this flow."
)


SEEDED_RUNS = [
    # Stored oldest-first; RunHistoryTable reverses to show newest-first
    {
        "run_id": "seed-run-001",
        "run_number": 1,
        "active_layers": ["user"],
        "quality_score": 18,
        "score_max": 40,
        "score_breakdown": {
            "persona_adherence": 2,
            "policy_accuracy": 2,
            "empathy_tone": 2,
            "context_awareness": 2,
            "actionability": 2,
            "personalization": 2,
            "no_hallucination": 2,
            "completeness": 4,
        },
        "insight": (
            "Without context layers, the model has no persona, policy knowledge, or customer history. "
            "Response is generic, suggests self-service (already broken), and provides no real resolution."
        ),
        "llm_response": _RESPONSE_USER_ONLY,
        "latency_ms": 8200,
        "total_tokens": 479,
        "timestamp": "2024-11-20T09:00:00Z",
    },
    {
        "run_id": "seed-run-002",
        "run_number": 2,
        "active_layers": ["system", "user"],
        "quality_score": 23,
        "score_max": 40,
        "score_breakdown": {
            "persona_adherence": 4,
            "policy_accuracy": 2,
            "empathy_tone": 4,
            "context_awareness": 2,
            "actionability": 2,
            "personalization": 2,
            "no_hallucination": 2,
            "completeness": 5,
        },
        "insight": (
            "System instructions give the model a persona and empathy-first tone. Alex introduces "
            "herself and takes ownership. But without policy knowledge, she can't cite specific "
            "return windows, portal incident details, or concrete resolution steps."
        ),
        "llm_response": _RESPONSE_SYSTEM_USER,
        "latency_ms": 5900,
        "total_tokens": 744,
        "timestamp": "2024-11-20T09:05:00Z",
    },
    {
        "run_id": "seed-run-003",
        "run_number": 3,
        "active_layers": ["system", "user", "knowledge"],
        "quality_score": 28,
        "score_max": 40,
        "score_breakdown": {
            "persona_adherence": 4,
            "policy_accuracy": 4,
            "empathy_tone": 4,
            "context_awareness": 3,
            "actionability": 3,
            "personalization": 2,
            "no_hallucination": 4,
            "completeness": 4,
        },
        "insight": (
            "Retrieved knowledge enables policy-accurate responses. The model can now cite the "
            "45-day audio return window, the portal bug, and the $15 inconvenience credit. "
            "Policy accuracy and hallucination risk both improve significantly."
        ),
        "llm_response": _RESPONSE_SYSTEM_USER_KNOWLEDGE,
        "latency_ms": 5700,
        "total_tokens": 1262,
        "timestamp": "2024-11-20T09:10:00Z",
    },
    {
        "run_id": "seed-run-004",
        "run_number": 4,
        "active_layers": ["system", "user", "history", "knowledge", "tools"],
        "quality_score": 30,
        "score_max": 40,
        "score_breakdown": {
            "persona_adherence": 4,
            "policy_accuracy": 5,
            "empathy_tone": 4,
            "context_awareness": 4,
            "actionability": 5,
            "personalization": 2,
            "no_hallucination": 4,
            "completeness": 2,
        },
        "insight": (
            "The model now references specific tools: process_replacement() for express shipping and "
            "issue_service_credit() for the inconvenience. The response becomes actionable, not just "
            "sympathetic. Context awareness improves with history, but without state the response "
            "still treats the customer somewhat generically."
        ),
        "llm_response": _RESPONSE_5_LAYERS,
        "latency_ms": 8200,
        "total_tokens": 1736,
        "timestamp": "2024-11-20T09:15:00Z",
    },
    {
        "run_id": "seed-run-005",
        "run_number": 5,
        "active_layers": ["system", "user", "history", "knowledge", "tools", "state"],
        "quality_score": 31,
        "score_max": 40,
        "score_breakdown": {
            "persona_adherence": 5,
            "policy_accuracy": 3,
            "empathy_tone": 5,
            "context_awareness": 5,
            "actionability": 5,
            "personalization": 5,
            "no_hallucination": 2,
            "completeness": 4,
        },
        "insight": (
            "Full context produces a highly personalized, policy-accurate, actionable response. "
            "Marcus is addressed by name, Platinum tier acknowledged, professional use case noted, "
            "and specific tool calls are proposed. The model leverages all available signals optimally."
        ),
        "llm_response": _RESPONSE_ALL_LAYERS,
        "latency_ms": 8900,
        "total_tokens": 1889,
        "timestamp": "2024-11-20T09:20:00Z",
    },
]
