# Dimension 05: Governance & Trust Layer — Memory Log

## Scope
Proof chains, evidence anchoring, mandate model (Human→System→Agent), ZKP integration points, audit trails, security policies. Covers regulatory compliance and agent governance only. No business semantics; no infra topology beyond what's needed for trust verification.

---

## Current State (2026-05-21)
Session recovered from git history + research artifacts after restart wipe. Full proof registry spec (§3), agentic mandate model (§4), and ZKP integration points (§7) exist in Architecture.md (~29KB). Impact analysis covers storage growth risks, hash chain latency concerns, and seeding strategy gaps.

### Proof Registry Design (§§3 — Committed):
**Core principles:** Append-only (never updated/deleted), event-sourced (current state derived from replay not status field read), channel-aware (captures how intent was expressed: document/digital/API/agent), authority-linked (links to entitlement graph validating actor's right at time of action).

#### Proof Type Taxonomy (§3.2):
| Type | Description | Example |
|------|-------------|---------|
| `DECLARATIVE` | Human intent via formal instrument | Signed agreement, board resolution, mandate form |
| `BEHAVIOURAL` | Intent expressed through authenticated action | Portal click-through, self-service confirmation with consent capture + UI interaction hash |
| `DELEGATED` | Authority chain from human to system | OAuth token scope extraction, API credential, power of attorney |
| `AGENTIC` | Non-human acting under granted authority | AI agent action under scoped mandate; requires delegationChain[] and decisionTrace{} |
| `SYSTEMIC` | Bank's own execution record | Audit log, transaction record, config snapshot |
| `REGULATORY` | Third-party attestation | LEI registry, sanctions screening, credit bureau response |

#### Proof Chain Schema (§3.3):
- Every edge has exactly one proof chain containing 1+ append-only records with monotonic sequence numbering within chain
- Cryptographic integrity: SHA-256 hash per record + `previousHash` forming tamper-evident linked list — no gaps allowed in the chain

#### Authority Basis Types (§3.4):
```
signing_authority → board resolution, signing mandate
power_of_attorney → legal delegation document  
oauth_scope       → API credential scope (e.g., ["accounts:read", "payments:initiate"])
entitlement_role  → portal RBAC role assignment
agent_mandate     → human-to-agent scoped delegation
regulatory_role   → court-appointed, regulatory-assigned authority
```

### Agentic Mandate Model (§4 — Committed):
Three-tier hierarchy with mandatory complete delegation chain:
1. **HumanMandate** (root) — issued by NaturalPerson w/ signing authority; governs automation categories permitted; e.g., Treasury Automation Policy
2. **SystemMandate** (intermediate) — delegated from HumanMandate; governs which systems may act under human mandate
3. **AgentMandate** (execution) — delegated from SystemMandate; defines `permittedOperations[]`, `limits{}`, `constraints[]`; version-specific to agent

#### Scope Violation Handling (§4.3):
1. Action blocked BEFORE execution (pre-flight, not post-hoc detection) via `/mandates/{agentId}/validate` endpoint on critical path — must meet sub-millisecond latency alongside entitlement store (<5ms target)
2. `ScopeViolation` event appended to proof chain; mandate auto-suspended pending review
3. Alert raised to human mandate owner regardless of action completion

**Invariant:** No agent action executes without valid, non-expired AgentMandate with intact delegation chain (§10 invariant #3).

### ZKP Integration Points (§7):
Used where claim must be verified WITHOUT exposing underlying evidence:

| Claim | What Proven (public) | What Hidden from public inputs |
|-------|---------------------|-------------------------------|
| "Agent acted within mandate" | Action was in permitted scope at execution time | Full scope definition, client treasury policy details |
| "Entity not sanctioned" | Screening performed and passed | Which lists checked, client PII data |
| "Counterparty has valid KYC" | Completed, current, within policy | Documentation contents |
| "Ownership chain verified" | Each link in UBO chain has valid proof | Intermediate ownership percentages |

**Open question:** Proof system choice (Groth16 vs PLONK vs STARKs) deferred with no evaluation criteria — Phase 4 blocker but doesn't block earlier phases since opt-in per record. Should start vendor/library research now given bank procurement cycles of 6-12 months.

### Security Model Layers (§7 impact analysis):
1. **Append-only enforcement** via `delta.appendOnly = true` + CHECK constraints on proof chain refs — prevents direct mutation even by privileged users outside API path
2. **Row-Level Security** via `domain_scope ARRAY<STRING>` filtering with dynamic LOB context resolution (`array_contains(domain_scope, caller_lob)`)
3. **Column-level masking** on sensitive fields (intent_payload, signature visible only to auditor roles; raw table access restricted by Unity Catalog grants per schema for separation of duties)
4. **Temporal auditability** — full point-in-time reconstruction from append-only event history satisfies regulatory examination without separate archive system

## Key Decisions Captured in Spec (§10 Invariants):
- No edge write without atomic ProofChain creation + at least one ProofRecord; API rejects payload-less writes (invariant #1)
- Every proof record must reference valid AuthorityBasis active at `assertedAt` time — reject if authority not valid at assertion moment (#2)  
- Expired/suspended/missing mandate blocks execution, doesn't warn (#3)
- No status field mutations allowed; state always derived from event replay (#4)
- Graph + proof registry are append-only forever: terminated relationships remain queryable, invalid proofs get PROOF_INVALIDATED appended not deleted (#5)

## Open Questions / Critical Risks (from impact analysis):
1. 🔴 **No initial seeding strategy** — how to populate millions of existing entities/relationships into append-only tables while creating valid proof chains for legacy relationships lacking digital evidence? Needs migration runbook + exception handling when historical proofs cannot be constructed (`proof_chain_integrity_rate` and `kyc_reuse_rate` metrics will fail until resolved)
2. 🔴 **Unbounded storage growth** — every relationship change generates append-only records with full intent payloads containing potentially large JSON blobs; at TB scale (millions of edges × multiple proof events per edge), no partitioning scheme beyond Liquid Clustering columns, no retention policy or lifecycle management for aged records defined yet
3. 🟡 **Conflict resolution workflow** — when two proof records assert conflicting claims about same edge, what's the escalation path and who has resolution authority? (Open Q #1 in spec)
4. 🟡 **Proof expiry vs relationship expiry** — if Banking Agreement expires but no termination event recorded, does relationship auto-terminate or stay active pending explicit termination proof? (Open Q #2 in spec)
