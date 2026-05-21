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

## Open Questions
- Complete entity catalog coverage for all four product lines? (current spec covers core types but need to validate against full Maya demo inventory)
- Cross-product-line relationship definitions finalized and tested against real client scenarios?
- Product taxonomy completeness validated against vendor system catalogs before DDL generation?
