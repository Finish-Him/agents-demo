"""Domain tools for the Prometheus AI-governance / data-privacy compliance agent."""

from datetime import datetime, timedelta
from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Embedded regulatory data (self-contained for demo — no external DB needed)
# ---------------------------------------------------------------------------

REGULATIONS_DB: dict[str, dict] = {
    "GDPR": {
        "full_name": "General Data Protection Regulation (EU) 2016/679",
        "jurisdiction": "European Union / EEA",
        "effective": "2018-05-25",
        "key_articles": {
            "Art. 5": "Principles: lawfulness, fairness, transparency, purpose limitation, data minimization, accuracy, storage limitation, integrity, accountability.",
            "Art. 6": "Lawful bases for processing: consent, contract, legal obligation, vital interests, public task, legitimate interests.",
            "Art. 7": "Conditions for consent: freely given, specific, informed, unambiguous. Must be as easy to withdraw as to give.",
            "Art. 13": "Information to provide when data is collected directly from the data subject.",
            "Art. 15": "Right of access: data subjects can obtain confirmation and a copy of their personal data.",
            "Art. 17": "Right to erasure ('right to be forgotten'): data subject can request deletion.",
            "Art. 22": "Automated decision-making: right not to be subject to solely automated decisions with legal effects.",
            "Art. 25": "Data protection by design and by default.",
            "Art. 30": "Records of processing activities — controllers and processors must maintain written records.",
            "Art. 33": "Breach notification to supervisory authority within 72 hours.",
            "Art. 35": "Data Protection Impact Assessment (DPIA) required for high-risk processing.",
            "Art. 83": "Penalties: up to EUR 20M or 4% of global annual turnover, whichever is higher.",
        },
    },
    "CCPA": {
        "full_name": "California Consumer Privacy Act (as amended by CPRA)",
        "jurisdiction": "California, USA",
        "effective": "2020-01-01 (CPRA amendments: 2023-01-01)",
        "key_articles": {
            "Sec. 1798.100": "Right to know: consumers can request disclosure of personal information collected.",
            "Sec. 1798.105": "Right to delete: consumers can request deletion of personal information.",
            "Sec. 1798.106": "Right to correct: consumers can request correction of inaccurate data.",
            "Sec. 1798.110": "Right to know categories and specific pieces of data collected.",
            "Sec. 1798.120": "Right to opt-out of sale or sharing of personal information.",
            "Sec. 1798.121": "Right to limit use of sensitive personal information.",
            "Sec. 1798.135": "Methods for submitting opt-out requests; 'Do Not Sell' link.",
            "Sec. 1798.155": "Penalties: up to $2,500 per violation, $7,500 per intentional violation.",
        },
    },
    "EU_AI_ACT": {
        "full_name": "EU Artificial Intelligence Act (Regulation 2024/1689)",
        "jurisdiction": "European Union",
        "effective": "2024-08-01 (phased enforcement through 2027)",
        "key_articles": {
            "Art. 5": "Prohibited AI practices: social scoring, real-time biometric ID in public (exceptions), subliminal manipulation, exploitation of vulnerabilities.",
            "Art. 6": "Classification of high-risk AI systems: Annex I (safety) and Annex III (fundamental rights).",
            "Art. 9": "Risk management system required for high-risk AI: continuous, iterative process.",
            "Art. 10": "Data governance: training data must be relevant, representative, free of errors, complete.",
            "Art. 11": "Technical documentation: must describe system, development process, monitoring.",
            "Art. 13": "Transparency: high-risk AI must be sufficiently transparent for users to interpret output.",
            "Art. 14": "Human oversight: high-risk AI must allow effective human oversight measures.",
            "Art. 52": "Transparency for certain AI: chatbots, deepfakes, and emotion recognition must disclose AI use.",
            "Art. 71": "Penalties: up to EUR 35M or 7% of global turnover for prohibited practices; EUR 15M or 3% for other violations.",
        },
    },
    "NIST_AI_RMF": {
        "full_name": "NIST AI Risk Management Framework 1.0",
        "jurisdiction": "United States (voluntary framework)",
        "effective": "2023-01-26",
        "key_articles": {
            "GOVERN": "Establish AI governance: policies, roles, culture of risk management.",
            "MAP": "Map AI risks: context, stakeholders, potential impacts.",
            "MEASURE": "Measure AI risks: metrics, testing, evaluation methods.",
            "MANAGE": "Manage AI risks: prioritize, respond, monitor over time.",
        },
    },
}

PENALTY_TABLE: dict[str, list[dict]] = {
    "GDPR": [
        {"tier": "Lower", "max_amount": "EUR 10M or 2% of global turnover", "applies_to": "Art. 8, 11, 25-39, 42-43 violations"},
        {"tier": "Upper", "max_amount": "EUR 20M or 4% of global turnover", "applies_to": "Art. 5, 6, 7, 9, 12-22, 44-49 violations"},
    ],
    "CCPA": [
        {"tier": "Unintentional", "max_amount": "$2,500 per violation", "applies_to": "General non-compliance"},
        {"tier": "Intentional", "max_amount": "$7,500 per violation", "applies_to": "Intentional violations"},
        {"tier": "Data breach (private action)", "max_amount": "$100-$750 per consumer per incident", "applies_to": "Sec. 1798.150 — security breach"},
    ],
    "EU_AI_ACT": [
        {"tier": "Prohibited practices", "max_amount": "EUR 35M or 7% of global turnover", "applies_to": "Art. 5 violations"},
        {"tier": "High-risk non-compliance", "max_amount": "EUR 15M or 3% of global turnover", "applies_to": "Other obligations"},
        {"tier": "Incorrect information", "max_amount": "EUR 7.5M or 1% of global turnover", "applies_to": "Supplying incorrect info to authorities"},
    ],
}

AI_RISK_LEVELS: dict[str, dict] = {
    "unacceptable": {
        "description": "Banned AI practices — clear threat to safety, rights, or values.",
        "examples": ["Social scoring by governments", "Real-time biometric identification in public spaces", "Subliminal manipulation", "Exploitation of vulnerabilities (age, disability)"],
        "action": "PROHIBITED — must not be deployed in the EU.",
    },
    "high": {
        "description": "AI systems with significant impact on health, safety, or fundamental rights.",
        "examples": ["Credit scoring", "Employment screening/hiring", "Critical infrastructure management", "Law enforcement predictive policing", "Education admission/grading", "Medical device AI"],
        "action": "ALLOWED with strict requirements: risk management, data governance, transparency, human oversight, CE marking.",
    },
    "limited": {
        "description": "AI systems with specific transparency obligations.",
        "examples": ["Chatbots", "Emotion recognition systems", "Deepfake generators", "Biometric categorization"],
        "action": "ALLOWED — must disclose AI usage to users.",
    },
    "minimal": {
        "description": "AI systems posing minimal risk — most AI falls here.",
        "examples": ["Spam filters", "AI-powered video games", "Inventory management", "Recommendation engines"],
        "action": "ALLOWED — no specific obligations, codes of conduct encouraged.",
    },
}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@tool
def lookup_regulation(regulation: str, article: str | None = None) -> str:
    """Look up a data privacy or AI regulation and optionally a specific article.

    Args:
        regulation: Regulation key: 'GDPR', 'CCPA', 'EU_AI_ACT', or 'NIST_AI_RMF'.
        article: Optional specific article (e.g., 'Art. 5', 'Sec. 1798.100').
    """
    reg = REGULATIONS_DB.get(regulation.upper().replace(" ", "_"))
    if not reg:
        available = ", ".join(REGULATIONS_DB.keys())
        return f"Regulation '{regulation}' not found. Available: {available}"

    if article:
        text = reg["key_articles"].get(article)
        if text:
            return (
                f"[{reg['full_name']}]\n"
                f"{article}: {text}"
            )
        available_arts = ", ".join(reg["key_articles"].keys())
        return f"Article '{article}' not found in {regulation}. Available: {available_arts}"

    articles_summary = "\n".join(
        f"  {k}: {v[:80]}..." for k, v in reg["key_articles"].items()
    )
    return (
        f"{reg['full_name']}\n"
        f"Jurisdiction: {reg['jurisdiction']}\n"
        f"Effective: {reg['effective']}\n\n"
        f"Key articles:\n{articles_summary}"
    )


@tool
def check_penalty(regulation: str, violation_type: str | None = None) -> str:
    """Check potential penalties for non-compliance with a regulation.

    Args:
        regulation: Regulation: 'GDPR', 'CCPA', or 'EU_AI_ACT'.
        violation_type: Optional filter (e.g., 'upper', 'intentional', 'prohibited').
    """
    reg_key = regulation.upper().replace(" ", "_")
    penalties = PENALTY_TABLE.get(reg_key)
    if not penalties:
        available = ", ".join(PENALTY_TABLE.keys())
        return f"No penalty data for '{regulation}'. Available: {available}"

    if violation_type:
        vt_lower = violation_type.lower()
        filtered = [p for p in penalties if vt_lower in p["tier"].lower()]
        if filtered:
            penalties = filtered

    lines = [f"Penalties under {regulation}:\n"]
    for p in penalties:
        lines.append(
            f"  [{p['tier']}]\n"
            f"    Max: {p['max_amount']}\n"
            f"    Applies to: {p['applies_to']}\n"
        )
    return "\n".join(lines)


@tool
def assess_ai_risk_level(system_description: str) -> str:
    """Assess the EU AI Act risk level for an AI system based on its description.

    Args:
        system_description: Description of the AI system (purpose, domain, impact).
    """
    desc_lower = system_description.lower()

    # Check for unacceptable risk keywords
    unacceptable_kw = ["social scoring", "subliminal", "manipulation", "exploit vulnerab"]
    if any(kw in desc_lower for kw in unacceptable_kw):
        level = "unacceptable"
    # Check for high risk keywords
    elif any(kw in desc_lower for kw in [
        "credit scor", "hiring", "recruitment", "employment", "medical", "health",
        "critical infrastructure", "law enforcement", "predictive policing",
        "education", "grading", "admission", "biometric identification",
        "border control", "immigration", "judicial",
    ]):
        level = "high"
    # Check for limited risk keywords
    elif any(kw in desc_lower for kw in [
        "chatbot", "deepfake", "emotion recognition", "synthetic media",
        "biometric categorization",
    ]):
        level = "limited"
    else:
        level = "minimal"

    info = AI_RISK_LEVELS[level]
    examples = "\n".join(f"    - {e}" for e in info["examples"])

    return (
        f"AI Risk Assessment (EU AI Act)\n"
        f"{'='*40}\n"
        f"System: {system_description[:100]}\n"
        f"Risk Level: {level.upper()}\n\n"
        f"Description: {info['description']}\n\n"
        f"Action Required: {info['action']}\n\n"
        f"Similar systems:\n{examples}"
    )


@tool
def generate_compliance_checklist(
    regulation: str,
    processing_type: str = "general",
) -> str:
    """Generate a compliance checklist for a specific regulation and processing type.

    Args:
        regulation: Regulation: 'GDPR', 'CCPA', or 'EU_AI_ACT'.
        processing_type: Type of processing: 'general', 'ai_system', 'data_collection', 'cross_border'.
    """
    checklists = {
        ("GDPR", "general"): [
            "Identify lawful basis for each processing activity (Art. 6)",
            "Implement data protection by design and by default (Art. 25)",
            "Maintain records of processing activities (Art. 30)",
            "Conduct Data Protection Impact Assessment if high-risk (Art. 35)",
            "Appoint a Data Protection Officer if required (Art. 37)",
            "Establish data breach notification procedures — 72h to authority (Art. 33)",
            "Provide clear privacy notices to data subjects (Art. 13/14)",
            "Implement data subject rights mechanisms (access, erasure, portability)",
            "Ensure processor agreements include required clauses (Art. 28)",
            "Review cross-border transfer mechanisms (SCCs, adequacy decisions)",
        ],
        ("GDPR", "ai_system"): [
            "Conduct DPIA for automated decision-making with legal effects (Art. 35)",
            "Ensure right to human review of automated decisions (Art. 22)",
            "Document logic, significance, and consequences of profiling",
            "Implement data minimization in training data (Art. 5.1.c)",
            "Validate training data accuracy and representativeness",
            "Provide meaningful information about automated decision logic (Art. 13.2.f)",
            "Enable data subjects to contest automated decisions",
            "Establish regular model auditing and bias testing procedures",
        ],
        ("EU_AI_ACT", "ai_system"): [
            "Classify AI system risk level (Art. 6, Annex III)",
            "If high-risk: implement risk management system (Art. 9)",
            "Ensure training data quality, relevance, and representativeness (Art. 10)",
            "Create and maintain technical documentation (Art. 11)",
            "Implement logging and traceability (Art. 12)",
            "Ensure transparency — users can interpret system output (Art. 13)",
            "Design for effective human oversight (Art. 14)",
            "Achieve appropriate accuracy, robustness, and cybersecurity (Art. 15)",
            "Register in EU database for high-risk AI (Art. 49)",
            "Appoint authorized representative if outside EU (Art. 25)",
            "Implement post-market monitoring system (Art. 61)",
        ],
        ("CCPA", "general"): [
            "Update privacy policy with required CCPA disclosures",
            "Implement 'Do Not Sell or Share My Personal Information' link (Sec. 1798.135)",
            "Establish consumer request intake and verification process",
            "Respond to consumer requests within 45 days (extendable once by 45 days)",
            "Implement reasonable security measures to protect personal information",
            "Review and update data processing agreements with service providers",
            "Maintain records of consumer requests for 24 months",
            "Train employees handling consumer inquiries on CCPA requirements",
        ],
    }

    key = (regulation.upper().replace(" ", "_"), processing_type.lower())
    checklist = checklists.get(key)

    if not checklist:
        available = [f"{r} / {t}" for (r, t) in checklists.keys()]
        return (
            f"No checklist for '{regulation}' / '{processing_type}'.\n"
            f"Available: {', '.join(available)}"
        )

    items = "\n".join(f"  [ ] {i+1}. {item}" for i, item in enumerate(checklist))
    return (
        f"Compliance Checklist: {regulation} ({processing_type})\n"
        f"{'='*50}\n\n"
        f"{items}\n\n"
        f"Note: This checklist is for guidance only. Consult a qualified legal\n"
        f"professional for compliance advice specific to your organization."
    )


@tool
def calculate_deadline(
    event_type: str,
    event_date: str,
) -> str:
    """Calculate regulatory deadlines from a given event date.

    Args:
        event_type: Type: 'gdpr_breach_notify', 'gdpr_dsar', 'ccpa_request', 'ccpa_opt_out'.
        event_date: Date of the event in YYYY-MM-DD format.
    """
    deadlines = {
        "gdpr_breach_notify": ("GDPR breach notification to authority", 3, "Art. 33 — 72 hours from discovery"),
        "gdpr_dsar": ("GDPR Data Subject Access Request response", 30, "Art. 12.3 — 1 month, extendable by 2 months"),
        "ccpa_request": ("CCPA consumer request response", 45, "Sec. 1798.130 — 45 days, extendable once by 45 days"),
        "ccpa_opt_out": ("CCPA opt-out request processing", 15, "Sec. 1798.135 — 15 business days"),
    }

    info = deadlines.get(event_type)
    if not info:
        available = ", ".join(deadlines.keys())
        return f"Unknown event type '{event_type}'. Available: {available}"

    name, days, basis = info
    try:
        dt = datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError:
        return "Invalid date format. Use YYYY-MM-DD."

    due = dt + timedelta(days=days)
    today = datetime.now()
    remaining = (due - today).days

    status = f"ON TIME ({remaining} days remaining)" if remaining > 0 else "OVERDUE"

    return (
        f"{name}\n"
        f"  Event date: {event_date}\n"
        f"  Deadline: {days} days\n"
        f"  Due by: {due.strftime('%Y-%m-%d')}\n"
        f"  Status: {status}\n"
        f"  Legal basis: {basis}"
    )


# Export all tools for agent registration
all_tools = [
    lookup_regulation,
    check_penalty,
    assess_ai_risk_level,
    generate_compliance_checklist,
    calculate_deadline,
]
