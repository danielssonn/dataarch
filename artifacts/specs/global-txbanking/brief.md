# Global Transaction Banking — Data Platform Brief

**Lead Architect:** Daniel Maly
**Author:** Daniel Maly, captured by Data Architect Agent
**Dates:** Requirements sessions — 2026-05-20 and 2026-05-21 (Thursday)
**Status:** Discovery  

---

## Business Context
Top 10 North American bank building a data platform to power its Global Transaction Banking division. Primary driver is growth and market penetration through superior data-driven capabilities. Environment includes both greenfield opportunities and legacy silos requiring integration.

### Design Target
Fortune 50-scale corporate entities with full real-world complexity (multi-entity hierarchies, cross-border operations, complex product mixes). If the blueprint solves for this segment, it covers all other customer tiers by design.

---

## Product Lines

| # | Offering             | Notes                       |
|---|----------------------|------------------------------|
| 1 | Cash Management      | Core transaction banking     |
| 2 | Liquidity            | Sweeps, pooling, optimization|
| 3 | Trade Finance        | Letters of credit, guarantees|
| 4 | Supply Chain Finance | Reverse factoring, financing |

Most core offerings are vendor-hosted systems — not homegrown bank applications.

---

## Scale Assumptions

- **Year 1:** ~200 corporate customers  
- **Year 5 Target:** ~1,000 corporate customers
- **Transaction volumes:** Low to medium (not high-frequency trading scale)

---

## Platform & Cloud

| Layer             | Choice                        | Owner        |
|------------------|-------------------------------|-------------|
| Data platform    | Databricks                    | Daniel Maly  |
| Cloud            | Azure                         | —           |
| Vendor integration | APIs / microservices         | Loosely coupled architecture |

Daniel will provision and own the Databricks environment. Architecture work focuses on what flows in, how it's modeled, and how data exits to consumers.

---

## Solution Tenets

1. **Bi-directional streaming** — Data must flow INTO and OUT of the platform natively. Not a one-way ETL sink.
2. **Near-real-time exposure** — Serve operational and analytical consumers with minimal latency, including external client-facing systems. This is NOT purely an analytics play.
3. **Ontology-first design** — A rigorous ontology model serves as the foundational semantic layer for cross-product-line data consistency.

---

## Planned Artifacts (Separation of Concerns)

| Artifact                  | Purpose                                                    | Dependency              |
|---------------------------|------------------------------------------------------------|-------------------------|
| Data Ontology Model       | Semantic foundation, entity relationships, canonical model  | None                    |
| Data Exposure Patterns    | How data is served to consumers; APIs, streams, datasets   | Informed by ontology    |

These are two distinct deliverables. The ontology should be able to opine on the exposure pattern — not dictate it directly.

---

## Data Strategy — Dual Containment Model

### Core Principle
Two distinct data domains with different governance, lifecycle, and evolution cadence. A containment boundary between them prevents uncontrolled diffusion while enabling rapid integration velocity.

| Layer | Scope | Control Level | Evolution Cadence |
|-------|-------|--------------|-------------------|
| **Containment Model** (External) | Vendor system data feeds: Trade Finance vendor, Supply Chain Finance vendor, Cash Flow Forecasting tool. Third-party integrations we cannot easily control source schemas of | Low — adapt & absorb quickly; map progressively to Core over time | Quarantine zone that isolates external schema volatility from internal architecture |
| **Core Model** (Internal) | Bank-owned systems: Core Ledger + Payments drive the data space. Canonical domain entities under our full lifecycle ownership | High — deliberate, progressive evolution as business understanding matures (~5 year horizon) | "True north" semantic layer; evolves at our pace, not driven by vendor change cycles |

### Key Tension Being Solved
Enable fast third-party integration + rapid time-to-value → **BUT contain data diffusion and fragmentation** while progressively defining the Core model.

Without this boundary, every new vendor system pollutes the internal model with its own schema conventions — creating a fragmented mess that slows everything down over time. Containment absorbs; Core harmonizes.

### Harmonization Governance
This architecture work **IS** the harmonization engine. No separate team or parallel process needed:
```
Vendor System → Containment Zone ──(progressive mapping)──→ Common Ontology ← Core Systems
                                                    ↑
                                          The ontology definition drives alignment.
```
The common ontology serves dual role: (1) north star for canonical entities, and (2) progressive mapping target for containment zone feeds as business understanding matures.

---

## Core Tenets (Architectural Guardrails)

These principles are non-negotiable. They guide all design decisions, ontology modeling choices, containment zone patterns, and exposure layer architecture.

### Tenet 1 — Containment Model with Progressive Harmonization
External vendor systems land in a quarantine/containment zone that isolates their schema volatility from the internal Core model. Time-to-value is fast because new integrations slot into containment immediately without waiting for canonical alignment. Over time, progressive mapping lifts signal upward toward Core entities as business understanding matures.

The common ontology IS the harmonization engine — not a separate team or parallel process.

### Tenet 2 *(Critical)* — Intent-First Ontology Rooted in Client Need
**Top tier of the ontology = client intent.** What does the corporation need? What can we sell them that satisfies it?

```
Client Intent        ← Maya thinks here ("move money", "hedge exposure")
      ↓
Product/Service Offering  ← Bank sells this (Cash Pool, FX Forward)
      ↓
Technical Rail Selection   ← Geography + bank infrastructure resolves execution path 
                             (ACH vs Fedwire vs Lynx vs CHAPS — invisible to client)
      ↓
Domain Execution         ← ISO messages hit the wire; ledger entries post
```

**Key properties:**
- Client-facing consumers never see technical rail names. "Send $5M to Canada subsidiary" → platform resolves CAD → Lynx automatically.
- **Correlation is maintained end-to-end.** Full traceability from intent through product selection down to domain execution (ISO 20022 payloads, ledger postings). Audit complete without forcing implementation details upward into business semantics.
- Geography + rail availability = operational constraints that drive resolution logic. They are NOT ontology concepts themselves — they're metadata on the technical layer beneath client-facing abstractions.

This tenet directly informs containment zone design: external vendor systems produce domain-level execution data (raw ISO messages, proprietary status codes). Containment absorbs them as-is; progressive mapping lifts signal upward through rail → product → intent layers over time until it lands in Core ontology terms that reflect what the client actually needed and received.

### Tenet 3 *(Flagged)* — Business-Friendly Abstraction Above ISO 20022
ISO 20022 is technically rich but not business-intuitive. The Top tier must present payment concepts at level of intent + execution status, NOT message-level fidelity. Technical rail selection and geography constraints are resolved automatically by the platform.

⚠️ This tenet expands on Tenet #1 above once ISO 20022 → Business Ontology mapping patterns get fully unpacked.

---

## Notes
- Requirements captured via conversation (2026-05-20). No design artifacts committed yet per Daniel's preference for extensive discovery before committing architecture decisions.
- Ongoing refinement expected as requirements mature.
