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

---

## Compliance & Regulatory Scope (In-Scope)
Client onboarding and ongoing regulatory compliance are **in-scope** for the data platform:
- KYC/CDD at client onboarding stage with full audit trail of verification steps/sources/timestamps/decision-makers involved in each check before account opens or access granted to any product/service
- AML/sanctions screening as part of Core ontology layer (not Containment zone — regulatory compliance is foundational to the entity graph, not bolted-on after core model matures)
  - Real-time transaction monitoring feeds into Platform Observer pattern for near-real time exposure requirement → alerts surfaced through containment boundary initially; progressive mapping lifts signal upward toward canonical entities over time as business understanding deepens and jurisdictional requirements across all geographies fully mapped out first before adding complexity to Core semantic layer
- "Change in circumstance" events tracked per entity (ownership changes, UBO updates, risk profile shifts) → triggers re-screening workflows automatically via Workflow Engine integration with Entitlement Platform enforcement of maker-checker resolution + SoD validation at each compliance checkpoint/gate/phase transition point before state change persists to Core ledger domain systems
- Data classification rules built into ontology itself: sensitive fields (PEP flags, risk scores, source documentation references) have explicit metadata tags governing access patterns and exposure layer visibility controls per user role/entity scope boundaries defined by Entitlement Platform records stored separately from semantic layer but correlated through CIF-level entity hierarchy relationships maintained natively in Core model
---

## Product Architecture Scope (Confirmed In-Scope)
All four core product lines are in-scope for Phase 1, including complex composite offerings:
- **Cash Pooling** — distinct composite Product in the Ontology with explicit structural relationships to underlying Products it aggregates (DDA/Operating Accounts across entities). Not just metadata about which accounts participate but actual aggregation layer built ON TOP OF constituent account instances spanning multiple jurisdictions simultaneously active within same corporate group hierarchy like Nexus Global reference case shows during session configuration sequence when header pools members USA East 35.5% + Canada 23.2% with percentage weights and yield delta calculations consolidating USD/CAD positions in real-time from multiple domain systems feeding different parts of graph structure
- **FX Hedging** — cross-currency risk management products (USD/CAD forward, GBP/USD hedge) modeled as distinct offerings per Maya demo catalog (PROD-003 FX Forward CAD, PROD-004 FX Hedge GBP)
- **Intercompany Lending/Facilities** — revolving credit relationships between entities within same corporate group tracked separately from operating accounts but correlated through CIF-level entity hierarchy maintained natively in Core model
- **Payment Rails Services** — ACH/Fedwire/Lynx/CHAPS/EFT modeled as configurable product instances per currency/geography/rail eligibility matrices defined by Product Platform schema-driven generation pattern shown during App 2 admin portal demo where DDA (PROD-010) defines deployable configuration options across entities simultaneously active within same corporate group structure like Nexus Global example demonstrates

**Product taxonomy layer must support composite/hierarchical products**, not just flat catalog offerings without interdependencies between them affecting how intent flows through system when client says "optimize liquidity" → CashPool config wizard auto-generates from schema definition per Maya demo shows during session sequence

---

## Notes
- Requirements captured via conversation (2026-05-20). No design artifacts committed yet per Daniel's preference for extensive discovery before committing architecture decisions.
- Ongoing refinement expected as requirements mature.
