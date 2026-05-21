# Dimension 04: API Integration Contract — Memory Log

## Scope
Entity Platform API surface, REST endpoints, auth patterns, rate limits, LOB integration points, vendor system connectivity. Defines external interfaces and integration contracts only. No internal infra topology; no business semantics beyond what's exposed via the contract.

---

## Current State (2026-05-21)
Session recovered from git history + research artifacts after restart wipe. API spec exists in Architecture.md §6 Entity Platform API (~3KB). Impact analysis identifies critical non-functional gaps for production readiness.

### Core Endpoints (§6 — Committed):
```
GET  /entities/{id}                        — resolve by canonical ID
GET  /entities/by-lei/{lei}               — resolve by LEI (universal join key)
GET  /entities/{id}/relationships          — all edges from node, filtered by state
GET  /entities/{id}/ownership-chain        — traverse to UltimateParent
GET  /entities/{id}/beneficial-owners      — UBO resolution
GET  /entities/{id}/regulatory-exposure    — Party + Regulator edges by jurisdiction

GET  /proof/{edgeId}                       — current proof chain summary for edge
GET  /proof/{edgeId}/full                  — complete evidentiary chain
GET  /proof/{edgeId}/at/{timestamp}        — point-in-time proof state

POST /relationships                        — assert new relationship (triggers proof chain creation)
POST /proof/{edgeId}/records               — append proof record to chain

GET  /mandates/{agentId}                   — active mandate for agent
POST /mandates/{agentId}/validate          — pre-flight scope check before agent action
```

### Point-in-Time Query Support (§6.2)
All endpoints support `?asOf={timestamp}` parameter returning relationship state as it existed at that timestamp with proof chain state as of that date — foundation for regulatory examination response (any historical state reconstructable from graph).

**Example:** `GET /entities/ACME-CORP/relationships?asOf=2023-03-01T00:00:00Z`

### Entity Resolution Response Contract (§6.3):
```typescript
interface EntityResolutionResponse {
  entity: GraphNode
  relationships: { active: GraphEdge[]; suspended: GraphEdge[] } // terminated excluded by default (?includeTerminated=true)
  proofSummary: { allChainsIntact: boolean; chainCount: number; oldestChainDate: ISO8601; pendingVerifications: number }
  lob_visibility: LOBScope[]              // which LOBs caller authorized to see
  asOf: ISO8601                           // effective timestamp of response
}
```

### API as Sole Write Path (§5.2 Projection Rule)
The Entity Platform API is **the only interface** that queries the canonical graph directly and accepts writes via `POST /relationships`. All other systems (CB, CM, Wealth operational databases) consume read-only projections carrying explicit freshness timestamps — they never write back to canonical data.

### Key Invariants Enforced at API Layer (§10):
1. Every edge POST must atomically create a ProofChain + at least one ProofRecord; rejects writes without proof payload
2. No direct state field mutation allowed (state derived from event replay)
3. Pre-flight mandate validation mandatory for agent actions — expired/suspended/missing mandate blocks execution, doesn't warn

## Key Decisions Captured in Spec
1. **LEI as canonical identity** — where LegalEntity exists, LEI is primary join key; LOB-internal IDs are aliases never canonicals (§10 invariant #6)
2. **Ontology serialization:** OWL/RDF for formal ontology definition (FIBO-aligned), JSON-LD for API serialisation of graph data, Protobuf for high-throughput internal messaging

## Open Questions / Critical Gaps (from impact analysis):
- 🔴 No rate limiting strategy defined — LOB consumers need these before integration work begins; consider burst vs sustained limits per tenant/channel type
- 🟠 No pagination model documented (`?asOf` queries returning full relationship sets at enterprise scale will blow out response sizes); needs cursor-based or offset+limit with max page size
- 🟡 No circuit breaker patterns, retry semantics, error taxonomy (HTTP status code mapping), or OpenAPI 3.x spec generated yet — LOB integration teams need this before Phase 2 to begin mock-server testing and client code generation
- 🟠 Point-in-time queries require efficient temporal indexing on append-only tables; Delta Lake time-travel supports natively but at scale scan ranges for arbitrary historical timestamps could be expensive without careful partitioning by temporal boundaries (monthly partitions with `created_at` as co-clustering column)
