# Entity Platform API — Ontology Action Surface

**Dimension:** 04 — API Integration Contract
**Date:** 2026-05-22
**Status:** Draft — ontology action surface (supersedes REST CRUD model)
**Reference Client:** Nexus Global

---

## 1. Design Philosophy

The Entity Platform API is **the sole interface** to the canonical graph. It is not a CRUD REST API. It is an **ontology action surface** — every endpoint corresponds to a declared Action Type or Function from the ontology (Dimension 01, §9).

### Core Principles

1. **Actions, not resources.** Endpoints invoke declared ontology actions (`POST /actions/execute-fx-forward`), not generic CRUD operations (`POST /transactions`). Each action carries its pre-flight rules, effects, and governance mode as part of the contract.

2. **Proof is mandatory.** Every write operation must include a proof payload. The API rejects writes without proof. This is not an implementation detail — it is part of the API contract.

3. **LEI as canonical identity.** Where a LegalEntity exists, LEI is the primary join key. LOB-internal identifiers are aliases, never canonicals.

4. **Projections never write to canonical.** LOB consumers (CB, CM, WM) read from projections only. All writes flow through this API.

5. **Temporal queries are first-class.** Every read endpoint supports `?asOf={timestamp}` for point-in-time reconstruction.

---

## 2. API Surface

### 2.1 Entity Resolution (Read)

Resolve entities by canonical identity. Returns current state unless `?asOf` is specified.

```
GET  /entities/{id}                        — resolve by canonical UUID
GET  /entities/by-lei/{lei}               — resolve by LEI (universal join key)
```

**Response:**
```typescript
interface EntityResolutionResponse {
  entity: GraphNode
  relationships: {
    active: GraphEdge[]
    suspended: GraphEdge[]
    // terminated excluded by default — use ?includeTerminated=true
  }
  interfaces: string[]                    // implemented ontology interfaces (e.g., ["IIsSettlementTarget", "IHasBalance"])
  proofSummary: {
    allChainsIntact: boolean
    chainCount: number
    oldestChainDate: ISO8601
    pendingVerifications: number
  }
  lobVisibility: LOBScope[]               // which LOBs caller is authorized to see
  asOf: ISO8601                           // effective timestamp of response
}
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `asOf` | ISO8601 | now | Point-in-time query |
| `includeTerminated` | boolean | false | Include terminated relationships |
| `interfaceFilter` | string | — | Filter relationships by target interface (e.g., `IIsSettlementTarget`) |
| `depth` | integer | 1 | Traversal depth (1 = direct edges, 2 = two-hop, etc.) |

**Example (Nexus Global):**
```
GET /entities/by-lei/549300NEXG001?interfaceFilter=IIsSettlementTarget&depth=2
```
Returns Nexus Global (Canada) with all accounts implementing `IIsSettlementTarget`, including subsidiary accounts (two-hop through `isSubsidiaryOf` edges).

---

### 2.2 Graph Traversal (Read)

Traverse the ontology graph using declared relationship patterns.

```
GET  /entities/{id}/ownership-chain        — traverse to UltimateParent
GET  /entities/{id}/beneficial-owners      — UBO resolution
GET  /entities/{id}/regulatory-exposure   — Party + Regulator edges by jurisdiction
GET  /entities/{id}/relationships          — all edges from node (filtered by state)
```

**Ownership Chain Response:**
```typescript
interface OwnershipChainResponse {
  root: LegalEntity                       // UltimateParent
  chain: LegalEntity[]                    // ordered from query target → root
  edges: {
    entity: LegalEntity
    relationship: GraphEdge               // isSubsidiaryOf edge
    proofSummary: ProofChainSummary
  }[]
  asOf: ISO8601
}
```

**Beneficial Owners Response:**
```typescript
interface BeneficialOwnersResponse {
  entity: LegalEntity
  beneficialOwners: {
    person: NaturalPerson
    ownershipPercentage: Decimal
    chain: LegalEntity[]                  // intermediate entities in ownership path
    isDirect: boolean                     // true if direct owner, false if indirect
  }[]
  threshold: Decimal                      // minimum ownership % included (default 25%)
  asOf: ISO8601
}
```

**Regulatory Exposure Response:**
```typescript
interface RegulatoryExposureResponse {
  entity: LegalEntity
  jurisdictions: {
    jurisdiction: string
    regulators: {
      regulator: Regulator
      kycStatus: EdgeState               // Active | Suspended | Terminated
      lastScreenedAt: ISO8601
      sanctionsStatus: "CLEAR" | "FLAGGED" | "NOT_SCREENED"
    }[]
    obligations: RegulatoryObligation[]
  }[]
  asOf: ISO8601
}
```

**Example (Nexus Global):**
```
GET /entities/by-lei/549300NEXG004/beneficial-owners?threshold=10
```
Returns all beneficial owners of Nexus Global UK Ltd with ≥10% ownership, including indirect owners through Nexus Global (Canada).

---

### 2.3 Proof Chain Retrieval (Read)

Access evidentiary chains for any relationship.

```
GET  /proof/{edgeId}                       — current proof chain summary
GET  /proof/{edgeId}/full                  — complete evidentiary chain
GET  /proof/{edgeId}/at/{timestamp}        — point-in-time proof state
```

**Summary Response:**
```typescript
interface ProofChainSummary {
  chainId: string
  edgeId: string
  currentState: ProofChainState
  integrityStatus: IntegrityStatus         // Valid | Challenged | Broken | Expired
  recordCount: number
  oldestRecord: ISO8601
  newestRecord: ISO8601
  pendingVerifications: number
}
```

**Full Chain Response:**
```typescript
interface ProofChainFull {
  chain: ProofChainSummary
  records: ProofRecord[]                   // ordered by sequence
  hashChainValid: boolean                  // cryptographic integrity check
  authorityBases: AuthorityBasis[]         // all authority bases referenced
}
```

---

### 2.4 Ontology Actions (Write)

These endpoints invoke declared Action Types from the ontology (§9.2-9.3). Each action declares its inputs, pre-flight rules, effects, governance mode, and audit trail.

**General pattern:**
```
POST /actions/{actionType}
```

**Request:**
```typescript
interface ActionRequest {
  inputs: Record<string, unknown>          // action-specific inputs (typed per Action Type)
  proofPayload: ProofRecord               // mandatory — evidence backing this action
  actorId: string                         // who/what is invoking
  actorType: "Human" | "System" | "Agent"
  idempotencyKey?: string                 // optional — prevents duplicate execution
}
```

**Response:**
```typescript
interface ActionResponse {
  actionId: string                        // unique execution identifier
  actionType: string
  status: "COMPLETED" | "PROPOSED" | "REVIEW_PENDING" | "BLOCKED"
  effects: ActionEffect[]                 // what was done
  proofChainId: string                    // proof chain created/updated
  governanceMode: GovernanceMode
  preFlightResult: PreFlightResult        // rule evaluation results
  executedAt: ISO8601
  executedBy: string
}
```

**Pre-Flight Result:**
```typescript
interface PreFlightResult {
  passed: boolean
  rulesEvaluated: {
    ruleId: string
    result: "PASS" | "FAIL"
    detail?: string
  }[]
}
```

---

#### Defined Action Endpoints

Each endpoint maps to an ontology Action Type. The contract below declares the action surface — not implementation details.

| Endpoint | Action Type | Governance | Description |
|----------|-------------|------------|-------------|
| `POST /actions/assert-relationship` | `AssertRelationship` | `PROPOSED` | Assert new relationship between entities |
| `POST /actions/review-relationship` | `ReviewRelationshipProposal` | `IMMEDIATE` | Approve/reject a proposed relationship |
| `POST /actions/approve-kyc-renewal` | `ApproveKYCRenewal` | `IMMEDIATE` | Approve KYC renewal |
| `POST /actions/initiate-payment` | `InitiatePayment` | `IMMEDIATE` | Initiate payment instruction |
| `POST /actions/execute-fx-forward` | `ExecuteFXForward` | `IMMEDIATE` | Execute FX forward contract |
| `POST /actions/drawdown-facility` | `DrawdownIntercompanyFacility` | `REVIEWED` | Drawdown intercompany lending |
| `POST /actions/initiate-pool-sweep` | `InitiatePoolSweep` | `IMMEDIATE` | Initiate cash pool sweep |

**Example: Execute FX Forward**
```
POST /actions/execute-fx-forward
Authorization: Bearer <token>
Content-Type: application/json

{
  "inputs": {
    "legalEntity": "549300NEXG001",
    "currencyPair": "USD/CAD",
    "notional": 1000000,
    "rate": 1.3650,
    "maturityDate": "2026-08-15T00:00:00Z",
    "settlementAccount": "NG-USA-USD-001"
  },
  "proofPayload": {
    "proofType": "SYSTEMIC",
    "intentSummary": "FX forward execution for Nexus Global CAD hedge",
    "intentPayload": {
      "contractRef": "FX-2026-0522-001",
      "traderId": "TRADER-042",
      "executionVenue": "INTERNAL"
    }
  },
  "actorId": "TRADER-042",
  "actorType": "Human",
  "idempotencyKey": "fx-exec-20260522-001"
}
```

**Response (success):**
```json
{
  "actionId": "act_9f8e7d6c5b4a",
  "actionType": "ExecuteFXForward",
  "status": "COMPLETED",
  "effects": [
    { "type": "createNode", "target": "FXTransaction", "id": "txn_fx_001" },
    { "type": "createNode", "target": "SettlementObligation", "id": "obl_001" },
    { "type": "createEdge", "target": "txn_fx_001 → initiatedBy → 549300NEXG001" },
    { "type": "createEdge", "target": "txn_fx_001 → settlesAgainst → NG-USA-USD-001" },
    { "type": "appendProofRecord", "target": "proof_txn_fx_001" }
  ],
  "proofChainId": "proof_txn_fx_001",
  "governanceMode": "IMMEDIATE",
  "preFlightResult": {
    "passed": true,
    "rulesEvaluated": [
      { "ruleId": "fx-subscription-active", "result": "PASS" },
      { "ruleId": "notional-within-limit", "result": "PASS" },
      { "ruleId": "aggregate-exposure-check", "result": "PASS" },
      { "ruleId": "currency-pair-permitted", "result": "PASS" },
      { "ruleId": "settlement-account-owned", "result": "PASS" }
    ]
  },
  "executedAt": "2026-05-22T14:23:11Z",
  "executedBy": "TRADER-042"
}
```

---

### 2.5 Function Invocation (Read/Compute)

Invoke declared ontology Functions (§9.4-9.5) for business logic evaluation.

```
POST /functions/{functionId}/evaluate
```

**Request:**
```typescript
interface FunctionRequest {
  inputs: Record<string, unknown>          // function-specific inputs
  asOf?: ISO8601                           // point-in-time evaluation
}
```

**Response:**
```typescript
interface FunctionResponse {
  functionId: string
  version: string
  result: unknown                          // function-specific output
  evaluatedAt: ISO8601
  auditLevel: AuditLevel
}
```

**Defined Function Endpoints:**

| Endpoint | Function | Audit Level | Description |
|----------|----------|-------------|-------------|
| `POST /functions/derive-edge-state/evaluate` | `deriveEdgeState` | `LOG` | Derive edge state from proof chain |
| `POST /functions/validate-mandate-scope/evaluate` | `validateMandateScope` | `FULL` | Validate agent mandate scope |
| `POST /functions/compute-product-eligibility/evaluate` | `computeProductEligibility` | `LOG` | Compute product eligibility |
| `POST /functions/compute-signing-authority/evaluate` | `computeSigningAuthority` | `FULL` | Determine signing authority |
| `POST /functions/compute-pool-interest/evaluate` | `computePoolInterest` | `FULL` | Compute pool interest posting |
| `POST /functions/validate-transfer-pricing/evaluate` | `validateTransferPricing` | `FULL` | Validate arm's-length pricing |

**Example: Validate Mandate Scope**
```
POST /functions/validate-mandate-scope/evaluate

{
  "inputs": {
    "agentMandate": "mandate_treasury_v2_3",
    "operation": "pool_restructure",
    "amount": 12000000,
    "currency": "CAD"
  }
}
```

**Response:**
```json
{
  "functionId": "validateMandateScope",
  "version": "1.0.0",
  "result": {
    "valid": true,
    "violations": [],
    "remainingLimit": 38000000
  },
  "evaluatedAt": "2026-05-22T14:00:00Z",
  "auditLevel": "FULL"
}
```

---

### 2.6 Mandate Management (Read/Write)

Manage and validate agentic mandates.

```
GET    /mandates/{agentId}                 — active mandate for agent
POST   /mandates/{agentId}/validate        — pre-flight scope check
```

**Validate Response (sub-millisecond target):**
```typescript
interface MandateValidationResponse {
  agentId: string
  mandateId: string
  valid: boolean
  state: MandateState                      // Active | Suspended | Revoked
  delegationChainIntact: boolean
  permittedOperations: OperationType[]
  limits: OperationLimits
  constraints: Constraint[]
  expiresAt: ISO8601
  validatedAt: ISO8601
}
```

---

### 2.7 Interface Resolution (Read)

Resolve which entities implement a given ontology interface.

```
GET  /interfaces/{interfaceName}           — list entities implementing interface
GET  /interfaces/{interfaceName}/{entityId} — check if entity implements interface
```

**Example:**
```
GET /interfaces/IIsSettlementTarget?entityType=LegalEntity&entityId=549300NEXG001&depth=2
```
Returns all settlement-target accounts owned by Nexus Global or its subsidiaries (two-hop).

---

## 3. Non-Functional Requirements

### 3.1 Latency Targets

| Operation | Target p99 | Store |
|-----------|------------|-------|
| Entity resolution by LEI | < 5 ms | Neo4j + Redis |
| Ownership chain traversal | < 5 ms | Neo4j |
| Beneficial owners resolution | < 10 ms | Neo4j |
| Mandate pre-flight validation | < 1 ms | PostgreSQL + Redis |
| Action execution (IMMEDIATE) | < 50 ms | Neo4j + PostgreSQL |
| Action execution (REVIEWED) | < 50 ms (sync) + async review | Neo4j + PostgreSQL |
| Proof chain retrieval | < 100 ms | PostgreSQL |
| Point-in-time query | < 500 ms | Delta Lake time-travel |
| Function evaluation | < 10 ms | In-process |

### 3.2 Rate Limiting

| Tier | Sustained RPS | Burst RPS | Scope |
|------|--------------|-----------|-------|
| LOB Consumer (CB/CM/WM) | 100 | 300 | Per tenant |
| Agent (automated) | 50 | 150 | Per agent |
| Human (portal/API) | 20 | 60 | Per user |
| Proof retrieval | 10 | 30 | Per edge |
| Action execution | 5 | 15 | Per action type |

Rate limits are enforced at the API gateway layer. Responses include `RateLimit-Remaining`, `RateLimit-Reset`, and `Retry-After` headers.

### 3.3 Pagination

All list endpoints support cursor-based pagination:

```
GET /entities/{id}/relationships?cursor=abc123&limit=50
```

Response includes pagination metadata:
```typescript
interface PaginationMeta {
  nextCursor?: string
  hasMore: boolean
  limit: number
  totalEstimated?: number
}
```

Default page size: 50. Maximum page size: 200.

### 3.4 Error Taxonomy

| HTTP Status | Error Code | Description | Retryable |
|-------------|------------|-------------|-----------|
| 400 | `INVALID_INPUT` | Request validation failed | No |
| 401 | `UNAUTHORIZED` | Missing/invalid credentials | No |
| 403 | `FORBIDDEN` | Insufficient permissions | No |
| 403 | `MANDATE_EXPIRED` | Agent mandate expired/suspended | No |
| 403 | `SCOPE_VIOLATION` | Action outside mandate scope | No |
| 404 | `ENTITY_NOT_FOUND` | Entity does not exist | No |
| 409 | `CONFLICT` | Pre-flight rule failed | No (fix inputs) |
| 409 | `PROOF_MISSING` | Write without proof payload | No |
| 429 | `RATE_LIMITED` | Rate limit exceeded | Yes (after Retry-After) |
| 422 | `PRE_FLIGHT_FAILED` | Business rule evaluation failed | No (fix inputs) |
| 500 | `INTERNAL_ERROR` | Unexpected server error | Yes |
| 503 | `SERVICE_UNAVAILABLE` | Circuit breaker open | Yes (after Retry-After) |

### 3.5 Circuit Breaker

Action execution endpoints use circuit breaker pattern:

| State | Condition | Behavior |
|-------|-----------|----------|
| CLOSED | Error rate < 5% | Normal operation |
| OPEN | Error rate ≥ 5% for 30s | Reject requests immediately (503) |
| HALF_OPEN | After 60s cooldown | Allow 1 request through; if success → CLOSED, if fail → OPEN |

Circuit breaker state exposed via `X-Circuit-Breaker` header.

### 3.6 Idempotency

All `POST /actions/*` endpoints support idempotency via `idempotencyKey`:
- Same key → returns cached result from original execution
- Key expires after 24 hours
- Collision with different payload → 409 `IDEMPOTENCY_CONFLICT`

### 3.7 Authentication & Authorization

- **Authentication:** OAuth 2.0 Bearer tokens (OIDC)
- **Authorization:** LOB-scoped roles mapped to `domain_scope` filtering
- **Agent authentication:** mTLS + agent-specific OAuth client credentials
- **Proof of authority:** Every write includes `actorId` + `actorType`; validated against entitlement graph

---

## 4. Serialization

| Context | Format | Rationale |
|---------|--------|-----------|
| API request/response | JSON-LD | Ontology-aligned, includes `@context` for type resolution |
| Internal messaging | Protobuf | High-throughput, schema-enforced |
| Formal ontology definition | OWL/RDF | FIBO-aligned, machine-readable |
| Proof payloads | JSON | Human-readable audit trail |

---

## 5. Vendor System Integration

Vendor-hosted products (Trade Finance, Supply Chain Finance) interact through the Containment Zone, not directly with the canonical graph.

```
Vendor System → Containment Zone API → Progressive Mapping → Canonical Graph
```

**Containment Zone Endpoints:**
```
POST /containment/ingest/{vendorId}        — ingest raw vendor data
GET  /containment/mapping/{vendorId}       — current mapping status
POST /containment/promote/{recordId}       — promote mapped record to canonical
```

Vendor systems authenticate via API keys scoped to their containment zone. They cannot query the canonical graph directly.

---

## 6. OpenAPI Specification

A machine-readable OpenAPI 3.1 specification will be generated from this contract for:
- Client code generation (TypeScript, Java, Go)
- Mock server testing (Phase 2 LOB integration)
- API gateway configuration
- Contract testing in CI/CD

**Location:** `artifacts/dimensions/04-api-integration-contract/specs/entity-platform-api.openapi.yaml` (to be generated)

---

## 7. Versioning

- API version in URL path: `/v1/actions/...`, `/v1/entities/...`
- Breaking changes → new major version
- Non-breaking additions (new action types, new query params) → same major version
- Current version: `v1`
- Deprecation policy: 12-month notice before EOL

---

## 8. Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-05-22 | v1-draft | Initial ontology action surface (supersedes REST CRUD model) |
