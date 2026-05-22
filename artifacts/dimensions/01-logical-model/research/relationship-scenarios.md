# Relationship Scenarios — GTB Ontology Validation

**Dimension:** 01 — Logical Model & Ontology
**Date:** 2026-05-22
**Status:** Draft

## Purpose

Validate the edge taxonomy against real-world client scenarios. Each scenario traces a complete workflow through the graph, identifying required edges, state transitions, and proof chain interactions.

---

## Scenario 1: New Client Onboarding + Cash Pool Setup

**Actor:** ACME Corp (multinational, Canada + US + UK entities)
**Products:** Cash Pooling + Payment Rails
**Duration:** ~5 days target

### Graph Operations

**Step 1: Entity Creation**
```
CREATE LegalEntity "ACME Corp Canada" (LEI: 549300XXX)
CREATE LegalEntity "ACME Corp USA" (LEI: 549300YYY)
CREATE LegalEntity "ACME UK Ltd" (LEI: 549300ZZZ)
CREATE NaturalPerson "Jane Smith" (CFO, signing authority)
CREATE NaturalPerson "John Doe" (Treasury Manager)

EDGE: ACME USA → isSubsidiaryOf → ACME Canada
EDGE: ACME UK → isSubsidiaryOf → ACME USA
EDGE: Jane Smith → hasSigningAuthority → ACME Canada
EDGE: Jane Smith → hasSigningAuthority → ACME USA
EDGE: John Doe → hasAuthorisedRepresentative → ACME Canada (delegated, limited scope)
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

EDGE: ACME Canada → isKnownBy → FINTRAC (KYC complete)
EDGE: ACME USA → isKnownBy → FinCEN (KYC complete)
EDGE: ACME UK → isKnownBy → FCA (KYC pending)

EDGE: ACME Canada → isScreenedAgainst → FINTRAC
EDGE: ACME USA → isScreenedAgainst → FinCEN
EDGE: ACME UK → isScreenedAgainst → FCA

EDGE: ACME Canada → reportsTo → FINTRAC
EDGE: ACME USA → reportsTo → FinCEN
```

**Step 3: Pool Structure Creation**
```
CREATE ProductBundle "ACME CAD Cash Pool"
CREATE ProductInstance "CAD Pool Config"
CREATE NotionalPool "ACME-CAD-Pool"

CREATE OperatingAccount "ACME-CA-OP-001" (owned by ACME Canada)
CREATE OperatingAccount "ACME-US-OP-001" (owned by ACME USA)

EDGE: ACME Canada → owns → ACME-CA-OP-001
EDGE: ACME USA → owns → ACME-US-OP-001
EDGE: ACME-CA-OP-001 → isPartOf → ACME-CAD-Pool
EDGE: ACME-US-OP-001 → isPartOf → ACME-CAD-Pool
EDGE: ACME-CAD-Pool → isGovernedBy → CAD Pool Config
EDGE: ACME Canada → isSubscribedTo → ACME CAD Cash Pool
```

**Step 4: Sweep Rule Configuration**
```
CREATE ContractualObligation "Intraday Sweep Rule"
  properties: { type: "intraday", threshold: 0, direction: "upthenoffset", frequency: "continuous" }

EDGE: CAD Pool Config → isGovernedBy → Intraday Sweep Rule
```

**Step 5: Payment Rail Subscription**
```
CREATE ProductInstance "ACH Rail ACME"
CREATE ProductInstance "Fedwire Rail ACME"

EDGE: ACME Canada → isEligibleFor → ACH (ProductDefinition)
EDGE: ACME USA → isEligibleFor → Fedwire (ProductDefinition)
EDGE: ACME Canada → isSubscribedTo → ACH Rail ACME
EDGE: ACME USA → isSubscribedTo → Fedwire Rail ACME
EDGE: ACH Rail ACME → isDeliveredThrough → H2HChannel
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

## Scenario 2: FX Forward Hedge Execution

**Actor:** ACME Corp USA (existing client from Scenario 1)
**Product:** FX Hedging (USD/CAD 12-month forward)
**Notional:** $10M USD → CAD

### Graph Operations

**Step 1: Hedge Program Mandate**
```
CREATE HumanMandate "ACME Treasury Hedge Mandate"
  properties: {
    permittedCurrencies: ["USD", "CAD", "GBP"],
    maxNotionalPerContract: 20000000,
    aggregateExposureLimit: 100000000,
    permittedInstruments: ["forward", "spot"],
    authorizedBy: "Jane Smith (CFO)",
    effectiveFrom: "2026-01-01",
    effectiveTo: "2026-12-31"
  }

CREATE AgentMandate "Auto-Hedge Agent"
  properties: {
    parentMandateId: "ACME Treasury Hedge Mandate",
    permittedOperations: ["forward_initiate", "spot_execute"],
    limits: { maxNotional: 5000000, currency: "USD" },
    constraints: ["same_day_settlement", "no_exotic_structures"]
  }

EDGE: Auto-Hedge Agent → operatesUnder → ACME Treasury Hedge Mandate
```

**Step 2: Forward Contract Creation**
```
CREATE ProductInstance "USD/CAD Forward Q3-2026"
  properties: {
    currencyPair: "USD/CAD",
    notional: 10000000,
    rate: 1.3650,
    maturity: "2026-09-15",
    counterparty: "BANK-INTERNAL"
  }

CREATE SettlementObligation "USD/CAD Forward Settlement"
  properties: {
    settleDate: "2026-09-15",
    deliverCurrency: "USD",
    deliverAmount: 10000000,
    receiveCurrency: "CAD",
    receiveAmount: 13650000
  }

EDGE: ACME USA → isSubscribedTo → USD/CAD Forward Q3-2026
EDGE: USD/CAD Forward Q3-2026 → creates → USD/CAD Forward Settlement
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

EDGE: FWD-2026-001 → initiatedBy → ACME USA
EDGE: FWD-2026-001 → executedVia → SWIFTChannel
EDGE: FWD-2026-001 → settlesAgainst → ACME-US-OP-001
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

**Actor:** ACME UK Ltd (borrower) → ACME Corp Canada (lender)
**Product:** Intercompany Revolving Facility
**Amount:** £5M drawdown

### Graph Operations

**Step 1: Facility Establishment** (assumes already set up during onboarding)
```
ProductBundle "ACME Intercompany Facility"
├── ProductInstance "GBP Revolving Credit £20M"
├── ContractualObligation "Master Intercompany Lending Agreement"
└── CreditObligation "ACME UK Credit Limit £20M"
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

EDGE: IC-Drawdown-001 → initiatedBy → ACME UK
EDGE: IC-Drawdown-001 → settlesAgainst → ACME-CA-OP-001 (lender account)
EDGE: IC-Drawdown-001 → settlesAgainst → ACME-UK-OP-001 (borrower account)
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

EDGE: IC-Interest-2026-05-22 → settlesAgainst → ACME-UK-OP-001
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

**Actor:** ACME Corp Canada
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
EDGE: WIRE-2026-001 → settlesAgainst → ACME-CA-OP-001
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

**Actor:** ACME UK Ltd
**Trigger:** KYC expiry → suspension → renewal → reinstatement

### State Transition Trace

```
// T0: Active relationship
EDGE: ACME UK → isKnownBy → FCA
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
**Scope:** ACME-CAD-Pool

### Graph Operations

**Step 1: Pre-Flight Mandate Validation**
```
API CALL: POST /mandates/treasury-liquidity-agent-v2/validate
  payload: {
    operation: "pool_sweep",
    amount: 12000000,
    currency: "CAD",
    pool: "ACME-CAD-Pool"
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

EDGE: SWEEP-2026-05-22-001 → initiatedBy → ACME Canada (pool master, agent acts on behalf)
EDGE: SWEEP-2026-05-22-001 → wasExecutedBy → treasury-liquidity-agent-v2 (AgentMandate)
EDGE: SWEEP-2026-05-22-001 → settlesAgainst → ACME-CA-OP-001
EDGE: SWEEP-2026-05-22-001 → settlesAgainst → ACME-US-OP-001
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
      { actor: "Treasury System", authorityBasis: "SystemMandate-ACME-001", grantedAt: "2026-01-15" },
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
      determinedAction: "Sweep CAD 12M from ACME-US-OP-001 to ACME-CA-OP-001"
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

## Scenario 7: Cross-LOB Client View

**Trigger:** Relationship manager requests single view of ACME Corp across CB + CM + WM

### Graph Traversal

```
START: LegalEntity "ACME Corp Canada" (LEI: 549300XXX)

1. Ownership chain traversal:
   ACME Canada ← isSubsidiaryOf — ACME USA ← isSubsidiaryOf — ACME UK
   → 3 entities in group

2. Product subscriptions (all entities):
   ACME Canada: Cash Pool (CB), ACH Rail (CB)
   ACME USA: FX Hedge Program (CM), Fedwire Rail (CB), Intercompany Facility (CB)
   ACME UK: Intercompany Borrower (CB)

3. Active accounts:
   ACME-CA-OP-001 (CAD) — member of ACME-CAD-Pool
   ACME-US-OP-001 (USD) — member of ACME-CAD-Pool
   ACME-UK-OP-001 (GBP) — intercompany borrower

4. Active transactions (last 30 days):
   Sweeps: 45
   FX Forwards: 3
   Intercompany Drawdowns: 2
   Wire Payments: 127

5. Regulatory exposure:
   FINTRAC (Canada): KYC complete, AML active
   FinCEN (US): KYC complete, BOI filed
   FCA (UK): KYC pending

6. Open obligations:
   FX Forward Settlement: $10M USD/CAD due 2026-09-15
   Intercompany Credit: £5M outstanding of £20M limit
```

**API calls to produce this view:**
```
GET /entities/by-lei/549300XXX
GET /entities/ACME-CA/ownership-chain
GET /entities/ACME-CA/relationships?states=active
GET /entities/ACME-USA/relationships?states=active
GET /entities/ACME-UK/relationships?states=active
GET /entities/ACME-CA/regulatory-exposure
```

**Validation:** Graph traversal produces complete cross-LOB view without joining operational databases. Single source of truth validated.

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

### Recommended Additions

1. **`creates`** (Product → SettlementObligation) — validated by Scenario 2
2. **Multiple `settlesAgainst` edges per transaction** — validated by Scenarios 3, 6

### Recommended Testing

Run scenarios 1–4 through the graph store (Neo4j or chosen implementation) to validate:
- Query performance on ownership-chain traversal (Scenario 7)
- Proof chain append latency under concurrent load (Scenario 4)
- Point-in-time query accuracy after suspension/reinstatement (Scenario 5)

---

_End of Relationship Scenarios_
