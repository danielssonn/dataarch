# Proof Taxonomy for Global Transaction Banking
## Beyond Proof of Fact — A Complete Proof Model for Nexus Global

**Date:** 2026-05-23
**Context:** Extending the existing 6-type proof taxonomy (Dim 05) to cover the full spectrum of proofs applicable to Maya, Nexus Global, and the broader GTB domain.
**Status:** Research draft — to be folded into Dim 05 spec

---

## 1. Starting Point: Existing Taxonomy (Dim 05 §3.2)

Our current proof taxonomy is organized by **source of assertion** — who/what is making the claim:

| Type | Source | Example |
|------|--------|---------|
| `DECLARATIVE` | Human via formal instrument | Signed agreement, board resolution |
| `BEHAVIOURAL` | Human via authenticated action | Portal click-through, consent capture |
| `DELEGATED` | Authority chain | OAuth scope, power of attorney |
| `AGENTIC` | Non-human under mandate | AI agent action under scoped mandate |
| `SYSTEMIC` | Bank's own execution record | Audit log, transaction record |
| `REGULATORY` | Third-party attestation | LEI registry, sanctions screening |

This taxonomy answers: **"Who said it?"**

But in transaction banking, we need to also answer: **"What kind of truth is being claimed?"**

The gap: Proof of Fact (identity/KYC) and Proof of Intent (client instruction) are both captured by the existing taxonomy, but they represent fundamentally different *kinds* of proof that serve different regulatory, operational, and strategic purposes.

---

## 2. Proof Taxonomy by Kind of Truth

This is the new dimension. Organized by **what is being proven**, not who is proving it. Each kind maps to a regulatory domain, a business process, and a proof chain pattern.

### 2.1 Proof of Identity (Who You Are)

**What it proves:** The party presenting themselves is who they claim to be.

**Regulatory domain:** KYC, CDD, AML, PEP screening, UBO identification.

**Existing proof types that serve this:** `REGULATORY` (LEI registry, passport verification), `DECLARATIVE` (signed identity declaration).

**Nexus Global scenario:**
```
Maya (NaturalPerson) presents:
  ├── Passport scan → REGULATORY proof (government-issued)
  ├── LEI for Nexus Global USA → REGULATORY proof (GLEIF registry)
  ├── Signed beneficial ownership declaration → DECLARATIVE proof
  └── Selfie + liveness check → BEHAVIOURAL proof (digital onboarding)

Proof chain establishes:
  "Maya IS Maya, AND Maya IS the authorized signatory for Nexus Global USA"
```

**Chain pattern:** Multiple proofs converge on a single identity claim. The chain is fan-in — several independent proofs must all validate before identity is established.

**Key risk:** Identity proofs expire. Passport expires, LEI lapses, PEP status changes. Proof chains must track validity windows, not just creation time.

---

### 2.2 Proof of Authority (What You Can Do)

**What it proves:** The actor has the right to perform a specific action on behalf of a party.

**Regulatory domain:** Mandate management, signing authority, board resolutions, power of attorney, RBAC.

**Existing proof types that serve this:** `DELEGATED` (OAuth scope, power of attorney), `DECLARATIVE` (board resolution).

**Nexus Global scenario:**
```
Maya initiates a $2M FX forward:
  ├── Board resolution authorizing Maya to execute FX up to $5M → DECLARATIVE
  ├── Maya's signing mandate (active, not expired) → DELEGATED
  ├── Dual-signature rule: transaction > $1M requires second signer → DECLARATIVE
  └── Co-signer John Doe authenticated → BEHAVIOURAL

Proof chain establishes:
  "Maya HAS AUTHORITY to execute FX forwards up to $5M, AND this $2M transaction IS WITHIN her mandate"
```

**Chain pattern:** Hierarchy. Authority proofs form a tree — board resolution → mandate → specific action scope. Each level must be valid for the leaf action to proceed.

**Key risk:** Authority is temporal and conditional. Mandates expire, board resolutions are superseded, transaction limits change. Pre-flight validation must check current state, not just existence.

---

### 2.3 Proof of Intent (What You Asked For)

**What it proves:** The client's instruction was what they intended — capturing the exact request at the moment it was made.

**Regulatory domain:** Payment execution, trade settlement, dispute resolution, non-repudiation.

**Existing proof types that serve this:** `BEHAVIOURAL` (portal submission with UI hash), `DECLARATIVE` (signed payment instruction), `SYSTEMIC` (channel log).

**Nexus Global scenario:**
```
Maya submits payment instruction via Digital Portal:
  ├── Screenshot/UI hash of configured payment → BEHAVIOURAL
  │     { recipient: "ABC Corp", amount: 150000, currency: "USD", purpose: "Invoice #2026-0451" }
  ├── Maya's authentication at time of submission → BEHAVIOURAL (JWT + MFA)
  ├── Channel log: DigitalPortal, session ID, timestamp → SYSTEMIC
  └── Payment instruction signed (digital signature) → DECLARATIVE

Proof chain establishes:
  "Maya INTENDED to pay ABC Corp $150K USD for Invoice #2026-0451, AT this exact moment, THROUGH this channel"
```

**Chain pattern:** Snapshot. The proof captures a point-in-time state of intent. Unlike identity (which persists) or authority (which is hierarchical), intent is ephemeral — it exists only for the duration of the instruction.

**Key risk:** Dispute resolution. If the bank executes differently from what was proven, the proof chain is the arbiter. "The bank paid $150K to ABC Corp" vs "I instructed $150K to ABC Corp" — the proof chain resolves the conflict.

---

### 2.4 Proof of Execution (What Was Done)

**What it proves:** The bank executed the instruction correctly, completely, and within the agreed terms.

**Regulatory domain:** Operational compliance, service level agreements, settlement finality, audit.

**Existing proof types that serve this:** `SYSTEMIC` (transaction record, settlement confirmation).

**Nexus Global scenario:**
```
Bank executes Maya's payment:
  ├── SWIFT MT103 sent → SYSTEMIC (message ID, timestamp, value date)
  ├── Settlement confirmation from receiving bank → REGULATORY (counterparty attestation)
  ├── Fee applied: $25 (per published fee schedule) → SYSTEMIC
  ├── Exchange rate applied: 1.3520 USD/CAD (per agreed rate) → SYSTEMIC
  └── Execution timestamp vs instruction timestamp: 4.2 seconds → SYSTEMIC

Proof chain establishes:
  "The bank DID execute Maya's payment instruction CORRECTLY — same recipient, same amount, within agreed SLA"
```

**Chain pattern:** Verification against intent. The execution proof chain references the intent proof chain. The comparison between them is the compliance check: intent → execution = delta. Delta should be zero (or within tolerance).

**Key risk:** Execution drift. Fee discrepancies, rate slippage, timing delays. The proof chain captures the delta so it can be explained, contested, or compensated.

---

### 2.5 Proof of Compliance (Rules Were Followed)

**What it proves:** The action satisfied all applicable regulatory, contractual, and policy constraints at the time of execution.

**Regulatory domain:** AML screening, sanctions checks, transfer pricing, regulatory reporting, conduct rules.

**Existing proof types that serve this:** `REGULATORY` (sanctions screening result), `SYSTEMIC` (compliance check log).

**Nexus Global scenario:**
```
Before Maya's $150K payment executes:
  ├── Sanctions screen: recipient ABC Corp → CLEAR → REGULATORY
  ├── AML check: transaction pattern analysis → LOW RISK → SYSTEMIC
  ├── PEP check: Maya → NOT PEP → REGULATORY
  ├── Transfer pricing: intercompany rate arm's-length → SYSTEMIC (function evaluation)
  ├── FATCA/CRS: withholding tax determined → 0% → REGULATORY
  └── Internal policy: single-signature threshold for < $500K → COMPLIANT → SYSTEMIC

Proof chain establishes:
  "The payment COMPLIED with all applicable rules — sanctions, AML, PEP, transfer pricing, FATCA, internal policy"
```

**Chain pattern:** Gate. Compliance proofs must all pass before execution proceeds. If any gate fails, the action is blocked. The proof chain records both the check and the result.

**Key risk:** Compliance rules change. A transaction that was compliant at execution time may appear non-compliant when reviewed against rules that existed later. Proof chains must be temporally anchored — "compliant as of execution timestamp."

---

### 2.6 Proof of Consent (You Agreed to This)

**What it proves:** The party explicitly agreed to terms, conditions, data processing, or product enrollment.

**Regulatory domain:** GDPR consent, product terms acceptance, data sharing agreements, marketing opt-in/out.

**Existing proof types that serve this:** `BEHAVIOURAL` (click-through with consent capture), `DECLARATIVE` (signed terms acceptance).

**Nexus Global scenario:**
```
Maya enrolls in FX Forward product:
  ├── Terms & conditions displayed (UI hash + version) → BEHAVIOURAL
  ├── Maya clicks "I Agree" (timestamped, authenticated) → BEHAVIOURAL
  ├── GDPR data processing consent captured → BEHAVIOURAL
  ├── Product-specific risk disclosure acknowledged → BEHAVIOURAL
  └── Consent scope: "FX products only, not trade finance" → DECLARATIVE (scope definition)

Proof chain establishes:
  "Maya CONSENTED to the specific terms of FX Forward enrollment, WITH explicit scope limitations"
```

**Chain pattern:** Scoped assertion. Consent is never blanket — it always has scope (what products, what data, what jurisdiction). The proof chain must capture the scope boundaries, not just the consent event.

**Key risk:** Consent withdrawal. Maya can revoke consent at any time (GDPR right). The proof chain must track the consent lifecycle: granted → active → withdrawn. Post-withdrawal actions must not reference expired consent.

---

### 2.7 Proof of Ownership (You Own This)

**What it proves:** A party has a documented ownership or control relationship over an asset, entity, or right.

**Regulatory domain:** UBO identification, collateral ownership, account ownership, intellectual property, beneficial ownership.

**Existing proof types that serve this:** `DECLARATIVE` (shareholder registry, articles of incorporation), `REGULATORY` (corporate registry filing).

**Nexus Global scenario:**
```
Nexus Global USA claims ownership of OperatingAccount-USA:
  ├── Account opening agreement (signed by authorized signatory) → DECLARATIVE
  ├── Corporate registry filing confirming Nexus Global USA's legal existence → REGULATORY
  ├── Board resolution authorizing account opening → DECLARATIVE
  └── Beneficial ownership: Maya (25%), John Doe (25%), Nexus Global Canada (50%) → DECLARATIVE

Proof chain establishes:
  "Nexus Global USA OWNS OperatingAccount-USA, AND the beneficial owners ARE Maya, John Doe, and Nexus Global Canada"
```

**Chain pattern:** Chain of title. Ownership proofs form a chain from the asset back through intermediaries to the ultimate owners. Each link must be independently proven.

**Key risk:** Ownership changes. M&A activity, share transfers, trust restructuring. The proof chain must support temporal queries: "Who owned this account as of 2026-03-15?"

---

### 2.8 Proof of Solvency (You Can Pay)

**What it proves:** A party has sufficient financial capacity to fulfill an obligation.

**Regulatory domain:** Credit assessment, margin calls, counterparty risk, settlement capacity.

**Existing proof types that serve this:** `REGULATORY` (credit bureau response), `SYSTEMIC` (account balance snapshot).

**Nexus Global scenario:**
```
Maya requests $2M FX forward:
  ├── Credit line check: $10M approved, $6M utilized → SYSTEMIC
  ├── Available capacity: $4M > $2M requested → SYSTEMIC (function evaluation)
  ├── Collateral: OperatingAccount-USA balance $5M → SYSTEMIC
  ├── Credit rating: A- (S&P, current as of 2026-04-01) → REGULATORY
  └── Counterparty limit: no concentration risk → SYSTEMIC

Proof chain establishes:
  "Nexus Global IS SOLVENT to support a $2M FX forward — credit line available, collateral posted, rating current"
```

**Chain pattern:** Point-in-time assessment. Solvency is evaluated at the moment of request. It may change seconds later. The proof chain captures the snapshot, not a persistent truth.

**Key risk:** Rapid deterioration. A solvency proof valid at 10:00 AM may be invalid at 10:05 AM if a large payment executes. Proof chains for solvency must have very short validity windows.

---

### 2.9 Proof of Delivery (You Received It)

**What it proves:** Information, funds, or assets were successfully delivered to the intended recipient.

**Regulatory domain:** Payment settlement, trade document delivery, notification delivery, SWIFT message confirmation.

**Existing proof types that serve this:** `SYSTEMIC` (delivery confirmation log), `REGULATORY` (counterparty acknowledgment).

**Nexus Global scenario:**
```
Payment to ABC Corp confirmed:
  ├── SWIFT MT103 delivery receipt from receiving bank → REGULATORY
  ├── ABC Corp's bank confirms credit to ABC Corp's account → REGULATORY
  ├── Notification sent to Maya (email + portal) → SYSTEMIC
  └── Maya acknowledges receipt (portal click) → BEHAVIOURAL

Proof chain establishes:
  "The payment WAS DELIVERED to ABC Corp, AND Maya WAS NOTIFIED of completion"
```

**Chain pattern:** Acknowledgment loop. Delivery proof requires confirmation from the receiving party (or their agent). Without acknowledgment, delivery is unconfirmed.

**Key risk:** Silent failure. Receiving bank processes payment but doesn't send confirmation. Proof chain shows execution but not delivery. May need timeout-based fallback to presumed delivery.

---

### 2.10 Proof of Remediation (You Fixed It)

**What it proves:** When something went wrong, it was identified, addressed, and corrected within agreed terms.

**Regulatory domain:** Error resolution, complaint handling, regulatory remediation, service credit, compensating actions.

**Existing proof types that serve this:** `SYSTEMIC` (remediation log), `DECLARATIVE` (client acceptance of correction).

**Nexus Global scenario:**
```
FX rate discrepancy detected:
  ├── Original rate applied: 1.3520 (should have been 1.3535 per agreed rate) → SYSTEMIC
  ├── Discrepancy identified: 0.0015 adverse to client → SYSTEMIC (automated detection)
  ├── Correcting payment issued: $225 difference → SYSTEMIC
  ├── Maya acknowledges correction → BEHAVIOURAL
  └── Root cause documented: rate feed latency → SYSTEMIC

Proof chain establishes:
  "The error WAS identified, WAS corrected, AND the correction WAS accepted by the client"
```

**Chain pattern:** Closed loop. Remediation proof chains reference the original execution proof chain and demonstrate that the delta has been resolved. The chain shows: error → detection → correction → acceptance.

**Key risk:** Incomplete remediation. The correction may address the financial impact but not the root cause. Proof chains should distinguish between symptom remediation and root cause resolution.

---

## 3. Cross-Cutting Proof Dimensions

Beyond the "what" (kind of truth) and "who" (source of assertion), proof chains in GTB must also capture three cross-cutting dimensions:

### 3.1 Temporal Dimension

Every proof has a temporal profile:

| Dimension | Description | Example |
|-----------|-------------|---------|
| **assertedAt** | When the proof was created | Maya signed the agreement on 2026-05-01 |
| **effectiveFrom** | When the proof becomes valid | Mandate effective from 2026-06-01 |
| **effectiveTo** | When the proof expires | Passport expires 2028-12-31 |
| **supersededBy** | Reference to replacement proof | Mandate v2 supersedes mandate v1 |

**Implication:** Proof chains are not just append-only lists — they are temporal sequences. The current state of a proof chain is derived by replaying events with temporal awareness, not by reading a status field.

### 3.2 Scope Dimension

Every proof has scope boundaries:

| Scope Type | Description | Example |
|-----------|-------------|---------|
| **Entity scope** | Which entities does this proof cover? | Maya's mandate covers Nexus Global USA only |
| **Action scope** | Which actions are permitted? | FX forwards up to $5M |
| **Temporal scope** | For what period is the proof valid? | Mandate valid 2026-01-01 to 2026-12-31 |
| **Jurisdictional scope** | In which jurisdictions does it apply? | Canadian law, OSFI regulation |

**Implication:** Pre-flight validation must check all four scope dimensions, not just existence. A proof that exists but is out of scope is equivalent to no proof.

### 3.3 Confidence Dimension

Not all proofs are equally reliable:

| Confidence Level | Description | Example |
|-----------------|-------------|---------|
| **Cryptographic** | Mathematically verifiable | Digital signature, hash chain |
| **Institutional** | Issued by trusted authority | Government passport, LEI registry |
| **Procedural** | Follows documented process | Internal approval workflow |
| **Declarative** | Self-reported, unverified | Client-provided address |
| **Inferred** | Derived from other proofs | Solvency inferred from balance + credit line |

**Implication:** Different regulatory contexts require different minimum confidence levels. KYC may require institutional or cryptographic proof. Internal process tracking may accept procedural proof.

---

## 4. Proof Chain Composition Patterns

Real-world scenarios require composed proof chains — multiple kinds of proof working together.

### Pattern A: Onboarding Chain (Identity + Authority + Consent)

```
Client onboarding:
  1. Proof of Identity → "Maya is who she says she is"
  2. Proof of Authority → "Maya can act for Nexus Global USA"
  3. Proof of Consent → "Maya agrees to the bank's terms"
  4. Proof of Compliance → "KYC/AML/sanctions checks pass"
  ──────────────────────────────────────────────────────
  Result: Relationship edge created with composite proof chain
```

### Pattern B: Transaction Chain (Intent + Authority + Compliance + Execution + Delivery)

```
Payment execution:
  1. Proof of Intent → "Maya instructed this payment"
  2. Proof of Authority → "Maya is authorized to make this payment"
  3. Proof of Compliance → "Sanctions/AML/policy checks pass"
  4. Proof of Execution → "Bank executed the payment correctly"
  5. Proof of Delivery → "Recipient confirmed receipt"
  ──────────────────────────────────────────────────────
  Result: Transaction edge with full lifecycle proof chain
```

### Pattern C: Product Enrollment Chain (Eligibility + Consent + Ownership)

```
Product enrollment:
  1. Proof of Identity → "Maya is verified"
  2. Proof of Eligibility → "Maya meets product requirements" (kinetic function evaluation)
  3. Proof of Consent → "Maya accepts product terms"
  4. Proof of Ownership → "Maya/Nexus Global owns the account the product attaches to"
  ──────────────────────────────────────────────────────
  Result: subscribedTo edge with enrollment proof chain
```

### Pattern D: Dispute Resolution Chain (Intent vs Execution + Remediation)

```
Dispute handling:
  1. Proof of Intent → "What Maya asked for"
  2. Proof of Execution → "What the bank did"
  3. Delta analysis → "Where they differ"
  4. Proof of Remediation → "How the difference was resolved"
  ──────────────────────────────────────────────────────
  Result: Dispute edge with resolution proof chain
```

---

## 5. Mapping to Existing Architecture

### 5.1 Proof Types (Source) × Proof Kinds (Truth) Matrix

| | Identity | Authority | Intent | Execution | Compliance | Consent | Ownership | Solvency | Delivery | Remediation |
|---|---------|-----------|--------|-----------|------------|---------|-----------|----------|----------|-------------|
| **DECLARATIVE** | ✅ | ✅ | ✅ | | ✅ | ✅ | ✅ | | | ✅ |
| **BEHAVIOURAL** | ✅ | | ✅ | | | ✅ | | | ✅ | ✅ |
| **DELEGATED** | | ✅ | | | | | | | | |
| **AGENTIC** | | | | ✅ | ✅ | | | | | |
| **SYSTEMIC** | | | ✅ | ✅ | ✅ | | | ✅ | ✅ | ✅ |
| **REGULATORY** | ✅ | | | ✅ | ✅ | | | ✅ | ✅ | |

Cells indicate where a proof type from source taxonomy naturally serves a proof kind from the truth taxonomy. Some cells are empty because the combination doesn't naturally occur (e.g., `DELEGATED` proofs don't serve `Solvency` — delegation is about authority, not financial capacity).

### 5.2 Kinetic Layer Integration

The kinetic layer's function definitions and business rules are the evaluation engine for proof kinds:

| Kinetic Function | Proof Kind It Produces |
|-----------------|----------------------|
| `computeProductEligibility` | Proof of Eligibility (subset of Compliance) |
| `validateMandateScope` | Proof of Authority |
| `computeSigningAuthority` | Proof of Authority |
| `validateTransferPricing` | Proof of Compliance |
| `deriveEdgeState` | Proof of Ownership (temporal) |

Each function evaluation produces a proof record in the proof registry, creating an auditable trail of not just what happened, but why it was allowed.

### 5.3 Proof Chain Schema Extension

Current schema (§3.3) captures:
- `proof_type` (source taxonomy: DECLARATIVE, BEHAVIOURAL, etc.)
- `authority_basis` (signing_authority, power_of_attorney, etc.)
- `assertedAt`, `actor`, `channel`

**Proposed extensions:**
- `proof_kind` (truth taxonomy: IDENTITY, AUTHORITY, INTENT, EXECUTION, etc.)
- `scope` (entity scope, action scope, temporal scope, jurisdictional scope)
- `confidence_level` (CRYPTOGRAPHIC, INSTITUTIONAL, PROCEDURAL, DECLARATIVE, INFERRED)
- `validity_window` (`effectiveFrom`, `effectiveTo`)
- `references` (array of proof chain IDs this proof depends on or supersedes)

---

## 6. Differentiation vs. Palantir

Palantir's ontology has actions and audit trails, but:

| Aspect | Palantir | Our Platform |
|--------|----------|--------------|
| **Proof model** | Audit log (passive) | 10 proof kinds × 6 proof types × 3 cross-cutting dimensions |
| **Proof composition** | Flat audit trail | Composed chains (onboarding, transaction, enrollment, dispute) |
| **Temporal reasoning** | Point-in-time queries | Full temporal profile (assertedAt, effectiveFrom/To, supersededBy) |
| **Scope validation** | RBAC | 4-dimensional scope (entity, action, temporal, jurisdictional) |
| **Confidence grading** | Not applicable | 5-level confidence (cryptographic → inferred) |
| **Remediation tracking** | Manual | Proof of Remediation with closed-loop chains |
| **Regulatory mapping** | Generic | Each proof kind maps to specific regulatory domain |

**The differentiation:** Palantir proves that something happened. Our platform proves that the right thing happened, by the right person, at the right time, under the right authority, following the right rules — and if something went wrong, proves it was fixed.

---

## 7. Open Questions

1. **Proof kind vs. proof type in schema:** Should `proof_kind` be a first-class field in `proof_records`, or derived from the combination of `proof_type` + `authority_basis` + context? Recommendation: first-class field — it enables direct regulatory queries ("show me all Identity proofs for this entity").

2. **Composed chain indexing:** When a transaction chain references 5 sub-chains (Intent, Authority, Compliance, Execution, Delivery), how do we query the composite? Recommendation: `proof_chains` table gains a `composite_chain_id` field linking sub-chains to their parent.

3. **Confidence level enforcement:** Should minimum confidence levels be configurable per proof kind? E.g., KYC requires INSTITUTIONAL or CRYPTOGRAPHIC, but internal process tracking accepts PROCEDURAL? Recommendation: Yes — store minimum confidence in `kinetic.business_rules` as a pre-flight rule.

4. **Proof expiry handling:** When a proof expires (passport, mandate, consent), does the proof chain auto-terminate the relationship, or flag it for review? Recommendation: Flag for review (PROPOSED governance mode) — auto-termination is too aggressive for production.

5. **ZKP integration for proof kinds:** Which proof kinds benefit most from ZKP? Recommendation: Identity (prove KYC without exposing PII), Solvency (prove sufficient balance without exposing balance), Compliance (prove sanctions-clear without exposing screening details).

---

*This research extends the existing Dim 05 proof taxonomy. When validated, fold into `05-governance-trust-layer/specs/` as a new section or standalone spec.*
