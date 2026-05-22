# Global Transaction Banking — Data Strategy

**Executive Summary**
**Date:** 2026-05-22
**Client:** Top 10 North American Bank
**Reference Implementation:** Nexus Global

---

## 1. The Problem

Global Transaction Banking operates across three lines of business — Commercial Banking, Cash Management, and Wealth Management — each with its own systems, data models, and client views. The result:

- A corporate client with relationships in all three LOBs is invisible as a single entity. Relationship managers navigate three separate systems to understand one client.
- KYC is duplicated across LOBs. Onboarding costs are 3× what they should be because no LOB reuses another's completed due diligence.
- Regulatory reporting is manual quarter-end reconciliation. There is no consolidated counterparty view across CB, CM, and Wealth.
- Vendor-hosted products (Trade Finance, Supply Chain Finance) operate in semantic isolation — their data cannot be joined to core banking data without fragile point-to-point integrations.
- Automation (agentic operations) has no trusted foundation. AI agents operating on fragmented data produce unreliable outputs with no auditable authority chain.

**The root cause is not a technology problem. It is an ontology problem.** The bank has data but no shared model of what that data means, how entities relate, or what operations are permitted against them.

---

## 2. The Strategy: Ontology-First, Proof-Backed

This strategy has two pillars that together differentiate it from any off-the-shelf platform:

### Pillar 1 — Ontology as the Operational Interface

The canonical graph is not a data warehouse or a semantic layer. It is **the operational interface through which the bank acts on its data**. Borrowed from the Palantir Foundry pattern but adapted for banking:

- **Noun + Verb integration.** The ontology declares not just what exists (entities, relationships, products) but what can be done (actions, functions, governance modes). An action to execute an FX forward or draw down an intercompany facility is a first-class ontology construct — not an undocumented API behavior.
- **Single source of truth.** Every system — CB, CM, Wealth, vendor platforms — consumes read-only projections from the ontology. No system writes to canonical data except through the Entity Platform API. This eliminates schema drift and projection inconsistency.
- **Polymorphic contracts.** Interfaces (`IHasBalance`, `IIsSettlementTarget`, `IIsPoolMember`) enable cross-type queries and actions without enumerating concrete types. A payment initiation action accepts `IIsSettlementTarget` — it works against OperatingAccount, TradingAccount, or CustodyAccount without code changes.

### Pillar 2 — Proof as the Trust Foundation

Palantir has operational audit logs. We need **regulatory-grade evidentiary chains**. This is our differentiator:

- Every relationship in the graph has an append-only proof chain with SHA-256 hash chaining — tamper-evident from first assertion.
- Every proof record is authority-linked — it captures not just what happened, but who had the right to make it happen, at what time, under what mandate.
- Six proof types cover the full spectrum of banking evidence: declarative (signed agreements), behavioural (portal actions), delegated (API credentials), agentic (AI under mandate), systemic (execution records), regulatory (third-party attestations).
- A three-tier mandate hierarchy (Human → System → Agent) ensures every automated action has a complete, verifiable delegation chain back to a human with signing authority.

**The result:** When an OSFI, FinCEN, or FCA examiner asks "show me the evidentiary chain for this counterparty relationship," we can reconstruct not just what the relationship was, but why it was valid, who authorized it, and what authority backed that authorization — at any point in time.

---

## 3. Architecture at a Glance

```
                    ┌──────────────────────────────────────┐
                    │           ONTOLOGY                    │
                    │  Objects · Links · Actions · Functions│
                    │  Interfaces · Governance · Mandates   │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │       ENTITY PLATFORM API             │
                    │    (sole interface to canonical)      │
                    └───┬──────┬──────────┬──────────┬─────┘
                        │      │          │          │
               ┌────────▼───┐ ┌▼────────┐ ┌▼─────────┐ ┌▼──────────┐
               │   Neo4j    │ │PostgreSQL│ │  Redis   │ │ Delta Lake│
               │            │ │          │ │          │ │           │
               │ Graph      │ │ Kinetic  │ │ Hot      │ │ Analytics │
               │ traversal  │ │ + Proof  │ │ cache    │ │ + History │
               │ <5ms p99   │ │ ACID     │ │ <1ms     │ │ CDC mirror│
               └────────────┘ └──────────┘ └──────────┘ └───────────┘
```

| Store | Role | Why |
|-------|------|-----|
| **Neo4j** | Operational graph traversal | Native multi-hop queries (ownership chains, beneficial owners, regulatory exposure) at <5ms p99. No other store does this well. |
| **PostgreSQL** | Kinetic engine + proof registry | ACID transactions for the two-phase write state machine. Append-only proof records with hash chaining. Mandate validation at <1ms. |
| **Azure Cache for Redis** | Hot operational cache | Entitlements, active mandates, interface implementations. Write-through invalidation. Never source of truth. |
| **Delta Lake (Databricks)** | Analytics + temporal history | CDC-synced mirror (<5s lag) of operational stores. Unity Catalog governance. LOB projections. Regulatory reporting. Never the source of truth for current state. |

---

## 4. What This Enables

### For Relationship Managers
- **Single client view across LOBs.** One query shows every product, account, obligation, and relationship for a corporate client — regardless of which LOB owns the data.
- **KYC reuse.** When a client onboards for a second product, existing KYC proof chains are reused. Target: >80% KYC reuse rate.
- **Onboarding cycle time.** From first application to first active product. Target: <5 days (down from current multi-week process).

### For Compliance & Risk
- **Beneficial ownership resolution.** Multi-hop ownership chain traversal with full proof chains for every link. No manual spreadsheet reconciliation.
- **Regulatory examination readiness.** Any historical graph state reconstructable via point-in-time queries. Full evidentiary chains for every relationship.
- **Consolidated counterparty view.** Cross-LOB exposure visible in real time, not at quarter-end.

### For Treasury & Operations
- **Automated cash pool sweeps.** Agent-initiated, mandate-governed, proof-backed. Sub-millisecond mandate validation on the critical path.
- **FX execution with governance.** Forward contracts executed with pre-flight rule validation (mandate limits, aggregate exposure, permitted pairs) and automatic proof record creation.
- **Intercompany lending with oversight.** Drawdowns execute immediately but trigger async compliance review. If review fails, compensating action reverses the transaction.

### For Vendor Integration
- **Containment Zone.** Vendor-hosted products (Trade Finance, Supply Chain Finance) land in an isolated semantic buffer. Progressive mapping lifts signal upward to canonical ontology terms over time. No fragile point-to-point transformations.

---

## 5. The Kinetic Layer — What Makes It Operational

The ontology is not a static data model. Three constructs make it actionable:

### Interfaces (Polymorphism)
Eight defined interfaces enable cross-type operations. Example: `IIsSettlementTarget` is implemented by OperatingAccount, TradingAccount, and CustodyAccount. A payment action accepts the interface — not a concrete type — so it works across account types without code duplication.

### Action Types (Declared Operations)
Seven defined action types cover core GTB operations:

| Action | Governance Mode | Example |
|--------|----------------|---------|
| `AssertRelationship` | PROPOSED | New counterparty relationship requires compliance review |
| `InitiatePayment` | IMMEDIATE | Time-critical; executes with pre-flight sanctions check |
| `ExecuteFXForward` | IMMEDIATE | Market execution; mandate-governed |
| `DrawdownIntercompanyFacility` | REVIEWED | Executes immediately, async compliance review, compensating action on failure |
| `InitiatePoolSweep` | IMMEDIATE | Intraday liquidity management |
| `ApproveKYCRenewal` | IMMEDIATE | Compliance officer approval is final |
| `ReviewRelationshipProposal` | IMMEDIATE | Approve/reject pending relationship assertions |

### Functions (Versioned Business Logic)
Six defined functions encode critical business logic as auditable, versioned constructs:
- `deriveEdgeState` — derives current relationship state from proof chain replay
- `validateMandateScope` — pre-flight agent mandate validation (<1ms)
- `computeProductEligibility` — KYC, sanctions, and product-specific checks
- `computeSigningAuthority` — tiered signing limits (solo/dual/board)
- `computePoolInterest` — daily interest posting for cash pools
- `validateTransferPricing` — arm's-length pricing for intercompany transactions

---

## 6. Governance & Trust

### Proof Chain Integrity
- Append-only enforcement (no updates, no deletions)
- SHA-256 hash chaining between records (tamper-evident)
- 15-minute integrity sweep validates chain continuity
- Current state derived from event replay — never from a status field

### Agentic Mandate Model
- Three-tier hierarchy: HumanMandate → SystemMandate → AgentMandate
- Complete delegation chain required for every agent action
- Pre-flight scope validation blocks execution (does not warn)
- Scope violations auto-suspend the mandate and alert the human owner

### Zero-Knowledge Proofs (Phase 4)
Four use cases where claims are verified without exposing underlying evidence:
- "Agent acted within mandate" — proven without revealing full scope definition
- "Entity not sanctioned" — proven without revealing which lists were checked
- "Counterparty has valid KYC" — proven without revealing documentation contents
- "Ownership chain verified" — proven without revealing intermediate ownership percentages

### Security Layers
1. Append-only enforcement at storage layer
2. Row-Level Security via `domain_scope` (enforced at SQL and API layers)
3. Column-level masking on sensitive proof fields (auditor-only visibility)
4. Temporal auditability — full point-in-time reconstruction

---

## 7. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Graph store | **Neo4j** | Native graph traversal for multi-hop queries. No alternative matches <5ms p99 for ownership chains and beneficial ownership resolution. |
| Proof registry | **PostgreSQL** (not QLDB) | Co-located with kinetic layer for cross-store consistency. Team familiarity. Azure-native managed service. Hash chain provides equivalent cryptographic integrity. |
| Analytical layer | **Databricks + Delta Lake** | Locked. Unity Catalog governance. Time-travel for point-in-time queries. CDC-synced from operational stores. |
| Hot cache | **Azure Cache for Redis** | Sub-millisecond mandate validation and entitlement checks. Write-through invalidation. |
| API contract | **Ontology action surface** | Endpoints map to declared Action Types, not generic CRUD. Pre-flight rules, governance modes, and proof requirements are part of the contract. |

---

## 8. Reference Client: Nexus Global

All examples, volume estimates, and validation scenarios are grounded in the Nexus Global reference client:

- **Corporate structure:** Nexus Global (Canada) → Nexus Global USA → Nexus Global USA-East; Nexus Global UK Ltd
- **Jurisdictions:** Canada (FINTRAC/OSFI), United States (FinCEN/Fedwire), United Kingdom (FCA/CHAPS)
- **Product catalog:** FX Forward (CAD), FX Hedge (GBP), DDA, Trade Finance (vendor-hosted), Supply Chain Finance (vendor-hosted)
- **Cash pool:** Multi-currency pool with USA-East (35.5%), Canada (23.2%), and remaining participants
- **Year 1 scale:** ~28K graph nodes, ~62K edges, ~188K proof records, ~1GB total storage across all stores

---

## 9. Delivery Plan

| Phase | Duration | Scope |
|-------|----------|-------|
| **Phase 1 — Foundation** | Weeks 1–6 | Graph store + proof registry schema. Core node/edge types. Append-only enforcement. Basic Entity Platform API. Relationship lifecycle state machine. |
| **Phase 2 — Proof Channels** | Weeks 7–10 | All six proof type handlers. Point-in-time query support. LOB projection deployment. API non-functional requirements (rate limiting, pagination, circuit breakers). |
| **Phase 3 — Projections** | Weeks 11–14 | Unity Catalog deployment. CB operational projection. Entitlement store (<5ms). Cross-LOB analytical view. Canonical KPIs. |
| **Phase 4 — Agentic Layer** | Weeks 15–18 | Mandate model. Delegation chain validation. Pre-flight scope API. Scope violation detection. ZKP integration points. |

---

## 10. Open Risks

| Risk | Severity | Status |
|------|----------|--------|
| Cross-store transaction consistency | 🟠 | Saga pattern designed; implementation needed before Phase 1 |
| Vendor API contracts (Trade Finance + Supply Chain Finance) | 🔴 | Schemas unknown; blocks vendor integration design |
| Initial seeding strategy | 🟠 | Legacy data migration runbook needed |
| Neo4j team readiness | 🟠 | Training plan required |
| CDC sync latency (<5s target) | 🟠 | Benchmarking needed |
| Business rule engine selection | 🟡 | Lightweight expression engine recommended for Phase 1 |
| Hash chain batch computation | 🟡 | Benchmark needed for ~188K initial records |

---

## 11. What This Is Not

This strategy is **not**:
- A data lake initiative. Delta Lake is a mirror, not the source of truth.
- A knowledge graph for analytics. The graph is operational — it governs actions, not just answers queries.
- A Palantir Foundry clone. We adopt the noun+verb pattern and ontology-first discipline, but retain our proof-based evidentiary system which Palantir lacks.
- A replacement for LOB systems. CB, CM, and Wealth operational databases continue to serve their domains. The ontology unifies them through projections, not consolidation.

---

## 12. What Success Looks Like

| Metric | Target |
|--------|--------|
| Cross-LOB client visibility | 100% of clients with >1 LOB relationship visible as single entity |
| KYC reuse rate | >80% of new subscriptions reuse existing proof chains |
| Onboarding cycle time | <5 days from application to first active product |
| Payment straight-through processing | >95% |
| Proof chain integrity rate | 100% of active edges have valid, non-expired proof chains |
| Entitlement provisioning time | <4 hours from request to active access |
| Agent mandate validation latency | <1ms p99 on critical path |

---

*This document summarizes the five-dimension architecture specification. Detailed specs are in `artifacts/dimensions/`. All artifacts are version-controlled in GitHub.*
