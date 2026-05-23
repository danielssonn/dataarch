# Ontology × Kinetic × Proof: Coupling Analysis
## Complexity, Scalability, and Performance of the Compound System

**Date:** 2026-05-23
**Context:** How tightly should Ontology, Kinetic, and Proof layers couple? What breaks at scale?
**Status:** Research draft

---

## 1. The Coupling Problem

We have three layers that must work together but have fundamentally different characteristics:

| Layer | Nature | Access Pattern | Scale Profile |
|-------|--------|---------------|---------------|
| **Ontology (Neo4j)** | Graph of entities + relationships | Traversal-heavy, low-latency reads | ~28K nodes, ~62K edges Y1; grows with clients/products |
| **Kinetic (PostgreSQL)** | Business rules, actions, functions, review queues | Point queries + batch evaluations | ~10K rules, ~1M action instances/year |
| **Proof (PostgreSQL)** | Append-only hash-chained records | Sequential appends + chain verification | ~10M records/year (every edge write = 1+ proof records) |

**The question:** How tightly do these layers couple, and what is the performance cost of that coupling?

---

## 2. Tight vs. Loose Coupling — The Spectrum

### 2.1 Tight Coupling (Transaction-Scoped)

**Definition:** All three layers participate in a single logical transaction. An action cannot complete unless all three succeed atomically.

**Example:** Maya onboards Term Deposit 001
```
BEGIN TRANSACTION
  1. Neo4j: CREATE (maya)-[:subscribedTo]->(TD001-Instance)
  2. PostgreSQL/kinetic: INSERT INTO action_instances (COMPLETED)
  3. PostgreSQL/proof: INSERT INTO proof_chains + proof_records (hash-chained)
COMMIT
```

**Advantages:**
- Strong consistency — either the entire action succeeds or nothing changes
- Simple failure semantics — rollback is clean
- Audit trail is guaranteed to match graph state

**Disadvantages:**
- Cross-store transaction coordination (Saga pattern required — Neo4j + PostgreSQL cannot share a 2PC transaction)
- Saga compensation adds complexity (if proof write fails after graph write, must compensate)
- Latency = sum of all three operations (not max)
- Proof chain hash computation blocks the transaction (SHA-256 of previous record + new data)

**Verdict:** Required for Phase 1 write path. The Saga pattern we designed (Dim 02 §6) is the correct approach. Accept the complexity cost because regulatory correctness > performance optimization.

---

### 2.2 Loose Coupling (Event-Driven)

**Definition:** Ontology write completes first. Kinetic and Proof updates follow asynchronously via events.

**Example:**
```
1. Neo4j: CREATE edge (immediate, <5ms)
2. Publish event: edge.created { edgeId, partyId, productId }
3. Kinetic consumer: INSERT action_instances (async, <50ms)
4. Proof consumer: INSERT proof_records (async, <50ms)
```

**Advantages:**
- Ontology write latency is fast — not blocked by proof computation
- Kinetic and Proof can scale independently
- Failure in proof layer doesn't block graph operations

**Disadvantages:**
- Temporary inconsistency window — edge exists in graph before proof record exists
- Violates our invariant: "No edge write without atomic ProofChain creation"
- Replay complexity — if proof consumer lags, what happens to the edge?
- Regulatory risk — auditor sees edge without proof during inconsistency window

**Verdict:** Acceptable for read-heavy operations (proof verification, kinetic function evaluation) but NOT for write path. The invariant is non-negotiable for regulatory-grade systems.

---

### 2.3 Hybrid Coupling (The Practical Answer)

**Definition:** Write path is tightly coupled (Saga). Read path is loosely coupled with caching.

**This is what we're already designing.** The refinement is in understanding where the boundaries are and what breaks.

```
Write Path (Tight):
  API → Entity Platform API → Saga:
    Step 1: PostgreSQL kinetic.action_instances (PENDING)
    Step 2: PostgreSQL proof.proof_records (hash chain)
    Step 3: Neo4j CREATE edge
    Step 4: PostgreSQL kinetic.action_instances (COMPLETED)
    If any step fails → compensating action rolls back

Read Path (Loose + Cached):
  API → Redis cache (proof validity, kinetic eligibility) → Neo4j graph traversal
  Cache miss → synchronous fallback to PostgreSQL + Neo4j
```

---

## 3. Coupling Points — Where the Layers Touch

### 3.1 Ontology → Kinetic (Action Declaration)

**Coupling:** Action Types declared in Ontology are stored in `kinetic.action_types`.

**Direction:** Ontology defines the contract; Kinetic implements the execution.

**Coupling strength:** Loose. Ontology declares that `InitiatePayment` exists with certain parameters. Kinetic stores the executable definition. They can be updated independently as long as the contract is honored.

**Performance:** No runtime cost. The declaration is metadata, not execution.

**Risk:** Contract drift. If Ontology adds a parameter to `InitiatePayment` but Kinetic doesn't update its handler, the action fails at execution time. Mitigation: API contract validation at deployment time.

---

### 3.2 Ontology → Proof (Edge Creation)

**Coupling:** Every edge write in Neo4j must create a proof chain in PostgreSQL.

**Direction:** Ontology triggers Proof creation.

**Coupling strength:** Tight. This is the core invariant. Cannot be loosened.

**Performance:** This is the critical path.
```
Edge write latency = Neo4j CREATE (<5ms) + PostgreSQL proof INSERT (<5ms) + SHA-256 computation (<1ms) + Saga coordination (<10ms)
Total: ~25ms per edge write
```

At Nexus Global Y1 scale (~62K edges, assuming ~10 edge writes/day for new relationships):
- Daily proof records: ~10 (new edges) × ~3 (avg proof records per chain) = ~30 records/day
- This is trivial for PostgreSQL.

**But consider the steady state:**
- Payment transactions: ~5,000/day × 1 proof each = ~5,000 proof records/day
- Compliance checks: ~5,000/day × 4 checks = ~20,000 proof records/day
- Total: ~25,000 proof records/day ≈ ~9M/year

PostgreSQL handles ~100K inserts/sec. This is not a bottleneck.

**Real bottleneck:** Hash chain verification. When reading a proof chain with N records, verifying the chain requires computing SHA-256 for each record sequentially: O(N) hash computations. For chains with 50+ records (long-lived relationships with many events), this becomes noticeable.

**Mitigation:** Store `chainRootHash` as a materialized property on the edge itself. Verify root hash first (O(1)), then only do full chain verification on demand (audit queries).

---

### 3.3 Kinetic → Proof (Rule Evaluation)

**Coupling:** Kinetic function evaluations produce proof records.

**Direction:** Kinetic execution creates Proof evidence.

**Coupling strength:** Medium. The kinetic function `computeProductEligibility` evaluates rules and produces a result. That result is recorded as a proof record (`SYSTEMIC` type, `COMPLIANCE` kind).

**Performance:**
```
Eligibility evaluation:
  1. Load rules from kinetic.business_rules (<2ms, indexed)
  2. Load party data from Neo4j (<5ms, cached in Redis)
  3. Evaluate rules (<1ms per rule, ~4 rules = <4ms)
  4. Write proof record (<5ms)
Total: ~12ms per eligibility check
```

With Redis caching the result (TTL = rule change or party data change):
- First call: 12ms
- Cached calls: <1ms

**Scale consideration:** If 1,000 parties check eligibility simultaneously (product launch day), Redis cache handles it. Without cache, PostgreSQL handles ~100K queries/sec — still fine.

---

### 3.4 Proof → Kinetic (Pre-Flight Validation)

**Coupling:** Kinetic pre-flight rules check proof validity before allowing actions.

**Direction:** Kinetic queries Proof to gate actions.

**Coupling strength:** Tight on the critical path. Before `InitiatePayment` executes, the kinetic layer must verify:
- Mandate is valid (Proof query)
- Authority scope covers this action (Proof query)
- No scope violations (Proof query)

**Performance:**
```
Pre-flight validation:
  1. Redis: mandate validity check (<1ms)
  2. Redis: authority scope check (<1ms)
  3. If cache miss: PostgreSQL proof query (<5ms)
Total: <2ms cached, <15ms uncached
```

**This is why Redis is mandatory, not optional.** Without it, every action incurs a PostgreSQL proof query on the critical path. For high-frequency operations (payments, FX), this adds unacceptable latency.

---

### 3.5 Ontology ←→ Kinetic (Governance Mode)

**Coupling:** Ontology declares governance mode (`IMMEDIATE`, `PROPOSED`, `REVIEWED`). Kinetic implements the corresponding workflow.

**Direction:** Bidirectional. Ontology declares the mode; Kinetic executes the workflow and reports status back.

**Coupling strength:** Medium. The governance mode is metadata in the Ontology. The Kinetic layer reads it to decide whether to create an edge immediately or route through `review_queue`.

**Performance:** No runtime cost. Governance mode is read once at action type definition time, not per-action.

---

## 4. Complexity Analysis

### 4.1 Cyclomatic Complexity of the Write Path

```
Entity Platform API POST /actions/{actionType}
  ├── 1. Parse request + validate schema
  ├── 2. Resolve context (tenant, party, permissions)
  │     ├── Auth Service: JWT validation
  │     ├── Party Service: principal → party → tenant (Neo4j)
  │     └── Mandate check: Redis cache
  ├── 3. Kinetic pre-flight
  │     ├── Load action type definition
  │     ├── Evaluate pre_flight_rules (kinetic.business_rules)
  │     ├── Validate mandate scope (proof.proof_records)
  │     └── Check governance mode
  ├── 4. Execute Saga
  │     ├── Step 1: INSERT kinetic.action_instances (PENDING)
  │     ├── Step 2: INSERT proof.proof_chains
  │     ├── Step 3: INSERT proof.proof_records (hash-chained)
  │     ├── Step 4: Neo4j CREATE edge
  │     ├── Step 5: UPDATE kinetic.action_instances (COMPLETED)
  │     └── On failure: compensating action per step
  ├── 6. Publish event (Kafka)
  └── 7. Return response
```

**Branch count:** ~15 decision points (validation, governance mode, saga steps, error paths)
**Estimated cyclomatic complexity:** ~20-25

This is manageable but not trivial. The Saga pattern adds ~5 branches per step (success, failure, compensation, timeout, retry). With 5 steps, that's ~25 branches just in the saga.

**Recommendation:** Extract Saga orchestration into Temporal workflows. This moves complexity from application code into a dedicated orchestration engine with built-in retry, timeout, and compensation handling.

---

### 4.2 Data Flow Complexity

Three stores, one logical transaction:

```
┌──────────────────────────────────────────────────────────────┐
│                    WRITE PATH (Saga)                         │
│                                                              │
│  API → [1] PostgreSQL/kinetic (PENDING)                      │
│       → [2] PostgreSQL/proof (chain + records)               │
│       → [3] Neo4j (CREATE edge)                              │
│       → [4] PostgreSQL/kinetic (COMPLETED)                   │
│                                                              │
│  Compensation on failure:                                    │
│  [4] fail → rollback COMPLETED → PENDING                     │
│  [3] fail → Neo4j DELETE edge + rollback                     │
│  [2] fail → DELETE proof chain + rollback                    │
│  [1] fail → no-op (nothing committed yet)                    │
└──────────────────────────────────────────────────────────────┘
```

**Complexity drivers:**
1. **Cross-store atomicity** — Neo4j and PostgreSQL cannot share a distributed transaction. Saga is mandatory.
2. **Hash chain dependency** — Proof record N depends on hash of record N-1. Cannot parallelize proof chain creation.
3. **Compensation ordering** — Must compensate in reverse order of execution. Step 4 compensates before Step 3, etc.

---

## 5. Scalability Analysis

### 5.1 Ontology (Neo4j)

**Scale profile:**
- Y1: ~28K nodes, ~62K edges (Nexus Global estimate)
- Y3: ~100K nodes, ~250K edges (multi-client)
- Y5: ~500K nodes, ~1M edges (enterprise scale)

**Performance characteristics:**
- Graph traversal: <5ms p99 for 2-hop queries at 1M edges (Neo4j Aurora)
- Write throughput: ~1,000 edges/sec (Neo4j cluster)
- Read throughput: ~10,000 traversals/sec (with proper indexing)

**Bottlenecks:**
- Deep traversals (>3 hops) degrade quadratically. Mitigation: cache common traversals in Redis (tenant context, party hierarchy).
- Write contention on popular nodes (e.g., a ProductDefinition with 10,000 `subscribedTo` edges). Mitigation: Neo4j write partitioning by tenant.

**Verdict:** Neo4j scales adequately for GTB workloads. The graph is relatively shallow (2-3 hops typical) and write volume is moderate.

---

### 5.2 Kinetic (PostgreSQL)

**Scale profile:**
- `action_types`: ~50 rows (static, rarely changes)
- `business_rules`: ~10K rows (grows with products × rules)
- `action_instances`: ~1M/year (append-heavy, partitioned by month)
- `review_queue`: ~1K concurrent (low volume)
- `function_definitions`: ~20 rows (static)
- `proposed_edges`: ~500 concurrent (low volume)
- `compensating_actions`: ~100/year (rare)

**Performance characteristics:**
- Rule evaluation: <1ms per rule (simple SQL/PLpgSQL)
- Action instance writes: ~10K/sec (PostgreSQL standard)
- Review queue reads: <10ms (indexed)

**Bottlenecks:**
- `action_instances` table grows ~1M rows/year. At 5 years: ~5M rows. Needs monthly partitioning + archival strategy.
- Business rule evaluation at scale: if 100 rules must be evaluated per action, that's 100 sequential evaluations. Mitigation: compile rules into efficient evaluation trees; cache evaluation results.

**Verdict:** PostgreSQL kinetic layer is not the bottleneck. Rule evaluation is fast, and table volumes are manageable with standard partitioning.

---

### 5.3 Proof (PostgreSQL)

**Scale profile:**
- `proof_chains`: ~1 per edge write. At Y1: ~25K/year. At Y5: ~5M/year.
- `proof_records`: ~3 avg per chain. At Y1: ~75K/year. At Y5: ~15M/year.

**Performance characteristics:**
- Append throughput: ~100K/sec (PostgreSQL standard)
- Hash chain verification: O(N) per chain read. For chains with 50+ records: ~50ms.
- Chain integrity sweep: 15-minute batch job scanning all chains.

**Bottlenecks:**
- **Unbounded growth** is the #1 risk. Append-only means records never shrink. At Y5: ~15M proof records × ~1KB avg = ~15GB. Manageable but needs archival strategy.
- **Hash chain verification** degrades linearly with chain length. Long-lived relationships (banking agreements spanning decades) may have 100+ proof records. Full chain verification becomes expensive.
- **Intent payload size.** Proof records store the intent as JSON. Large intents (complex product configurations, multi-party mandates) can be tens of KB each. At scale, this inflates storage significantly.

**Mitigation strategy:**
1. **Materialized chain root hash** — store on the edge itself. O(1) validity check, O(N) only on demand.
2. **Intent payload compression** — gzip JSON payloads before storing. ~70% size reduction for structured data.
3. **Tiered storage** — hot proof records (<1 year) in PostgreSQL. Cold records (>1 year) archived to Azure Blob with WORM policy. Proof chain integrity maintained via hash anchors.
4. **Proof record batching** — for high-volume systemic proofs (compliance checks), batch multiple checks into a single proof record with array of results.

---

### 5.4 Compound System Scalability

**The combined system at Nexus Global Y1 scale:**

| Metric | Value | Bottleneck? |
|--------|-------|-------------|
| Edge writes/day | ~10 | No |
| Proof records/day | ~25K | No |
| Kinetic evaluations/day | ~50K | No |
| Graph traversals/day | ~100K | No (with Redis cache) |
| API calls/day | ~500K | No (API Gateway + Redis) |
| Proof chain verifications/day | ~1K | No |

**At enterprise scale (Y5, multi-client):**

| Metric | Value | Bottleneck? |
|--------|-------|-------------|
| Edge writes/day | ~500 | No |
| Proof records/day | ~40K | No |
| Kinetic evaluations/day | ~500K | No |
| Graph traversals/day | ~1M | ⚠️ Needs Redis cache + Neo4j cluster |
| API calls/day | ~5M | ⚠️ Needs API Gateway scaling |
| Proof storage | ~15GB/year | ⚠️ Needs archival strategy |

**Verdict:** The compound system scales to enterprise levels with standard infrastructure. The main risks are proof storage growth and graph traversal depth — both addressable with caching and archival.

---

## 6. Performance Budget

### 6.1 End-to-End Latency Budget

| Operation | Target | Breakdown |
|-----------|--------|-----------|
| **Product eligibility check** | <50ms | Redis cache: <1ms; uncached: 12ms |
| **Edge creation (onboarding)** | <100ms | Saga: 25ms + event publish: 5ms = 30ms |
| **Payment initiation** | <200ms | Pre-flight: 2ms + Saga: 25ms + SWIFT call: 150ms |
| **Context resolution** | <100ms | Redis: <1ms; uncached: 15ms |
| **Proof chain verification** | <500ms | Root hash: <1ms; full chain (50 records): ~50ms |
| **Party 360 view** | <1s | Neo4j 3-hop: 20ms + data assembly: 50ms |

### 6.2 Throughput Budget

| Operation | Target | Sustained |
|-----------|--------|-----------|
| Edge writes | 1,000/sec | Neo4j cluster |
| Proof appends | 100,000/sec | PostgreSQL |
| Kinetic evaluations | 10,000/sec | PostgreSQL (cached) |
| Graph traversals | 10,000/sec | Neo4j + Redis |
| API calls | 1,000/sec | API Gateway |

---

## 7. Coupling Recommendations

### 7.1 What Must Be Tightly Coupled

| Coupling | Reason | Alternative |
|----------|--------|-------------|
| **Edge write → Proof chain creation** | Regulatory invariant — edge without proof is invalid | None acceptable |
| **Action execution → Kinetic state** | Consistency — action must be tracked | None acceptable |
| **Pre-flight validation → Proof query** | Safety — must verify authority before acting | None acceptable |

### 7.2 What Can Be Loosely Coupled

| Coupling | Reason | Mechanism |
|----------|--------|-----------|
| **Proof chain verification (read)** | Not on write path | Async integrity sweep (15-min) |
| **Kinetic rule evaluation results** | Cached results suffice for reads | Redis cache with TTL |
| **Delta Lake sync** | Analytics can tolerate lag | CDC with <5s delay |
| **Event publishing (Kafka)** | Downstream consumers can lag | Async after Saga completes |

### 7.3 What Should Be Decoupled Entirely

| Concern | Reason | Approach |
|---------|--------|----------|
| **Proof archival** | Hot/cold data separation | Automated lifecycle management to Azure Blob WORM |
| **Kinetic rule management** | Business users edit rules independently | Separate admin surface; rules recompiled on change |
| **Ontology schema evolution** | Schema changes shouldn't block operations | Versioned schemas with migration path |

---

## 8. The Palantir Comparison — What They Got Right

Palantir's Object Storage V2 architecture separates three concerns that we're also separating, but with different store choices:

| Concern | Palantir OSv2 | Our Architecture |
|---------|--------------|------------------|
| **Metadata** | Ontology Metadata Service (OMS) | Ontology schema in Neo4j constraints + API contract |
| **Object storage** | Object Storage V2 (proprietary) | Neo4j (graph) + PostgreSQL (kinetic/proof) |
| **Query service** | Object Set Service (OSS) | Neo4j queries + Redis cache |
| **Write orchestration** | Object Data Funnel | Saga pattern + Temporal |
| **Action execution** | Actions service | Kinetic layer + Entity Platform API |

**Key insight from Palantir:** They separate indexing from querying. Object Storage V2 has distinct services for writing (Funnel) and reading (OSS). This enables horizontal scaling of each independently.

**Our equivalent:** Neo4j handles graph reads/writes. PostgreSQL handles kinetic/proof reads/writes. Redis handles hot cache reads. The separation is already there — but we should consider whether proof reads (verification queries) need a separate read replica to avoid competing with proof writes.

**Recommendation:** For Y1-Y3 scale, single PostgreSQL instance suffices for both kinetic and proof. At Y5+, consider read replicas for proof verification queries, especially if audit workload increases.

---

## 9. Summary — Coupling Principles

1. **Write path is tight.** Edge + Proof + Kinetic state must be consistent. Saga pattern is the mechanism. Accept the complexity cost.

2. **Read path is loose.** Cache aggressively (Redis). Async integrity verification. Delta Lake with <5s lag.

3. **Proof is the anchor.** Every coupling decision must preserve the invariant: no edge without proof, no action without mandate, no mandate without delegation chain.

4. **Complexity is in the Saga, not the stores.** Neo4j, PostgreSQL, and Redis are individually well-understood. The complexity is in coordinating them. Use Temporal to manage Saga orchestration.

5. **Scale is manageable.** At Nexus Global Y1 scale, the compound system is lightweight. The risks (proof storage growth, chain verification latency) are known and addressable.

6. **The differentiation is the cost.** Palantir doesn't have hash-chained proof chains, temporal validity windows, or 4-dimensional scope validation. Our coupling is tighter because our guarantees are stronger. That's the trade-off — and it's worth it for regulatory-grade GTB.

---

*This analysis should inform the Dim 02 materialization strategy (Saga refinement) and Dim 05 proof registry design (archival strategy, chain root hash). Fold validated recommendations into specs.*
