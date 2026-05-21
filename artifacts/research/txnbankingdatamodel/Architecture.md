# Transaction Banking — Canonical Graph & Proof Registry
## Architecture Specification for Implementation

---

## 1. What We Are Building

A **temporally versioned, evidence-anchored knowledge graph** for Global Transaction Banking.

Two inseparable systems:

1. **The Canonical Graph** — every entity, product, account, transaction, and channel relationship that exists in GTB, modelled as nodes and edges
2. **The Proof Registry** — for every edge in the graph, an immutable, append-only record of the evidence that proves the relationship is true

The graph answers: *what is the current state of the world?*  
The Proof Registry answers: *why is it true, and how do we know?*

Neither is complete without the other. An edge with no proof chain is an unverified assertion. A proof record with no graph edge is an orphaned document.

### Core Architectural Rule

> Materialisation is always derived from the graph. The graph is never derived from the materialisation.

Operational databases (CB, CM, Wealth) are projections of the canonical graph. The graph is the source of truth. Databases are read-optimised views shaped by LOB exposure and organisational structure.

---

## 2. The Canonical Graph

### 2.1 Node Types

```
Node
├── Party
│   ├── LegalEntity
│   │   ├── Corporation
│   │   ├── Partnership
│   │   ├── Trust
│   │   └── Sovereign
│   ├── NaturalPerson
│   ├── FinancialInstitution
│   └── Regulator
├── EntityGroup
│   ├── UltimateParent
│   └── ConsolidatedGroup
├── Product
│   ├── ProductDefinition
│   ├── ProductInstance
│   └── ProductBundle
├── Account
│   ├── OperatingAccount
│   ├── VirtualAccount
│   ├── NotionalPool
│   ├── TradingAccount
│   └── CustodyAccount
├── Transaction
│   ├── Payment
│   ├── TradeTransaction
│   ├── FXTransaction
│   └── Fee
├── Channel
│   ├── DigitalPortal
│   ├── APIChannel
│   ├── H2HChannel
│   └── SWIFTChannel
├── Obligation
│   ├── RegulatoryObligation
│   ├── ContractualObligation
│   └── CreditObligation
└── Mandate
    ├── HumanMandate
    └── AgentMandate
```

### 2.2 Node Schema (base)

Every node regardless of type carries:

```typescript
interface GraphNode {
  id: string                    // UUID v4
  type: NodeType                // enum from taxonomy above
  lei?: string                  // Legal Entity Identifier — universal join key where applicable
  canonicalName: string         // unambiguous display name
  aliases: string[]             // known alternate names across LOB systems
  createdAt: ISO8601            // when node was first asserted in graph
  createdBy: ActorRef           // who or what created it
  state: NodeState              // Active | Suspended | Terminated | Disputed
  domainExtensions: {           // LOB-specific properties — never override canonical fields
    cb?: Record<string, unknown>
    cm?: Record<string, unknown>
    wm?: Record<string, unknown>
  }
  proofChainId: string          // foreign key into Proof Registry
}
```

### 2.3 Edge Types

```
Edge
├── Ownership
│   ├── owns                    // Party → owns → Account
│   ├── isSubsidiaryOf          // LegalEntity → isSubsidiaryOf → LegalEntity
│   ├── isUltimateParentOf      // LegalEntity → isUltimateParentOf → EntityGroup
│   └── hasBeneficialOwner      // LegalEntity → hasBeneficialOwner → NaturalPerson
├── Authority
│   ├── hasSigningAuthority     // NaturalPerson → hasSigningAuthority → LegalEntity
│   ├── hasAuthorisedRepresentative // LegalEntity → hasAuthorisedRepresentative → NaturalPerson
│   └── delegatesTo             // Actor → delegatesTo → Actor (scope-bounded)
├── Product
│   ├── isSubscribedTo          // Party → isSubscribedTo → ProductInstance
│   ├── isEligibleFor           // Party → isEligibleFor → ProductDefinition
│   └── isDeliveredThrough      // ProductInstance → isDeliveredThrough → Channel
├── Account
│   ├── isGovernedBy            // Account → isGovernedBy → ProductInstance
│   ├── hasBalance              // Account → hasBalance → Position
│   └── isPartOf                // Account → isPartOf → NotionalPool
├── Transaction
│   ├── settlesAgainst          // Transaction → settlesAgainst → Account
│   ├── initiatedBy             // Transaction → initiatedBy → Party
│   └── executedVia             // Transaction → executedVia → Channel
├── Regulatory
│   ├── isSubjectTo             // Party → isSubjectTo → RegulatoryObligation
│   ├── isKnownBy               // Party → isKnownBy → Regulator (KYC status)
│   ├── isScreenedAgainst       // Party → isScreenedAgainst → Regulator (sanctions)
│   └── reportsTo               // LegalEntity → reportsTo → Regulator (jurisdiction)
└── Agentic
    ├── operatesUnder           // AgentMandate → operatesUnder → HumanMandate
    └── wasExecutedBy           // Transaction → wasExecutedBy → AgentMandate
```

### 2.4 Edge Schema (base)

```typescript
interface GraphEdge {
  id: string                    // UUID v4
  type: EdgeType                // enum from taxonomy above
  fromNodeId: string            // source node
  toNodeId: string              // target node
  state: EdgeState              // Proposed | Verified | Active | Suspended | Terminated | Disputed
  effectiveFrom: ISO8601        // when relationship became true
  effectiveTo?: ISO8601         // null = no expiry
  createdAt: ISO8601
  createdBy: ActorRef
  proofChainId: string          // mandatory — no edge without proof chain
  domainScope: LOBScope[]       // CB | CM | WM | ALL — which LOBs this edge is visible to
}
```

### 2.5 Relationship Lifecycle

```
Proposed ──► Verified ──► Active ──► Suspended ──► Active  (reinstated)
                                         │
                                         └──────────► Terminated
                              
Any state ──► Disputed ──► Active  (resolved)
                       └──► Terminated  (invalidated)
```

**State transitions are always driven by proof chain events, never by direct field updates.**

A relationship is `Active` when its proof chain is complete and no link is expired or challenged.  
A relationship is `Suspended` when a proof chain link is under challenge or pending re-attestation.  
A relationship is `Terminated` when a proof of termination intent has been recorded and executed.  
A relationship is `Disputed` when conflicting proof records exist and resolution is pending.

---

## 3. The Proof Registry

### 3.1 Design Principles

- **Append-only.** Records are never updated or deleted. New records supersede old ones; old records remain.
- **Event-sourced.** Current proof state is derived by replaying the event chain, not reading a status field.
- **Channel-aware.** Every proof record captures how intent was expressed (document, digital action, API call, agent execution).
- **Authority-linked.** Every proof record links to the entitlement graph that validated the actor's right to act at the time of action.

### 3.2 Proof Type Taxonomy

```typescript
enum ProofType {
  // Human intent via formal instrument
  DECLARATIVE = "declarative",        // signed agreement, board resolution, mandate form

  // Intent expressed through authenticated action
  BEHAVIOURAL = "behavioural",        // portal click-through, self-service confirmation

  // Authority chain from human to system
  DELEGATED = "delegated",            // OAuth token, API credential, power of attorney

  // Non-human acting under granted authority
  AGENTIC = "agentic",               // AI agent action under scoped mandate

  // Bank's own execution record
  SYSTEMIC = "systemic",             // audit log, transaction record, config snapshot

  // Third-party attestation
  REGULATORY = "regulatory"          // LEI registry, sanctions screening, credit bureau
}
```

### 3.3 Proof Chain Schema

Every edge has exactly one proof chain. A proof chain contains one or more proof records.

```typescript
interface ProofChain {
  id: string                          // matches proofChainId on GraphEdge
  edgeId: string                      // the edge this chain proves
  currentState: ProofChainState       // derived from event replay — never set directly
  records: ProofRecord[]              // ordered append-only array
  integrityStatus: IntegrityStatus    // Valid | Challenged | Broken | Expired
}

interface ProofRecord {
  id: string                          // UUID v4
  chainId: string
  sequence: number                    // monotonically increasing within chain
  event: ProofEvent                   // what happened
  proofType: ProofType
  
  // Intent layer — what was wanted or authorised
  intentSummary: string               // human-readable description
  intentPayload: Record<string, unknown>  // structured capture of the expressed intent
  
  // Authority layer — who had the right to act
  actorId: string                     // the party or system that expressed intent
  actorType: ActorType                // Human | System | Agent
  authorityBasis: AuthorityBasis      // what gave them the right
  entitlementSnapshotId: string       // point-in-time snapshot of actor's entitlement at time of action
  
  // Execution layer — what the bank did
  executionRecord: ExecutionRecord    // what was done, by what system, with what outcome
  
  // Channel context
  channel: ChannelRef                 // how intent was expressed
  sessionRef?: string                 // authenticated session (digital/API channels)
  
  // Temporal
  assertedAt: ISO8601
  verifiedAt?: ISO8601
  expiresAt?: ISO8601
  
  // Cryptographic integrity
  hash: string                        // SHA-256 of record content
  previousHash: string                // hash of prior record — forms tamper-evident chain
  signature?: string                  // cryptographic signature where applicable
}

enum ProofEvent {
  PROOF_ASSERTED    = "proof_asserted",     // new proof submitted
  PROOF_VERIFIED    = "proof_verified",     // proof validated by authorised reviewer
  PROOF_SUPERSEDED  = "proof_superseded",   // replaced by newer proof
  PROOF_CHALLENGED  = "proof_challenged",   // validity disputed
  PROOF_RESOLVED    = "proof_resolved",     // challenge resolved
  PROOF_EXPIRED     = "proof_expired",      // temporal validity elapsed
  PROOF_INVALIDATED = "proof_invalidated"   // proof found to be false
}
```

### 3.4 Authority Basis Types

```typescript
interface AuthorityBasis {
  type: AuthorityBasisType
  reference: string             // document, token, or registry reference
  scope: string[]               // what actions this authority covers
  grantedBy: string             // who granted the authority
  grantedAt: ISO8601
  expiresAt?: ISO8601
}

enum AuthorityBasisType {
  SIGNING_AUTHORITY    = "signing_authority",    // board resolution, signing mandate
  POWER_OF_ATTORNEY    = "power_of_attorney",
  OAUTH_SCOPE          = "oauth_scope",          // API credential scope
  ENTITLEMENT_ROLE     = "entitlement_role",     // portal RBAC role
  AGENT_MANDATE        = "agent_mandate",        // human-to-agent delegation
  REGULATORY_ROLE      = "regulatory_role"       // court-appointed, regulatory-assigned
}
```

### 3.5 Proof by Channel

Each channel type produces structurally different proof. The schema accommodates all.

**Declarative (document-based):**
```typescript
{
  proofType: "declarative",
  intentPayload: {
    documentType: "BankingAgreement",
    documentRef: "BA-20240215-ACME",
    documentHash: "sha256:...",
    signatoryName: "Jon Acme",
    signatoryTitle: "Director",
    signatoryAuthorityRef: "BoardResolution-2023-04"
  }
}
```

**Behavioural (self-service portal):**
```typescript
{
  proofType: "behavioural",
  channel: { type: "DigitalPortal", portalId: "GTB-PORTAL-CA" },
  sessionRef: "sess_abc123",          // authenticated session
  intentPayload: {
    action: "AccountOpeningConfirmed",
    consentCapture: {
      termsVersion: "TOS-2024-v3",
      capturedAt: "2024-02-15T14:23:11Z",
      captureMethod: "explicit_checkbox"
    },
    uiInteractionHash: "sha256:..."   // tamper-evident record of what was presented
  }
}
```

**Delegated (API/H2H):**
```typescript
{
  proofType: "delegated",
  channel: { type: "APIChannel", apiVersion: "v2" },
  intentPayload: {
    credentialType: "OAuth2",
    clientId: "acme-erp-prod",
    scopeGranted: ["accounts:read", "payments:initiate"],
    instructionHash: "sha256:...",    // hash of the API request payload
    responseRef: "txn_xyz789"
  }
}
```

**Agentic (AI agent execution):**
```typescript
{
  proofType: "agentic",
  intentPayload: {
    agentId: "treasury-liquidity-agent-v2",
    mandateRef: "MANDATE-2024-ACME-TREASURY",   // root human mandate
    delegationChain: [                           // every step from human to execution
      { actor: "CFO Jon Acme", authorityBasis: "TreasuryPolicy-2024-v2", grantedAt: "..." },
      { actor: "Treasury System", authorityBasis: "SystemMandate-ACME-001", grantedAt: "..." },
      { actor: "treasury-liquidity-agent-v2", authorityBasis: "AgentScope-v2", grantedAt: "..." }
    ],
    scopeAtExecution: {
      permittedOperations: ["pool_restructure", "intraday_sweep"],
      limits: { maxAmount: 50000000, currency: "CAD" },
      constraints: ["no_external_transfer", "same_day_only"]
    },
    decisionTrace: {
      observedCondition: "Pool balance below threshold at 14:00",
      appliedRule: "AutoSweep-Rule-7",
      determinedAction: "Transfer CAD 12M from OpAccount to NotionalPool"
    },
    scopeViolations: [],                        // must be empty for valid proof
    zkpProof?: string                           // ZKP attestation that action was within scope
  }
}
```

---

## 4. The Agentic Mandate Model

Agentic flows require the longest authority chain and the strictest proof requirements.

### 4.1 Mandate Hierarchy

```
HumanMandate (root)
  └── issued by: NaturalPerson with signing authority
  └── governs: what categories of automation are permitted
  └── examples: Treasury Automation Policy, Payments Automation Mandate

  SystemMandate (intermediate)
    └── delegated from: HumanMandate
    └── governs: which systems may act under the human mandate
    └── examples: ERP Integration Mandate, Liquidity System Mandate

    AgentMandate (execution)
      └── delegated from: SystemMandate
      └── governs: what a specific agent may do, with what limits
      └── must define: permittedOperations[], limits{}, constraints[]
      └── must reference: parent SystemMandate → parent HumanMandate
```

### 4.2 Mandate Schema

```typescript
interface AgentMandate {
  id: string
  type: "AgentMandate"
  agentId: string                       // the agent this mandate governs
  agentVersion: string                  // mandate is version-specific
  
  // Delegation chain — must be complete and each link verified
  parentMandateId: string               // SystemMandate
  rootMandateId: string                 // HumanMandate
  delegationChain: DelegationLink[]
  
  // Scope — what is permitted
  permittedOperations: OperationType[]
  limits: OperationLimits
  constraints: Constraint[]
  
  // Validity
  effectiveFrom: ISO8601
  effectiveTo?: ISO8601
  state: MandateState                   // Active | Suspended | Revoked
  
  // Proof
  proofChainId: string                  // the mandate itself requires proof of authorisation
}
```

### 4.3 Scope Violation Handling

If an agent action falls outside mandate scope:

1. Action is **blocked before execution** — scope is checked pre-flight, not post-hoc
2. `ScopeViolation` event is appended to the proof chain
3. Mandate is automatically `Suspended` pending review
4. Alert is raised to mandate owner (human)
5. Audit record is created regardless of whether action completed

**No agent action executes without a valid, non-expired AgentMandate with intact delegation chain.**

---

## 5. Graph Projections (Operational & Analytical)

The canonical graph is never directly queried by applications. It is materialised into domain-specific projections.

### 5.1 Projection Types

```
CanonicalGraph
    │
    ├── Operational Projections (low latency, write-heavy, LOB-scoped)
    │   ├── cb_operational      — CB: Parties, Accounts, Payment Instructions
    │   ├── cm_operational      — CM: Counterparties, Positions, Trade Obligations  
    │   └── entitlement_store   — Party + Channel + Permission subgraph (<5ms access)
    │
    ├── Analytical Projections (read-heavy, cross-LOB, metric-bearing)
    │   ├── tb_canonical        — Unity Catalog: full GTB cross-LOB view
    │   ├── credit_exposure     — CRO view: Party + Obligation subgraph
    │   └── regulatory_view     — Reporting: Party + Regulator edges by jurisdiction
    │
    └── Proof Projections (compliance & audit)
        ├── point_in_time       — graph state at any historical timestamp
        └── evidentiary_chain   — full proof chain for any edge or entity
```

### 5.2 Projection Rule

A projection:
- **reads** from the canonical graph via the Entity Platform API
- **never writes back** to the canonical graph
- **carries a freshness timestamp** — staleness is explicit, never hidden
- **scopes by LOB exposure** — a CB projection never contains CM-only counterparty data

### 5.3 Unity Catalog Mapping

```
tb_canonical                              ← top-level catalog (Channels Technology owns)
├── tb_canonical.entity                   ← entity schema (Party, EntityGroup, KYC)
├── tb_canonical.product                  ← product schema (Definition, Instance, Bundle)
├── tb_canonical.account                  ← account schema (Operating, Virtual, Pool)
├── tb_canonical.transaction              ← transaction schema (Payment, Trade, FX)
├── tb_canonical.channel                  ← channel + entitlement schema
├── tb_canonical.proof                    ← proof chain summaries (not full registry)
└── tb_canonical.metrics                  ← canonical KPIs defined once

tb_cb                                     ← CB extensions (open, CB-owned)
tb_cm                                     ← CM extensions (open, CM-owned)
tb_wm                                     ← WM extensions (open, WM-owned)
```

### 5.4 Canonical Metrics

Defined once in `tb_canonical.metrics`. Consumed by all downstream tools.

| Metric | Definition | Target |
|--------|-----------|--------|
| `client_revenue_total` | Total revenue per LegalEntity across CB + CM + WM | — |
| `onboarding_cycle_time` | Days from first application to first active product | < 5 days |
| `product_adoption_rate` | % eligible clients subscribed per ProductDefinition | — |
| `entitlement_provisioning_time` | Hours from request to active access | < 4 hours |
| `cross_lob_client_count` | LegalEntities with active products in > 1 LOB | — |
| `kyc_reuse_rate` | % new subscriptions reusing existing KYC ProofChain | > 80% |
| `payment_stp_rate` | % payment instructions processed straight-through | > 95% |
| `proof_chain_integrity_rate` | % active edges with valid, non-expired proof chains | 100% |

---

## 6. The Entity Platform API

The only interface that queries the canonical graph directly. All other systems consume projections.

### 6.1 Core Endpoints

```
GET  /entities/{id}                        — resolve entity by canonical ID
GET  /entities/by-lei/{lei}               — resolve by LEI (universal join key)
GET  /entities/{id}/relationships          — all edges from this node (filtered by state)
GET  /entities/{id}/ownership-chain        — traverse to UltimateParent
GET  /entities/{id}/beneficial-owners      — UBO resolution
GET  /entities/{id}/regulatory-exposure   — Party + Regulator edges by jurisdiction

GET  /proof/{edgeId}                       — current proof chain summary for edge
GET  /proof/{edgeId}/full                  — complete evidentiary chain
GET  /proof/{edgeId}/at/{timestamp}        — point-in-time proof state

POST /relationships                        — assert new relationship (triggers proof chain creation)
POST /proof/{edgeId}/records               — append proof record to chain

GET  /mandates/{agentId}                   — active mandate for agent
POST /mandates/{agentId}/validate          — pre-flight scope check before agent action
```

### 6.2 Point-in-Time Query

All endpoints support `?asOf={timestamp}` parameter.

```
GET /entities/ACME-CORP/relationships?asOf=2023-03-01T00:00:00Z
```

Returns the relationship state as it existed at that timestamp, with proof chain state as of that date. This is the foundation of regulatory examination response — any historical state is reconstructable from the graph.

### 6.3 Entity Resolution Response

```typescript
interface EntityResolutionResponse {
  entity: GraphNode
  relationships: {
    active: GraphEdge[]
    suspended: GraphEdge[]
    // terminated not returned by default — use ?includeTerminated=true
  }
  proofSummary: {
    allChainsIntact: boolean
    chainCount: number
    oldestChainDate: ISO8601
    pendingVerifications: number
  }
  lob_visibility: LOBScope[]           // which LOBs caller is authorised to see
  asOf: ISO8601                        // effective timestamp of this response
}
```

---

## 7. ZKP Integration Points

Zero-Knowledge Proofs are used where the claim must be verified without exposing the underlying evidence.

### 7.1 Use Cases

| Claim | What Must Be Proven | What Must Not Be Revealed |
|-------|--------------------|--------------------------| 
| "This agent acted within mandate" | Action was within permitted scope at time of execution | Full scope definition, client treasury policy |
| "This entity is not sanctioned" | Sanctions screening was performed and passed | Which lists were checked, client data |
| "This counterparty has valid KYC" | KYC was completed, current, within policy | KYC documentation contents |
| "This ownership chain is verified" | Each link in UBO chain has valid proof | Intermediate ownership percentages |

### 7.2 ZKP Proof Record

```typescript
{
  proofType: "regulatory",
  intentPayload: {
    claim: "AgentActionWithinMandateScope",
    zkpProof: "zkp:groth16:...",          // the ZKP
    publicInputs: {
      agentId: "treasury-agent-v2",
      actionType: "pool_restructure",
      executionTimestamp: "2024-02-15T14:23:11Z",
      mandateActive: true,
      scopeViolations: 0
    }
    // The mandate definition, limits, and constraints are NOT in publicInputs
    // The ZKP proves the claim without revealing them
  }
}
```

---

## 8. Implementation Sequence

### Phase 1 — Foundation (Weeks 1–6)
Build the core graph store and proof registry schema. No projections yet.

- [ ] Graph database selection and setup (see Technology Options below)
- [ ] Node and Edge schema implementation with full type system
- [ ] Proof Registry append-only store with event sourcing
- [ ] ProofChain integrity validation (hash chain verification)
- [ ] Basic Entity Platform API — CRUD on nodes and edges
- [ ] Relationship lifecycle state machine
- [ ] Unit tests: every edge write requires proof chain record

### Phase 2 — Proof Channels (Weeks 7–10)
Implement proof ingestion for each channel type.

- [ ] Declarative proof handler (document reference + hash)
- [ ] Behavioural proof handler (session + consent capture)
- [ ] Delegated proof handler (OAuth token scope extraction)
- [ ] Agentic proof handler (mandate chain validation + decision trace)
- [ ] Systemic proof handler (execution record attachment)
- [ ] Point-in-time query support across all endpoints

### Phase 3 — Projections (Weeks 11–14)
Build the materialised views from the canonical graph.

- [ ] Unity Catalog schema deployment (tb_canonical + domain schemas)
- [ ] Canonical metrics definitions (7 core KPIs)
- [ ] CB operational projection
- [ ] Entitlement store projection (sub-5ms path)
- [ ] Cross-LOB analytical view (cross_lob_client_count working end-to-end)

### Phase 4 — Agentic Layer (Weeks 15–18)
Full mandate model and agentic proof handling.

- [ ] AgentMandate schema and lifecycle
- [ ] Delegation chain validation
- [ ] Pre-flight scope check API (`/mandates/{agentId}/validate`)
- [ ] Scope violation detection and mandate suspension
- [ ] ZKP proof record support (integration point — ZKP library TBD)

---

## 9. Technology Options

### Graph Store
| Option | Fit | Notes |
|--------|-----|-------|
| **Neo4j** | High | Native graph, mature Cypher query language, enterprise support |
| **Amazon Neptune** | High | Managed, supports both RDF and property graph, good for regulated environments |
| **Apache AGE** (Postgres extension) | Medium | Good if existing Postgres infrastructure, lower operational overhead |
| **Databricks + Delta Lake** | Medium | Better for analytical projections than operational graph traversal |

**Recommendation:** Neo4j for canonical graph store. Databricks for analytical projections. Connect via Entity Platform API — consuming systems never touch graph store directly.

### Proof Registry Store
The Proof Registry must be append-only with cryptographic integrity. Options:
- **PostgreSQL with insert-only policy + hash chain** — simplest, audit-friendly
- **Apache Kafka + compacted topics** — event-sourced naturally, high throughput
- **Amazon QLDB** — purpose-built immutable ledger, good regulatory narrative

**Recommendation:** QLDB for proof registry (immutable ledger is the right abstraction and simplifies regulatory examination conversations).

### Ontology Layer
- **OWL/RDF** for the formal ontology definition (FIBO-aligned)
- **JSON-LD** for API serialisation of graph data
- **Protobuf** for high-throughput internal messaging

---

## 10. Key Invariants

These rules must be enforced at the application layer. They are not suggestions.

1. **No edge without a proof chain.** Every `GraphEdge` write must atomically create a `ProofChain` and at least one `ProofRecord`. Reject any write that arrives without proof payload.

2. **No proof chain without an authority basis.** Every `ProofRecord` must reference a valid `AuthorityBasis` that was active at `assertedAt` time. Reject records where authority was not valid at assertion time.

3. **No agent action without a valid mandate.** Pre-flight mandate validation is not optional. An expired, suspended, or missing mandate blocks execution — it does not generate a warning.

4. **No status field updates.** Edge state and proof chain state are always derived from event replay. Direct state field mutation is rejected at the API layer.

5. **No deletions.** The graph and proof registry are append-only. Terminated relationships remain queryable. Invalid proof records remain with `PROOF_INVALIDATED` event appended.

6. **LEI as canonical identity.** Where a LegalEntity exists, LEI is the primary join key. LOB-internal identifiers are aliases, never canonicals.

7. **Projections never write to canonical.** Operational and analytical projections are read-only consumers of the canonical graph. Any attempt to write to the canonical graph must go through the Entity Platform API with full proof payload.

---

## 11. Open Questions for Implementation

These require decisions before Phase 1 completion:

1. **Conflict resolution workflow** — when two proof records assert conflicting claims about the same edge, what is the escalation path and who has resolution authority?

2. **Proof expiry vs. relationship expiry** — if a Banking Agreement expires but no termination event is recorded, does the relationship auto-terminate or remain active pending explicit termination proof?

3. **Inference-based edges** — how do we model relationships that are inferred from transaction patterns rather than proven by explicit instruments? What confidence threshold triggers a `Proposed` edge?

4. **Cross-jurisdictional regulatory nodes** — a single LegalEntity may have `isKnownBy` edges to OSFI, FinCEN, FCA, and MAS simultaneously. How do we model jurisdictional scope on regulatory edges?

5. **ZKP library selection** — Groth16 vs. PLONK vs. STARKs for agentic mandate proofs. Choice affects proof size, verification speed, and trusted setup requirements.

