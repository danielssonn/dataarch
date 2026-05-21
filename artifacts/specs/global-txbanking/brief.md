# Global Transaction Banking — Data Platform Brief

**Author:** Daniel Maly  
**Captured by:** Data Architect Agent  
**Date:** 2026-05-21 (requirements gathered 2026-05-20)  
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

## Notes
- Requirements captured via conversation (2026-05-20). No design artifacts committed yet per Daniel's preference for extensive discovery before committing architecture decisions.
- Ongoing refinement expected as requirements mature.
