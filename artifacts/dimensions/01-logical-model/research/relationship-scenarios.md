# Relationship Scenarios — GTB Ontology Validation

**Dimension:** 01 — Logical Model & Ontology
**Date:** 2026-05-22
**Status:** Draft
**Reference Client:** Nexus Global (Maya's client)

## Purpose

Validate the edge taxonomy against real-world client scenarios using the **Nexus Global** reference client. Each scenario traces a complete workflow through the graph, identifying required edges, state transitions, and proof chain interactions.

---

## Scenario 1: Nexus Global Onboarding + Cash Pool Setup

**Actor:** Nexus Global (multinational, Canada + US + UK entities)
**Products:** Cash Pooling (PROD-010 DDA + Liquidity Suite) + Payment Rails
**Duration:** ~5 days target

### Graph Operations

**Step 1: Entity Creation**
```
CREATE LegalEntity "Nexus Global" (LEI: 549300NEXG001, Canada HQ)
CREATE LegalEntity "Nexus Global USA" (LEI: 549300NEXG002)
CREATE LegalEntity "Nexus Global USA-East" (LEI: 549300NEXG003)
CREATE LegalEntity "Nexus Global UK Ltd" (LEI: 549300NEXG004)
CREATE NaturalPerson "Jane Smith" (CFO, signing authority)
CREATE NaturalPerson "John Doe" (Treasury Manager)

EDGE: Nexus Global USA → isSubsidiaryOf → Nexus Global
EDGE: Nexus Global USA-East → isSubsidiaryOf → Nexus Global USA
EDGE: Nexus Global UK Ltd → isSubsidiaryOf → Nexus Global
EDGE: Jane Smith → hasSigningAuthority → Nexus Global
EDGE: Jane Smith → hasSigningAuthority → Nexus Global USA
EDGE: John Doe → hasAuthorisedRepresentative → Nexus Global (delegated, limited scope)
```

**Proof chains required:**
- Corporate registry extract → `DECLARATIVE` for LegalEntity creation
- Board resolution → `DECLARATIVE` for signing authority
- KYC documentation → `REGULATORY` for each entity
- Portal onboarding → `BEHAVIOURAL` for consent capture

**Step 2: Regulatory Screening**
```
CREATE Regulator "FINTRAC"
CREATE Regulator "FinCEN"
CREATE Regulator "FCA"
CREATE Regulator "OSFI"

EDGE: Nexus Global → isKnownBy → FINTRAC (KYC complete)
EDGE: Nexus Global → isKnownBy → OSFI (KYC complete)
EDGE: Nexus Global USA → isKnownBy → FinCEN (KYC complete)
EDGE: Nexus Global UK Ltd → isKnownBy → FCA (KYC complete)

EDGE: Nexus Global → isScreenedAgainst → FINTRAC
EDGE: Nexus Global USA → isScreenedAgainst → FinCEN
EDGE: Nexus Global UK Ltd → isScreenedAgainst → FCA

EDGE: Nexus Global → reportsTo → FINTRAC
EDGE: Nexus Global USA → reportsTo → FinCEN
EDGE: Nexus Global UK Ltd → reportsTo → FCA
```

**Step 3: Pool Structure Creation**
```
CREATE ProductBundle "Nexus Global Liquidity Suite"
CREATE ProductInstance "Multi-Currency Pool Config"
CREATE NotionalPool "Nexus Multi-Currency Pool"

CREATE OperatingAccount "Nexus-CA-CAD-001" (owned by Nexus Global, PROD-010 DDA)
CREATE OperatingAccount "Nexus-USE-USD-001" (owned by Nexus Global USA-East, PROD-010 DDA)

EDGE: Nexus Global → owns → Nexus-CA-CAD-001
EDGE: Nexus Global USA-East → owns → Nexus-USE-USD-001
EDGE: Nexus-CA-CAD-001 → isPartOf → Nexus Multi-Currency Pool [weight: 23.2%]
EDGE: Nexus-USE-USD-001 → isPartOf → Nexus Multi-Currency Pool [weight: 35.5%]
EDGE: Nexus Multi-Currency Pool → isGovernedBy → Multi-Currency Pool Config
EDGE: Nexus Global → isSubscribedTo → Nexus Global Liquidity Suite
```

**Step 4: Sweep Rule Configuration**
```
CREATE ContractualObligation "Intraday Sweep Rule"
  properties: { type: "intraday", threshold: 0, direction: "upthenoffset", frequency: "continuous", yieldDelta: "real-time" }

EDGE: CAD Pool Config → isGovernedBy → Intraday Sweep Rule
```

**Step 5: Payment Rail Subscription**
```
CREATE ProductInstance "Lynx Rail Nexus" (CAD)
CREATE ProductInstance "Fedwire Rail Nexus" (USD)
CREATE ProductInstance "CHAPS Rail Nexus" (GBP)

EDGE: Nexus Global → isEligibleFor → Lynx (ProductDefinition)
EDGE: Nexus Global USA → isEligibleFor → Fedwire (ProductDefinition)
EDGE: Nexus Global UK Ltd → isEligibleFor → CHAPS (ProductDefinition)
EDGE: Nexus Global → isSubscribedTo → Lynx Rail Nexus
EDGE: Nexus Global USA → isSubscribedTo → Fedwire Rail Nexus
EDGE: Nexus Global UK Ltd → isSubscribedTo → CHAPS Rail Nexus
EDGE: Lynx Rail Nexus → isDeliveredThrough → H2HChannel
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `isSubsidiaryOf` | 2 | Ownership chain |
| `hasSigningAuthority` | 2 | Authority matrix |
| `hasAuthorisedRepresentative` | 1 | Delegated authority |
| `isKnownBy` | 3 | KYC status per jurisdiction |
| `isScreenedAgainst` | 3 | Sanctions screening |
| `reportsTo` | 2 | Regulatory jurisdiction |
| `owns` | 2 | Account ownership |
| `isPartOf` | 2 | Pool membership |
| `isGovernedBy` | 2 | Product → obligation |
| `isSubscribedTo` | 3 | Product subscriptions |
| `isEligibleFor` | 2 | Rail eligibility |
| `isDeliveredThrough` | 1 | Channel mapping |

**All edges covered by existing taxonomy. No gaps.**

---

## Scenario 2: FX Forward Hedge Execution (PROD-003)

**Actor:** Nexus Global (existing client from Scenario 1)
**Product:** PROD-003 FX Forward (CAD)
**Notional:** $10M USD → CAD

### Graph Operations

**Step 1: Hedge Program Mandate**
```
CREATE HumanMandate "Nexus Global Treasury Hedge Mandate"
  properties: {
    permittedCurrencies: ["USD", "CAD", "GBP"],
    maxNotionalPerContract: 20000000,
    aggregateExposureLimit: 100000000,
    permittedInstruments: ["forward", "spot"],
    authorizedBy: "Jane Smith (CFO)",
    effectiveFrom: "2026-01-01",
    effectiveTo: "2026-12-31"
  }

CREATE AgentMandate "Nexus Auto-Hedge Agent"
  properties: {
    parentMandateId: "Nexus Global Treasury Hedge Mandate",
    permittedOperations: ["forward_initiate", "spot_execute"],
    limits: { maxNotional: 5000000, currency: "USD" },
    constraints: ["same_day_settlement", "no_exotic_structures"]
  }

EDGE: Nexus Auto-Hedge Agent → operatesUnder → Nexus Global Treasury Hedge Mandate
```

**Step 2: Forward Contract Creation (PROD-003)**
```
CREATE ProductInstance "PROD-003 USD/CAD Forward Q3-2026"
  properties: {
    productCode: "PROD-003",
    currencyPair: "USD/CAD",
    notional: 10000000,
    rate: 1.3650,
    maturity: "2026-09-15",
    counterparty: "BANK-INTERNAL"
  }

CREATE SettlementObligation "PROD-003 USD/CAD Forward Settlement"
  properties: {
    settleDate: "2026-09-15",
    deliverCurrency: "USD",
    deliverAmount: 10000000,
    receiveCurrency: "CAD",
    receiveAmount: 13650000
  }

EDGE: Nexus Global → isSubscribedTo → PROD-003 USD/CAD Forward Q3-2026
EDGE: PROD-003 USD/CAD Forward Q3-2026 → creates → PROD-003 USD/CAD Forward Settlement
```

**Step 3: Execution Record**
```
CREATE FXTransaction "FWD-2026-001"
  properties: {
    type: "forward",
    currencyPair: "USD/CAD",
    notional: 10000000,
    rate: 1.3650,
    valueDate: "2026-09-15"
  }

EDGE: FWD-2026-001 → initiatedBy → Nexus Global
EDGE: FWD-2026-001 → executedVia → SWIFTChannel
EDGE: FWD-2026-001 → settlesAgainst → Nexus-CA-CAD-001
```

**Proof chain:**
- Mandate validation → `DELEGATED` (treasury system authority)
- Contract execution → `SYSTEMIC` (bank's trade record)
- Counterparty confirmation → `DECLARATIVE` (confirm receipt)

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `operatesUnder` | 1 | Mandate hierarchy |
| `isSubscribedTo` | 1 | Product subscription |
| `initiatedBy` | 1 | Transaction origin |
| `executedVia` | 1 | Channel |
| `settlesAgainst` | 1 | Settlement account |

**New edge needed?** The `creates` relationship between `ProductInstance` and `SettlementObligation` is not in the original taxonomy. Adding:

```
├── Product
│   └── creates          // ProductInstance → creates → SettlementObligation
```

**Recommendation:** Add `creates` to Product edge category. Forward contracts, options, and structured products all create future settlement obligations at inception.

---

## Scenario 3: Intercompany Loan Drawdown

**Actor:** Nexus Global UK Ltd (borrower) → Nexus Global Canada (lender)
**Product:** Intercompany Revolving Facility
**Amount:** £5M drawdown

### Graph Operations

**Step 1: Facility Establishment** (assumes already set up during onboarding)
```
ProductBundle "Nexus Global Intercompany Facility"
├── ProductInstance "GBP Revolving Credit £20M"
├── ContractualObligation "Master Intercompany Lending Agreement"
└── CreditObligation "Nexus UK Credit Limit £20M"
```

**Step 2: Drawdown Request**
```
CREATE Payment "IC-Drawdown-001"
  properties: {
    type: "intercompany_drawdown",
    amount: 5000000,
    currency: "GBP",
    purpose: "working_capital"
  }

EDGE: IC-Drawdown-001 → initiatedBy → Nexus Global UK Ltd
EDGE: IC-Drawdown-001 → settlesAgainst → Nexus-CA-CAD-001 (lender account)
EDGE: IC-Drawdown-001 → settlesAgainst → Nexus-UK-GBP-001 (borrower account)
```

**Note:** A single payment has two `settlesAgainst` edges — debit from lender, credit to borrower. This is a compound settlement.

**Step 3: Credit Limit Update**
```
// CreditObligation tracks remaining availability
// No new node needed — update properties on existing CreditObligation
// But this violates append-only → need event-sourced update

CREATE ProofRecord on CreditObligation proof chain:
  event: PROOF_ASSERTED
  intentSummary: "Drawdown reduces available facility"
  intentPayload: {
    drawdownRef: "IC-Drawdown-001",
    previousAvailable: 20000000,
    drawdownAmount: 5000000,
    newAvailable: 15000000
  }
```

**Step 4: Interest Accrual** (daily)
```
CREATE InterestPosting "IC-Interest-2026-05-22"
  properties: {
    principal: 5000000,
    rate: 0.0575,  // SOFR + 1.50%
    currency: "GBP",
    accrualDate: "2026-05-22"
  }

EDGE: IC-Interest-2026-05-22 → settlesAgainst → Nexus-UK-GBP-001
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `initiatedBy` | 1 | Drawdown origin |
| `settlesAgainst` | 2 | Compound settlement (debit + credit) |

**Observation:** Compound settlements (one transaction, two accounts) need explicit modeling. Current `settlesAgainst` is singular. Two options:
1. Allow multiple `settlesAgainst` edges per transaction (recommended — matches reality)
2. Create `SettlementLeg` intermediate node

**Recommendation:** Option 1. Multiple `settlesAgainst` edges per transaction. Simpler, no new node type, matches how payments actually work (debit source, credit destination).

---

## Scenario 4: Payment Initiation + Sanctions Screening

**Actor:** Nexus Global Canada
**Action:** International wire payment via SWIFT gpi
**Amount:** CAD 250,000 to supplier in Germany

### Graph Operations

**Step 1: Payment Instruction**
```
CREATE Payment "WIRE-2026-001"
  properties: {
    type: "wire",
    amount: 250000,
    currency: "CAD",
    beneficiary: "Supplier GmbH",
    beneficiaryBank: "DEUTDEFF"
  }

EDGE: WIRE-2026-001 → initiatedBy → John Doe (authorized representative)
EDGE: WIRE-2026-001 → executedVia → SWIFTChannel
EDGE: WIRE-2026-001 → settlesAgainst → Nexus-CA-CAD-001
```

**Step 2: Sanctions Screening** (pre-execution)
```
// Screening is a regulatory obligation check, not a new entity
// Result is appended to proof chain

CREATE ProofRecord on WIRE-2026-001 proof chain:
  event: PROOF_ASSERTED
  proofType: REGULATORY
  intentSummary: "Sanctions screening passed"
  intentPayload: {
    screeningResult: "CLEAR",
    listsChecked: ["OFAC", "UN", "EU", "FINTRAC"],
    screenedAt: "2026-05-22T10:00:00Z"
  }
```

**Step 3: Approval (dual-signature)**
```
// John Doe initiates, Jane Smith approves (dual-signature threshold > CAD 100K)

CREATE ProofRecord:
  proofType: BEHAVIOURAL
  intentSummary: "Payment approved by CFO (dual-signature)"
  intentPayload: {
    approver: "Jane Smith",
    authorityBasis: "SIGNING_AUTHORITY",
    approvalThreshold: "CAD 100,000",
    paymentAmount: "CAD 250,000"
  }
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `initiatedBy` | 1 | Payment origin (NaturalPerson this time) |
| `executedVia` | 1 | SWIFT channel |
| `settlesAgainst` | 1 | Source account |

**All edges covered. Proof chain handles screening + approval without new edges.**

---

## Scenario 5: Relationship Suspension + Reinstatement

**Actor:** Nexus Global UK Ltd
**Trigger:** KYC expiry → suspension → renewal → reinstatement

### State Transition Trace

```
// T0: Active relationship
EDGE: Nexus Global UK Ltd → isKnownBy → FCA
  state: Active
  proofChainId: PC-KYC-UK-001

// T1: KYC expires → auto-suspend
APPEND ProofRecord to PC-KYC-UK-001:
  event: PROOF_EXPIRED
  assertedAt: "2026-06-01T00:00:00Z"
  → Edge state transitions: Active → Suspended

// T2: KYC renewal submitted
APPEND ProofRecord to PC-KYC-UK-001:
  event: PROOF_ASSERTED
  proofType: REGULATORY
  intentSummary: "KYC renewal documentation submitted"
  → Edge state transitions: Suspended → Verified

// T3: KYC verified by compliance officer
APPEND ProofRecord to PC-KYC-UK-001:
  event: PROOF_VERIFIED
  → Edge state transitions: Verified → Active
```

**Validation:** State machine works correctly. No manual state field updates — all transitions driven by proof chain events. Matches lifecycle model:

```
Active → Suspended → Verified → Active ✅
```

---

## Scenario 6: Agent-Initiated Pool Sweep (Autonomous)

**Actor:** Treasury Liquidity Agent (AI)
**Action:** Intraday sweep triggered by balance threshold
**Scope:** Nexus Multi-Currency Pool

### Graph Operations

**Step 1: Pre-Flight Mandate Validation**
```
API CALL: POST /mandates/treasury-liquidity-agent-v2/validate
  payload: {
    operation: "pool_sweep",
    amount: 12000000,
    currency: "CAD",
    pool: "Nexus Multi-Currency Pool"
  }

Response:
  {
    mandateValid: true,
    scopeWithinLimits: true,
    constraints: {
      maxAmount: 50000000,
      sameDayOnly: true,
      noExternalTransfer: true
    },
    validationResult: "APPROVED"
  }
```

**Step 2: Sweep Execution**
```
CREATE SweepTransaction "SWEEP-2026-05-22-001"
  properties: {
    type: "intraday_upthenoffset",
    amount: 12000000,
    currency: "CAD",
    trigger: "balance_below_threshold",
    agentId: "treasury-liquidity-agent-v2"
  }

EDGE: SWEEP-2026-05-22-001 → initiatedBy → Nexus Global (pool master, agent acts on behalf)
EDGE: SWEEP-2026-05-22-001 → wasExecutedBy → treasury-liquidity-agent-v2 (AgentMandate)
EDGE: SWEEP-2026-05-22-001 → settlesAgainst → Nexus-CA-CAD-001
EDGE: SWEEP-2026-05-22-001 → settlesAgainst → Nexus-USE-USD-001
```

**Step 3: Agentic Proof Record**
```
APPEND ProofRecord to SWEEP-2026-05-22-001 proof chain:
  proofType: AGENTIC
  intentPayload: {
    agentId: "treasury-liquidity-agent-v2",
    mandateRef: "MANDATE-ACME-TREASURY-001",
    delegationChain: [
      { actor: "Jane Smith (CFO)", authorityBasis: "TreasuryPolicy-2026", grantedAt: "2026-01-01" },
      { actor: "Treasury System", authorityBasis: "SystemMandate-Nexus-001", grantedAt: "2026-01-15" },
      { actor: "treasury-liquidity-agent-v2", authorityBasis: "AgentScope-v2", grantedAt: "2026-02-01" }
    ],
    scopeAtExecution: {
      permittedOperations: ["pool_sweep"],
      limits: { maxAmount: 50000000, currency: "CAD" },
      constraints: ["same_day_only", "no_external_transfer"]
    },
    decisionTrace: {
      observedCondition: "Pool balance CAD 2.1M below threshold CAD 5M at 14:00",
      appliedRule: "AutoSweep-Rule-7",
      determinedAction: "Sweep CAD 12M from Nexus-USE-USD-001 to Nexus-CA-CAD-001"
    },
    scopeViolations: []
  }
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `initiatedBy` | 1 | On behalf of pool master |
| `wasExecutedBy` | 1 | Agent execution record |
| `settlesAgainst` | 2 | Compound sweep |

**All edges covered. Agentic proof chain is the critical differentiator — full delegation trace from human to agent.**

---

## Scenario 7: Cross-LOB Client View (Nexus Global)

**Trigger:** Relationship manager requests single view of Nexus Global across CB + CM + WM

### Graph Traversal

```
START: LegalEntity "Nexus Global (CA)" (LEI: 549300NEXG001)

1. Ownership chain traversal:
   Nexus Global (CA) ← isSubsidiaryOf — Nexus Global USA ← isSubsidiaryOf — Nexus Global USA-East
   Nexus Global (CA) ← isSubsidiaryOf — Nexus Global UK Ltd
   → 4 entities in group

2. Product subscriptions (all entities):
   Nexus Global (CA): PROD-003 FX Forward CAD, Cash Pool Master, PROD-TF-001 Trade Finance [VENDOR]
   Nexus Global USA: PROD-010 DDA, Fedwire Rail, Intercompany Facility
   Nexus Global USA-East: PROD-010 DDA, Pool Member (35.5% weight)
   Nexus Global UK Ltd: PROD-004 FX Hedge GBP, CHAPS Rail, Intercompany Borrower, PROD-SCF-001 SCF [VENDOR]

3. Active accounts:
   Nexus-CA-CAD-001 (CAD) — member of Nexus Multi-Currency Pool (23.2%)
   Nexus-USE-USD-001 (USD) — member of Nexus Multi-Currency Pool (35.5%)
   Nexus-UK-GBP-001 (GBP) — intercompany borrower

4. Active transactions (last 30 days):
   Sweeps: 45
   FX Forwards (PROD-003): 3
   Intercompany Drawdowns: 2
   Wire Payments: 127

5. Regulatory exposure:
   FINTRAC (Canada): KYC complete, AML active
   FinCEN (US): KYC complete, BOI filed
   FCA (UK): KYC complete
   OSFI (Canada): Regulatory reporting active

6. Open obligations:
   FX Forward Settlement (PROD-003): $10M USD/CAD due 2026-09-15
   Intercompany Credit: £5M outstanding of £20M limit
   Trade Finance (PROD-TF-001): 2 active LCs [vendor-hosted]
   Supply Chain Finance (PROD-SCF-001): 3 supplier invoices [vendor-hosted]
```

**API calls to produce this view:**
```
GET /entities/by-lei/549300NEXG001
GET /entities/Nexus-CA/ownership-chain
GET /entities/Nexus-CA/relationships?states=active
GET /entities/Nexus-USA/relationships?states=active
GET /entities/Nexus-UK/relationships?states=active
GET /entities/Nexus-CA/regulatory-exposure
```

**Validation:** Graph traversal produces complete cross-LOB view without joining operational databases. Single source of truth validated.

---

## Scenario 8: Vendor-Hosted Trade Finance Integration `[VENDOR-HOSTED]`

**Actor:** Nexus Global (Canada)
**Product:** PROD-TF-001 Letters of Credit (Vendor-Hosted)
**Action:** New LC issuance via vendor system

### Graph Operations

**Step 1: Vendor System Registration**
```
CREATE VendorSystem "TradeFinanceVendor" (TradeFinanceSystem)
  properties: {
    vendorName: "TradeTech Solutions",
    containmentZone: true,
    vendorSchemaRef: "TF-API-v2.1",
    apiVersion: "2.1",
    mappingStatus: "Partial"
  }

CREATE ProductInstance "PROD-TF-001 Letters of Credit"
  properties: {
    productCode: "PROD-TF-001",
    hostingModel: "VendorHosted",
    vendorSystemId: "TradeFinanceVendor"
  }

EDGE: PROD-TF-001 → isHostedBy → TradeFinanceVendor
EDGE: TradeFinanceVendor → isMappedTo → PROD-TF-001 [mappingStatus: Partial]
EDGE: Nexus Global → isSubscribedTo → PROD-TF-001
```

**Step 2: LC Issuance (Vendor-Initiated)**
```
// Vendor system creates LC; event flows through Containment Zone
CREATE TradeTransaction "LC-2026-001"
  properties: {
    type: "letter_of_credit",
    amount: 1000000,
    currency: "USD",
    beneficiary: "European Supplier AG",
    expiryDate: "2026-12-31",
    vendorRef: "TFV-LC-98765",   // original vendor reference
    containmentZone: true
  }

EDGE: LC-2026-001 → initiatedBy → Nexus Global
EDGE: LC-2026-001 → creates → SettlementObligation (LC expiry)
```

**Step 3: Progressive Mapping**
```
// As vendor data is harmonized, mapping status advances
UPDATE Edge (TradeFinanceVendor → isMappedTo → PROD-TF-001):
  mappingStatus: "Partial" → "Complete"
  mappedAt: "2026-06-15T00:00:00Z"
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `isHostedBy` | 1 | **New** — vendor system hosting |
| `isMappedTo` | 1 | **New** — progressive mapping |
| `initiatedBy` | 1 | Standard |
| `creates` | 1 | LC → SettlementObligation |

**Key observation:** Vendor-hosted systems require the new `VendorSystem` node type and `isHostedBy`/`isMappedTo` edges. Containment Zone flag ensures vendor schema volatility is isolated from Core model.

---

## Scenario 9: Vendor-Hosted Supply Chain Finance Integration `[VENDOR-HOSTED]`

**Actor:** Nexus Global (as Buyer in reverse factoring program)
**Product:** PROD-SCF-001 Reverse Factoring (Vendor-Hosted)
**Action:** Supplier early payment via vendor SCF platform

### Graph Operations

**Step 1: SCF Vendor Registration**
```
CREATE VendorSystem "SupplyChainFinanceVendor" (SupplyChainFinanceSystem)
  properties: {
    vendorName: "SCF Connect",
    containmentZone: true,
    vendorSchemaRef: "SCF-API-v1.4",
    apiVersion: "1.4",
    mappingStatus: "Partial"
  }

CREATE ProductInstance "PROD-SCF-001 Reverse Factoring"
  properties: {
    productCode: "PROD-SCF-001",
    hostingModel: "VendorHosted",
    vendorSystemId: "SupplyChainFinanceVendor"
  }

EDGE: PROD-SCF-001 → isHostedBy → SupplyChainFinanceVendor
EDGE: SupplyChainFinanceVendor → isMappedTo → PROD-SCF-001 [mappingStatus: Partial]
EDGE: Nexus Global → isSubscribedTo → PROD-SCF-001
```

**Step 2: Invoice Financing (Vendor-Initiated)**
```
CREATE Payment "SCF-EarlyPay-001"
  properties: {
    type: "supplier_early_payment",
    amount: 500000,
    currency: "USD",
    supplier: "Component Supplier Inc",
    vendorRef: "SCF-INV-12345",
    containmentZone: true
  }

EDGE: SCF-EarlyPay-001 → initiatedBy → SupplyChainFinanceVendor (on behalf of Nexus Global)
EDGE: SCF-EarlyPay-001 → settlesAgainst → Supplier OperatingAccount
```

### Validation Result

| Edge Type Used | Count | Notes |
|---|---|---|
| `isHostedBy` | 1 | **New** — vendor system hosting |
| `isMappedTo` | 1 | **New** — progressive mapping |
| `initiatedBy` | 1 | Vendor acts on behalf of client |
| `settlesAgainst` | 1 | Supplier account |

**Key observation:** Same Containment Zone pattern as Trade Finance. Vendor reference (`vendorRef`) preserved alongside canonical properties for traceability.

---

## Summary: Edge Taxonomy Validation

| Edge Category | Edges Used in Scenarios | Edges Not Yet Tested |
|---|---|---|
| Ownership | `isSubsidiaryOf` ✅ | `isUltimateParentOf`, `hasBeneficialOwner` |
| Authority | `hasSigningAuthority` ✅, `hasAuthorisedRepresentative` ✅, `delegatesTo` | |
| Product | `isSubscribedTo` ✅, `isEligibleFor` ✅, `isDeliveredThrough` ✅ | |
| Account | `owns` ✅, `isPartOf` ✅, `isGovernedBy` ✅ | `hasBalance` |
| Transaction | `initiatedBy` ✅, `executedVia` ✅, `settlesAgainst` ✅ | |
| Regulatory | `isKnownBy` ✅, `isScreenedAgainst` ✅, `reportsTo` ✅, `isSubjectTo` | |
| Agentic | `operatesUnder` ✅, `wasExecutedBy` ✅ | |
| **Vendor Integration** | `isHostedBy` ✅, `isMappedTo` ✅ | `containmentStatus` |

### Recommended Additions

1. **`creates`** (Product → SettlementObligation) — validated by Scenario 2
2. **Multiple `settlesAgainst` edges per transaction** — validated by Scenarios 3, 6
3. **`isHostedBy`** (ProductInstance → VendorSystem) — validated by Scenarios 8, 9
4. **`isMappedTo`** (VendorSystem → ProductInstance) — validated by Scenarios 8, 9

### Recommended Testing

Run scenarios 1–4 through the graph store (Neo4j or chosen implementation) to validate:
- Query performance on ownership-chain traversal (Scenario 7)
- Proof chain append latency under concurrent load (Scenario 4)
- Point-in-time query accuracy after suspension/reinstatement (Scenario 5)

---

_End of Relationship Scenarios_
