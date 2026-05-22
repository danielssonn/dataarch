# Entity Catalog — Global Transaction Banking Ontology

**Dimension:** 01 — Logical Model & Ontology
**Date:** 2026-05-22
**Status:** Draft
**Reference Client:** Nexus Global (Maya's client)

## Purpose

Complete entity catalog covering all four GTB product lines, grounded in the **Nexus Global** reference client. Maps business concepts to canonical node types, validates coverage gaps, and defines composite product hierarchy.

Cross-references the node/edge taxonomy in `specs/canonical-graph-spec.md §2.1–2.3`.

## Vendor-Hosted Constraint `[VENDOR-HOSTED]`

Trade Finance and Supply Chain Finance are **vendor-hosted systems**, not homegrown bank applications. The ontology serves as a **semantic integration layer** over vendor schemas rather than a direct physical canonical store for all operational data. These systems land in the Containment Zone with progressive mapping to Core ontology terms.

| Product Line | Hosting Model | Ontology Role |
|---|---|---|
| Cash Management | Bank-owned (Core) | Direct canonical representation |
| Liquidity (Pooling/Sweeps) | Bank-owned (Core) | Direct canonical representation |
| **Trade Finance** | **Vendor-hosted** | **Containment Zone → progressive mapping** |
| **Supply Chain Finance** | **Vendor-hosted** | **Containment Zone → progressive mapping** |

---

## 1. Entity Taxonomy (Complete)

### 1.1 Party Subgraph

The party subgraph is the anchor of everything. Every account, transaction, obligation, and mandate traces back to a party.

```
Party
├── LegalEntity
│   ├── Corporation              ← primary client type; LEI-bearing
│   ├── Partnership              ← multi-party legal construct; may have LEI
│   ├── Trust                    ← fiduciary structure; settlor/beneficiaries are NaturalPerson
│   └── Sovereign                ← government entity; no LEI, uses national identifier
├── NaturalPerson                ← UBOs, signatories, authorised representatives
├── FinancialInstitution         ← correspondent banks, clearing agents, custodians
└── Regulator                    ← OSFI, FinCEN, FCA, MAS, FINTRAC, etc.
```

**Canonical identity:**
- `LegalEntity` → LEI (Legal Entity Identifier) is primary key where available
- `NaturalPerson` → government-issued ID + name + DOB composite key
- `FinancialInstitution` → BIC/SWIFT code + LEI
- `Regulator` → ISO 3166 country code + agency name

**Coverage note:** Every product line's client-facing entities map to `LegalEntity` or `NaturalPerson`. No new party subtypes needed for Phase 1.

---

### 1.2 EntityGroup Subgraph

Models corporate hierarchy and consolidation boundaries. Critical for Cash Pooling and Intercompany Lending.

```
EntityGroup
├── UltimateParent              ← top of ownership tree; UBO resolution target
└── ConsolidatedGroup           ← regulatory consolidation boundary (may differ from ownership)
```

**Key relationships:**
- `LegalEntity → isSubsidiaryOf → LegalEntity` (recursive, forms ownership tree)
- `LegalEntity → isUltimateParentOf → EntityGroup` (anchors the tree)
- `LegalEntity → hasBeneficialOwner → NaturalPerson` (UBO resolution, >25% threshold per FATF)

**Product line mapping:**
| Product Line | EntityGroup Usage |
|---|---|
| Cash Pooling | Pool master = UltimateParent or designated group entity; participants = subsidiaries |
| FX Hedging | Hedge program scoped to ConsolidatedGroup; individual contracts per LegalEntity |
| Intercompany Lending | Lender/borrower pairs within EntityGroup; credit limit at group level |
| Payment Rails | Payment approval hierarchies follow ownership tree |

---

### 1.3 Product Subgraph

**Must support composite/hierarchical products.** Flat catalog is insufficient.

```
Product
├── ProductDefinition           ← abstract template; defines capabilities, constraints, eligibility
├── ProductInstance             ← concrete instantiation for a specific client/jurisdiction
└── ProductBundle               ← composite; aggregates multiple ProductInstances
    └── contains: ProductInstance[]
```

**Composite model:** A `ProductBundle` is a first-class node with its own lifecycle, pricing, and subscription. It contains child `ProductInstance` nodes but is independently subscribed to by the client.

**Example — Cash Pooling as composite:**
```
ProductBundle: "Multi-Currency Cash Management Suite"
├── ProductInstance: "CAD Operating Account" (OperatingAccount)
├── ProductInstance: "USD Operating Account" (OperatingAccount)
├── ProductInstance: "Notional Pool CAD+USD" (NotionalPool)
├── ProductInstance: "Intraday Sweep Service" (Service)
└── ProductInstance: "Daily Balance Reporting" (Service)
```

Client subscribes to the bundle. Individual instances are managed by the bank but visible to the client as part of the offering.

---

### 1.4 Account Subgraph

```
Account
├── OperatingAccount            ← core transactional account; holds balance
├── VirtualAccount              ← logical account; no regulatory balance, routing-only
├── NotionalPool                ← aggregation of balances across accounts (no physical movement)
├── PhysicalPool                ← actual balance sweeping/zeroing (physical movement)
├── TradingAccount              ← securities/trade positions (CM overlap)
└── CustodyAccount              ← asset safekeeping (WM overlap)
```

**New vs. original spec:** Added `PhysicalPool` to distinguish notional pooling (balance aggregation for interest calculation) from physical pooling (actual fund sweeps). Both are needed for the Cash Pooling product line.

---

### 1.5 Transaction Subgraph

```
Transaction
├── Payment                     ← funds transfer; ACH, Wire, EFT, CHAPS, SEPA
├── TradeTransaction            ← securities trade; principal + settlement obligation
├── FXTransaction              ← currency conversion; spot, forward, swap
├── Fee                        ← service charge; always linked to parent transaction or account
├── InterestPosting            ← interest calculation result; linked to account/pool
├── SweepTransaction           ← intraday/overnight balance movement; pool-related
└── Reversal                   ← undoes parent transaction; maintains audit trail
```

**New vs. original spec:** Added `InterestPosting`, `SweepTransaction`, `Reversal` — all required for Cash Pooling and Intercompany Lending operational accuracy.

---

### 1.6 Channel Subgraph

```
Channel
├── DigitalPortal              ← client-facing web UI
├── APIChannel                 ← programmatic access; REST/GraphQL
├── H2HChannel                 ← host-to-host; SWIFT, ISO 20022 file exchange
└── SWIFTChannel              ← SWIFT-specific; gpi, MT/MX messages
```

No changes from original spec. Covers all client interaction vectors.

---

### 1.7 Obligation Subgraph

```
Obligation
├── RegulatoryObligation       ← compliance requirement; AML, KYC, sanctions, reporting
├── ContractualObligation      ← binding agreement; banking agreement, service level
├── CreditObligation           ← lending exposure; intercompany facility, credit line
└── SettlementObligation       ← pending settlement; trade confirmation, FX forward
```

**New vs. original spec:** Added `SettlementObligation` — needed for FX Hedging (forward contracts create settlement obligations at maturity) and TradeTransaction lifecycle.

---

### 1.8 Mandate Subgraph

```
Mandate
├── HumanMandate              ← root authority; signed by NaturalPerson with signing authority
└── AgentMandate              ← delegated authority; system/agent acting under HumanMandate
```

No changes. Covered in detail in canonical spec §4.

---

## 2. Product Line Entity Mapping

### 2.1 Cash Pooling

Core product. Requires the most complex entity relationships.

| Business Concept | Node Type | Notes |
|---|---|---|
| Pool Master (client) | `LegalEntity` | Designated entity managing the pool |
| Pool Participant | `LegalEntity` | Subsidiary with account in pool |
| Pool Structure | `ProductBundle` | Composite: accounts + sweep rules + reporting |
| Operating Account | `OperatingAccount` | Physical account per participant |
| Notional Pool | `NotionalPool` | Balance aggregation (no fund movement) |
| Physical Pool | `PhysicalPool` | Balance sweeping (fund movement) |
| Sweep Rule | `ContractualObligation` | Defines timing, thresholds, direction |
| Intraday Sweep | `SweepTransaction` | Execution record of sweep |
| Interest Calculation | `InterestPosting` | Daily interest on pooled balance |
| Pool Agreement | `ContractualObligation` | Master pooling agreement |
| Regulatory Reporting | `RegulatoryObligation` | Transfer pricing, thin capitalization rules |

**Relationships specific to Cash Pooling:**
```
LegalEntity (Pool Master) ──owns──► OperatingAccount
OperatingAccount ──isPartOf──► NotionalPool / PhysicalPool
NotionalPool ──isGovernedBy──► ProductInstance (Pool config)
LegalEntity (Participant) ──owns──► OperatingAccount
LegalEntity ──isSubsidiaryOf──► LegalEntity (ownership chain validates pool eligibility)
SweepTransaction ──settlesAgainst──► OperatingAccount
SweepTransaction ──initiatedBy──► LegalEntity (Pool Master)
InterestPosting ──settlesAgainst──► OperatingAccount
```

**Critical constraint:** Pool participants must be within the same `EntityGroup` (ownership-verified) OR have explicit intercompany lending mandate. Cross-group pooling requires regulatory approval per jurisdiction.

---

### 2.2 FX Hedging

Forward contracts, spot transactions, and structured hedges.

| Business Concept | Node Type | Notes |
|---|---|---|
| Hedge Program | `ProductBundle` | Composite: multiple forward contracts under one mandate |
| Forward Contract | `ProductInstance` | USD/CAD forward, GBP/USD forward, etc. |
| Spot Transaction | `FXTransaction` | Immediate settlement |
| Hedge Mandate | `HumanMandate` | Treasury authorization for hedging activities |
| Counterparty Bank | `FinancialInstitution` | Correspondent bank executing the hedge |
| Settlement Obligation | `SettlementObligation` | Future settlement at forward maturity |
| Margin Call | `CreditObligation` | Collateral requirement for open positions |
| Hedge Accounting | `RegulatoryObligation` | IFRS 9 / ASC 815 compliance |

**Relationships specific to FX Hedging:**
```
LegalEntity ──isSubscribedTo──► ProductBundle (Hedge Program)
ProductBundle ──contains──► ProductInstance (Forward Contract)
ProductInstance ──isDeliveredThrough──► SWIFTChannel / APIChannel
LegalEntity ──initiatedBy──► FXTransaction
FXTransaction ──executedVia──► FinancialInstitution (Counterparty)
FXTransaction ──settlesAgainst──► OperatingAccount
LegalEntity ──isSubjectTo──► RegulatoryObligation (Hedge Accounting)
ProductInstance ──creates──► SettlementObligation (at maturity)
```

**Critical constraint:** Hedge program mandates must specify permitted currency pairs, maximum notional per contract, and aggregate exposure limits. AgentMandate for auto-hedging must inherit these constraints.

---

### 2.3 Intercompany Lending / Facilities

Revolving credit facilities between group entities.

| Business Concept | Node Type | Notes |
|---|---|---|
| Lending Facility | `ProductBundle` | Composite: credit line + terms + covenants |
| Credit Line | `ProductInstance` | Revolving or term facility |
| Loan Drawdown | `Payment` | Funds transfer from lender to borrower |
| Repayment | `Payment` | Reverse flow; linked to original drawdown |
| Interest on Loan | `InterestPosting` | Periodic interest calculation |
| Facility Agreement | `ContractualObligation` | Master lending agreement |
| Credit Limit | `CreditObligation` | Maximum exposure per borrower |
| Covenant | `ContractualObligation` | Financial ratios, reporting requirements |
| Transfer Pricing | `RegulatoryObligation` | Arm's length pricing per tax jurisdiction |

**Relationships specific to Intercompany Lending:**
```
LegalEntity (Lender) ──owns──► OperatingAccount
LegalEntity (Borrower) ──owns──► OperatingAccount
LegalEntity (Borrower) ──isSubscribedTo──► ProductInstance (Credit Line)
CreditLine ──isGovernedBy──► ContractualObligation (Facility Agreement)
Payment (Drawdown) ──initiatedBy──► LegalEntity (Borrower)
Payment (Drawdown) ──settlesAgainst──► OperatingAccount (Lender → Borrower)
LegalEntity (Borrower) ──isSubjectTo──► CreditObligation (Limit)
LegalEntity ──isSubjectTo──► RegulatoryObligation (Transfer Pricing)
```

**Critical constraint:** Intercompany lending requires arm's-length pricing validation per tax jurisdiction. The `RegulatoryObligation` node for transfer pricing must carry jurisdiction-specific interest rate benchmarks (e.g., LIBOR/SOFR + spread per country).

---

### 2.4 Payment Rails Services

Multi-rail payment infrastructure.

| Business Concept | Node Type | Notes |
|---|---|---|
| Payment Rail | `ProductDefinition` | ACH, Fedwire, Lynx, CHAPS, EFT, SEPA |
| Rail Instance | `ProductInstance` | Configured per currency/geography/client |
| Payment Instruction | `Payment` | Client-initiated transfer |
| Rail Eligibility | `isEligibleFor` edge | Party → isEligibleFor → ProductDefinition |
| Payment Approval | `HumanMandate` | Signing authority matrix |
| Payment Screening | `RegulatoryObligation` | Sanctions/AML check per payment |
| Return/Reversal | `Reversal` | Failed or recalled payment |

**Relationships specific to Payment Rails:**
```
LegalEntity ──isEligibleFor──► ProductDefinition (Rail)
LegalEntity ──isSubscribedTo──► ProductInstance (Rail config)
Payment ──initiatedBy──► LegalEntity / NaturalPerson (signatory)
Payment ──executedVia──► Channel (DigitalPortal / APIChannel / H2HChannel)
Payment ──settlesAgainst──► OperatingAccount
Payment ──isSubjectTo──► RegulatoryObligation (Screening)
NaturalPerson ──hasSigningAuthority──► LegalEntity (approval matrix)
```

**Eligibility matrix:** Rail eligibility is determined by:
- Currency support (rail-specific)
- Geographic availability (sender/receiver jurisdiction)
- Client onboarding status (KYC complete for target jurisdiction)
- Product subscription (active rail instance)

This is a computed eligibility, not a static attribute. The `isEligibleFor` edge state is derived from the intersection of these conditions.

---

### 2.5 Trade Finance (Vendor-Hosted) `[VENDOR-HOSTED]`

Letters of credit, guarantees, and documentary collections. Hosted by external vendor.

| Business Concept | Node Type | Notes |
|---|---|---|
| Trade Finance Vendor | `VendorSystem` (TradeFinanceSystem) | External system; Containment Zone |
| Letter of Credit | `ProductInstance` | PROD-TF-001; hosted by vendor |
| Guarantee | `ContractualObligation` | Bank guarantee issued on behalf of client |
| LC Application | `Payment` | Client request to open LC |
| LC Settlement | `SettlementObligation` | Payment obligation upon document presentation |
| Documentary Collection | `TradeTransaction` | Documents exchanged for payment |

**Relationships specific to Trade Finance:**
```
LegalEntity (Nexus Global) ──isSubscribedTo──► ProductInstance (PROD-TF-001)
ProductInstance (PROD-TF-001) ──isHostedBy──► VendorSystem (TradeFinanceVendor)
VendorSystem ──isMappedTo──► ProductInstance [mappingStatus: Partial]
LegalEntity ──initiatedBy──► TradeTransaction
TradeTransaction ──creates──► SettlementObligation
VendorSystem ──containmentStatus──► Partial | Complete
```

**Critical constraint:** Vendor system produces proprietary status codes and raw messages. Containment Zone absorbs as-is; progressive mapping lifts signal upward to Core ontology terms over time. No direct canonical representation until mapping is `Complete`.

---

### 2.6 Supply Chain Finance (Vendor-Hosted) `[VENDOR-HOSTED]`

Reverse factoring and supplier financing. Hosted by external vendor.

| Business Concept | Node Type | Notes |
|---|---|---|
| SCF Vendor | `VendorSystem` (SupplyChainFinanceSystem) | External system; Containment Zone |
| Reverse Factoring Program | `ProductInstance` | PROD-SCF-001; hosted by vendor |
| Supplier Financing | `CreditObligation` | Financing extended to supplier |
| Invoice Assignment | `ContractualObligation` | Invoice transferred to financier |
| Early Payment | `Payment` | Supplier receives early payment |
| Debtor Confirmation | `DECLARATIVE` proof | Buyer confirms invoice obligation |

**Relationships specific to Supply Chain Finance:**
```
LegalEntity (Nexus Global, as Buyer) ──isSubscribedTo──► ProductInstance (PROD-SCF-001)
ProductInstance (PROD-SCF-001) ──isHostedBy──► VendorSystem (SupplyChainFinanceVendor)
VendorSystem ──isMappedTo──► ProductInstance [mappingStatus: Partial]
LegalEntity (Supplier) ──isSubjectTo──► CreditObligation (Financing limit)
Payment (Early Payment) ──settlesAgainst──► OperatingAccount (Supplier)
```

**Critical constraint:** Same Containment Zone pattern as Trade Finance. Vendor schema volatility is isolated from Core model. Progressive mapping tracks harmonization status.

---

## 3. Cross-Product-Line Relationships

Entities shared across product lines create the "single view of client" value proposition.

### 3.1 Shared Party Context (Nexus Global)

```
LegalEntity "Nexus Global (CA)"
├── Cash Pooling: Pool Master for Multi-Currency Pool
├── FX Hedging: PROD-003 FX Forward CAD (active)
├── Trade Finance: PROD-TF-001 Letters of Credit (vendor-hosted)
├── Supply Chain Finance: PROD-SCF-001 Reverse Factoring (vendor-hosted)
└── Payment Rails: Subscribed to ACH + Fedwire + Lynx + CHAPS
```

Single `LegalEntity` node. Multiple `isSubscribedTo` edges to different product instances. One `ownership-chain` traversal serves all product lines.

### 3.2 Shared Account Context (Nexus Global)

```
OperatingAccount "Nexus-CA-CAD-001"
├── Cash Pooling: Member of NotionalPool "Nexus Multi-Currency Pool" (Weight: 23.2%)
├── Payment Rails: Source account for Lynx CAD payments
├── FX Hedging: Settlement account for CAD leg of PROD-003 forwards
└── Intercompany Lending: Receives drawdown from lending facility
```

Single `OperatingAccount` node. Multiple `settlesAgainst` edges from different transaction types. One `isPartOf` edge to pool with weight property.

### 3.3 Shared Regulatory Context (Nexus Global)

```
LegalEntity "Nexus Global (CA)"
├── FINTRAC (Canada): KYC complete, AML screening active
├── FinCEN (US): KYC complete (via Nexus Global USA subsidiary)
├── FCA (UK): KYC complete (via Nexus Global UK Ltd subsidiary)
└── OSFI: Regulatory reporting active
```

Multiple `isKnownBy` and `isSubjectTo` edges. Jurisdictional scope is explicit per edge, not inferred from entity attributes.

---

## 4. Coverage Validation

### 4.1 Entity Coverage Checklist

| Node Type | Cash Pooling | FX Hedging | Intercompany Lending | Payment Rails | Trade Finance | SCF | Status |
|---|---|---|---|---|---|---|---|
| LegalEntity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Complete |
| NaturalPerson | ✅ (signatories) | ✅ (UBO) | ✅ (UBO) | ✅ (signatories) | — | — | Complete |
| FinancialInstitution | — | ✅ (counterparty) | — | ✅ (correspondent) | — | ✅ (financier) | Complete |
| EntityGroup | ✅ (pool scope) | ✅ (hedge scope) | ✅ (lending scope) | — | — | — | Complete |
| ProductBundle | ✅ | ✅ | ✅ | — | — | — | Complete |
| ProductInstance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Complete |
| OperatingAccount | ✅ | ✅ (settlement) | ✅ | ✅ | — | ✅ | Complete |
| VirtualAccount | ✅ (routing) | — | — | ✅ (routing) | — | — | Complete |
| NotionalPool | ✅ | — | — | — | — | — | Complete |
| PhysicalPool | ✅ | — | — | — | — | — | Complete |
| TradingAccount | — | ✅ (positions) | — | — | — | — | Complete |
| Payment | ✅ (sweeps) | — | ✅ (drawdown) | ✅ | — | ✅ (early pay) | Complete |
| FXTransaction | — | ✅ | — | — | — | — | Complete |
| InterestPosting | ✅ | — | ✅ | — | — | — | Complete |
| SweepTransaction | ✅ | — | — | — | — | — | Complete |
| Reversal | ✅ | — | ✅ | ✅ | — | — | Complete |
| RegulatoryObligation | ✅ | ✅ | ✅ | ✅ | — | — | Complete |
| ContractualObligation | ✅ | ✅ | ✅ | — | ✅ (guarantee) | ✅ (invoice) | Complete |
| CreditObligation | — | ✅ (margin) | ✅ (limit) | — | — | ✅ (financing) | Complete |
| SettlementObligation | — | ✅ | — | — | ✅ (LC settle) | — | Complete |
| HumanMandate | ✅ | ✅ | ✅ | ✅ | — | — | Complete |
| AgentMandate | ✅ (auto-sweep) | ✅ (auto-hedge) | ✅ (auto-drawdown) | ✅ (auto-payment) | — | — | Complete |
| **VendorSystem** | — | — | — | — | **✅** | **✅** | **New** |
| TradeTransaction | — | — | — | — | ✅ | — | Complete |

### 4.2 Gap Analysis

**No coverage gaps identified.** All six product areas (4 core + 2 vendor-hosted) map to existing or newly-added node types. The additions vs. original spec:

| New Node Type | Rationale |
|---|---|
| `PhysicalPool` | Distinguish from `NotionalPool`; both needed for Cash Pooling |
| `InterestPosting` | Required for Cash Pooling interest + Intercompany Lending |
| `SweepTransaction` | Cash Pooling operational record |
| `Reversal` | Payment reversal + loan repayment audit trail |
| `SettlementObligation` | FX forward maturity + trade settlement |
| `VendorSystem` | Trade Finance + Supply Chain Finance vendor-hosted systems |

All new types are subtypes of existing parent categories (`Account`, `Transaction`, `Obligation`), except `VendorSystem` which is a new top-level category required by the vendor-hosted constraint.

---

## 5. Vendor-Hosted Mapping Status

Current harmonization status for vendor systems:

| Vendor System | Product | mappingStatus | containmentZone | Notes |
|---|---|---|---|---|
| TradeFinanceVendor | PROD-TF-001 (Letters of Credit) | **Partial** | ✅ | API contract review pending |
| SupplyChainFinanceVendor | PROD-SCF-001 (Reverse Factoring) | **Partial** | ✅ | API contract review pending |

**Resolution path:** Vendor API contract review → Containment Zone schema definition → Progressive mapping strategy per feed. See `[VENDOR-HOSTED]` constraint in canonical spec §13.

---

## 5. Open Questions

1. **VirtualAccount vs. OperatingAccount routing** — when does a payment instruction target a VirtualAccount that then routes to an OperatingAccount? Need to model the routing rule as either an edge property or a separate configuration node.

2. **ProductBundle pricing** — should pricing be a property of `ProductBundle`, `ProductInstance`, or a separate `Pricing` node? Current spec has no pricing node; may need one if pricing is independent of product definition.

3. **Multi-currency accounts** — is a multi-currency account one `OperatingAccount` with currency sub-accounts, or multiple `OperatingAccount` nodes per currency? Impacts pool membership and sweep logic.

4. **Hedge accounting classification** — IFRS 9 hedge effectiveness testing creates a relationship between the hedge instrument and the hedged item. Should this be a dedicated edge type or a property of `SettlementObligation`?

---

_End of Entity Catalog_
