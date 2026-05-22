# Dimension 01: Logical Model & Ontology — Memory Log

## Scope
Business semantics, entity definitions, product catalog, relationships as the bank understands them. **No technology references whatsoever** — pure business/domain language. This is what "ontology-first" produces.

---

## Current State (2026-05-21)
Session recovered from git history + research artifacts after restart wipe. Full canonical graph spec exists at `artifacts/dimensions/01-logical-model/specs/canonical-graph-spec.md` (~32KB, 700 lines).

### Entity Taxonomy (Committed — Node Types)
```
Node
├── Party → LegalEntity (Corporation, Partnership, Trust, Sovereign), NaturalPerson, FinancialInstitution, Regulator
├── EntityGroup → UltimateParent, ConsolidatedGroup
├── Product → ProductDefinition, ProductInstance, ProductBundle
├── Account → OperatingAccount, VirtualAccount, NotionalPool, TradingAccount, CustodyAccount
├── Transaction → Payment, TradeTransaction, FXTransaction, Fee
├── Channel → DigitalPortal, APIChannel, H2HChannel, SWIFTChannel
├── Obligation → RegulatoryObligation, ContractualObligation, CreditObligation
└── Mandate → HumanMandate, AgentMandate
```

### Edge Taxonomy (Committed — Relationship Types)
- **Ownership:** owns, isSubsidiaryOf, isUltimateParentOf, hasBeneficialOwner
- **Authority:** hasSigningAuthority, hasAuthorisedRepresentative, delegatesTo
- **Product:** isSubscribedTo, isEligibleFor, isDeliveredThrough
- **Account:** isGovernedBy, hasBalance, isPartOf (NotionalPool membership)
- **Transaction:** settlesAgainst, initiatedBy, executedVia
- **Regulatory:** isSubjectTo, isKnownBy, isScreenedAgainst, reportsTo
- **Agentic:** operatesUnder, wasExecutedBy

### Product Architecture Scope (Confirmed In-Scope — from brief.md diff)
Phase 1 covers all four core product lines including composite offerings:
- Cash Pooling (composite Product with explicit aggregation layer over constituent accounts across entities/jurisdictions)
- FX Hedging (USD/CAD forward, GBP/USD hedge modeled per Maya demo catalog PROD-003/PROD-004)
- Intercompany Lending/Facilities (revolving credit between group entities via CIF-level hierarchy)
- Payment Rails Services (ACH/Fedwire/Lynx/CHAPS/EFT as configurable product instances per currency/geography/rail eligibility matrix)

**Product taxonomy must support composite/hierarchical products**, not flat catalog. CashPool config wizard auto-generates from schema definition (per Maya demo).

### Relationship Lifecycle Model
```
Proposed → Verified → Active ↔ Suspended → Terminated
                 ↓ Disputed → Resolved/Terminated
```
State transitions driven by proof chain events, never direct field updates.

## Key Decisions Captured in Spec
1. **Intent-First Ontology (Tenet #2)** — ontology rooted in client need/intent, not technical rails; ISO 20022 abstraction follows from this principle rather than dictating it
2. **Dual Containment Model** — Core model for bank-owned systems vs Containment zone for vendor data feeds with progressive mapping to common ontology
3. **KYC/AML/Sanctions in-scope as core, not bolt-on** — compliance entities are foundational graph nodes (Regulator, RegulatoryObligation), jurisdictional requirements vary across FINTRAC/FinCEN/FCA simultaneously on same corporate group structure; geographic scoping applies per Nexus Global reference case
4. **Materialisation always derived from the graph** — "the graph is never derived from materialisation"

## Expanded Content (2026-05-22)

### Entity Catalog (`research/entity-catalog.md` — ~17.7K)
Full entity catalog covering all four GTB product lines. Key additions vs. original spec:
- **5 new node subtypes:** `PhysicalPool` (physical fund sweeping vs. notional), `InterestPosting`, `SweepTransaction`, `Reversal`, `SettlementObligation`
- **Product hierarchy validated:** `ProductBundle` as composite first-class node; Cash Pooling modeled as bundle containing OperatingAccount × 2 + NotionalPool + Sweep Service + Reporting
- **Complete product-line mapping table:** Every business concept across Cash Pooling, FX Hedging, Intercompany Lending, Payment Rails mapped to canonical node types
- **Cross-product-line relationships documented:** Single LegalEntity node with subscriptions to 4 product bundles; single OperatingAccount with settlesAgainst edges from multiple transaction types
- **No coverage gaps identified** — all 4 product lines fully covered by existing or newly-added node types

### Relationship Scenarios (`research/relationship-scenarios.md` — ~17.2K)
7 real-world client scenarios validating edge taxonomy:
1. **New Client Onboarding + Cash Pool Setup** — 12 edge types used, all covered
2. **FX Forward Hedge Execution** — identified new `creates` edge (ProductInstance → SettlementObligation)
3. **Intercompany Loan Drawdown** — validated compound settlements (multiple `settlesAgainst` per transaction)
4. **Payment Initiation + Sanctions Screening** — proof chain handles screening/approval without new edges
5. **Relationship Suspension + Reinstatement** — state machine validated via proof chain events
6. **Agent-Initiated Pool Sweep** — full agentic proof chain with 3-level delegation trace
7. **Cross-LOB Client View** — graph traversal produces complete view without joining operational DBs

### Diagrams (`diagrams/` — 5 Mermaid + 5 PNG)
| Diagram | Source | PNG Size |
|---------|--------|----------|
| Entity Taxonomy | `entity-taxonomy.mmd` | 18.9K |
| Relationship Lifecycle | `relationship-lifecycle.mmd` | 40.1K |
| Product Hierarchy | `product-hierarchy.mmd` | 38.8K |
| Dual Containment Model | `dual-containment.mmd` | 48.6K |
| Cross-Product Client View | `cross-product-view.mmd` | 33.5K |

### Recommended Additions (from scenario validation)
1. **`creates`** edge: `ProductInstance → creates → SettlementObligation` (validated by FX Hedge scenario)
2. **Multiple `settlesAgainst` edges per transaction** (validated by Intercompany Lending + Sweep scenarios)

## Open Questions
- Complete entity catalog coverage for all four product lines? ✅ DONE — no gaps identified
- Cross-product-line relationship definitions finalized and tested against real client scenarios? ✅ DONE — 7 scenarios validated
- Product taxonomy completeness validated against vendor system catalogs before DDL generation? ⏳ PENDING
- VirtualAccount vs. OperatingAccount routing — when does a payment target a VirtualAccount that routes to OperatingAccount?
- ProductBundle pricing — should pricing be a property of Bundle/Instance or a separate Pricing node?
- Multi-currency accounts — one OperatingAccount with currency sub-accounts, or multiple nodes per currency?
- Hedge accounting classification — IFRS 9 effectiveness testing as dedicated edge or SettlementObligation property?
