# 04 — API & Integration Contract

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Entity Platform API surface, integration rules  
**Status:** Draft for Daniel's review

## 1. Core Principle

The Entity Platform API is:
- The sole write path to the canonical graph.
- An ontology action surface, not a CRUD facade.

Everything external (LOB systems, vendors, internal partners) integrates via:
- Sync: Entity Platform API (REST/JSON-LD).
- Async: Confluent event streams (for analytics, risk, vendors, governance).

No random CRUD. No untracked direct writes.

## 2. Entity Resolution (Read)

Key operations:
- GET /entities/{id}
- GET /entities/by-lei/{lei}
- GET /entities/{id}/relationships
- GET /entities/{id}/ownership-chain
- GET /entities/{id}/beneficial-owners
- GET /entities/{id}/regulatory-exposure

All endpoints:
- Support ?asOf={timestamp} for point-in-time reconstruction.
- Return LOB-scoped visibility.
- Never expose internal implementation details.

## 3. Proof Chain Access (Read)

- GET /proof/{edgeId}
- GET /proof/{edgeId}/full
- GET /proof/{edgeId}/at/{timestamp}

Purpose:
- Regulators, auditors, compliance can reconstruct exactly how a relationship became true.

## 4. Ontology Actions (Write)

Actions, not resources. Each endpoint maps to an Action Type with:
- Inputs (typed ontology objects).
- Pre-flight rules (business logic).
- Effects (graph mutations, proof appends).
- Governance mode (IMMEDIATE / PROPOSED / REVIEWED).

Examples:
- POST /actions/assert-relationship
- POST /actions/review-relationship
- POST /actions/initiate-payment
- POST /actions/execute-fx-forward
- POST /actions/drawdown-facility
- POST /actions/initiate-pool-sweep

Each:
- Requires proofPayload.
- Emits events to Confluent for downstream consumers.

## 5. Functions & Mandates

- POST /functions/{functionId}/evaluate:
  - deriveEdgeState, validateMandateScope, computeSigningAuthority, etc.
- GET /mandates/{agentId}
- POST /mandates/{agentId}/validate (sub-millisecond target).

Agents act strictly under mandates; scope enforced at runtime.

## 6. Vendor & LOB Integrations

- Vendor systems:
  - Communicate via Containment Zone endpoints.
  - Never write directly to Neo4j/PostgreSQL.
- LOB systems:
  - Use Entity Platform API for commands.
  - Use projections (tb_cb, tb_cm, tb_wm) for reads.
  - Optionally subscribe to curated Confluent topics for event-driven flows.
