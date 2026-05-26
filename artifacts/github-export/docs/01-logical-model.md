# 01 — Logical Model

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Canonical graph, proof registry, kinetic interfaces  
**Status:** Draft for Daniel's review

## 1. What the Logical Model Defines

A temporally versioned, evidence-anchored knowledge graph for global transaction banking:

- **Canonical Graph:**
  - All entities, products, accounts, transactions, channels, obligations, mandates, vendor systems.
  - Single definition shared across CB/CM/WM.

- **Proof Registry:**
  - Immutable, append-only evidence for every relationship.
  - Event-sourced: state derived by replay, never mutated in-place.

Materialization is always derived from the graph. The graph is never derived from materialization.

## 2. Core Node Types

- Party
  - LegalEntity (Corporation, Partnership, Trust, Sovereign)
  - NaturalPerson
  - FinancialInstitution
  - Regulator
- EntityGroup
  - UltimateParent
  - ConsolidatedGroup
- Product
  - ProductDefinition
  - ProductInstance
  - ProductBundle
- Account
  - OperatingAccount, VirtualAccount, NotionalPool, PhysicalPool, TradingAccount, CustodyAccount
- Transaction
  - Payment, TradeTransaction, FXTransaction, Fee, InterestPosting, SweepTransaction, Reversal
- Channel
  - DigitalPortal, APIChannel, H2HChannel, SWIFTChannel
- Obligation
  - RegulatoryObligation, ContractualObligation, CreditObligation, SettlementObligation
- Mandate
  - HumanMandate, AgentMandate
- VendorSystem
  - TradeFinanceSystem, SupplyChainFinanceSystem

## 3. Core Edge Types

Examples:
- isSubsidiaryOf, hasBeneficialOwner
- owns, isPartOf (pool membership)
- settlesAgainst, initiatedBy, executedVia
- isSubscribedTo, isEligibleFor
- isKnownBy, isScreenedAgainst, isSubjectTo
- operatesUnder, wasExecutedBy
- isHostedBy, isMappedTo

Every edge:
- Has a proof chain.
- Has an explicit lifecycle (Proposed → Verified → Active → Suspended/Terminated).
- Is LOB-scoped via domainScope.

## 4. Interfaces (Polymorphic Contracts)

Interfaces unify behavior across node types:
- IIdentifiable
- IHasLifecycle
- IHasBalance
- IIsSettlementTarget
- IIsRegulatable
- IIsSubscribable
- IIsPoolMember
- IHasMandate

Used by:
- Queries (“all settlement targets for ACME”).
- Action inputs (InitiatePayment requires IIsSettlementTarget).
- Functions (computeProductEligibility, etc.).

## 5. Kinetic Constructs

The graph is not passive. The kinetic layer makes it operational:

- **Interfaces:** polymorphic contracts across types.
- **Action Types:** declared business operations (e.g., InitiatePayment, ExecuteFXForward) with:
  - typed inputs,
  - pre-flight rules,
  - explicit effects,
  - permissions,
  - governance modes.
- **Functions:** versioned business logic (e.g., validateMandateScope, computeSigningAuthority).

## 6. Containment Zone for Vendor-Hosted Systems

- Trade Finance and Supply Chain Finance are vendor-hosted.
- Containment Zone:
  - Isolated catalog (tb_containment).
  - Vendor systems enter as-is; progressive mapping to canonical terms.
  - Mapping tracked via vendor_mapping_status (Partial → Complete).
