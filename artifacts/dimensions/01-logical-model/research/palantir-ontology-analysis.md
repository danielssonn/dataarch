# Palantir Ontology Approach — Research Analysis

**Dimension:** 01 — Logical Model & Ontology
**Date:** 2026-05-22
**Status:** Research Note
**Sources:** Palantir Architecture Center docs, Palantir Foundry documentation, industry analysis

---

## Executive Summary

Palantir's Ontology is not a knowledge graph or a semantic layer in the academic sense. It is an **operational layer** — a digital twin of the enterprise that unifies data, logic, action, and security into a single coherent model. The key architectural insight: the ontology is not read-only analysis; it is the interface through which the enterprise acts on its data.

This has direct implications for our GTB canonical graph design — particularly around write-back governance, action modeling, and the separation of semantic concerns from computation.

---

## 1. The Four-Fold Integration

Palantir's Ontology models decisions through four integrated dimensions:

| Dimension | What It Is | GTB Equivalent |
|-----------|-----------|----------------|
| **Data** | Semantic objects, properties, links unified from disparate sources | Canonical Graph nodes + edges |
| **Logic** | Business rules, ML models, LLM functions that power reasoning | Proof chain state derivation, mandate validation |
| **Action** | Governed write-back operations — not just reads, but writes to operational systems | Entity Platform API POST endpoints, proof chain appends |
| **Security** | Fine-grained, object-level access control respecting semantic relationships | LOB scoping, RLS, domain_scope arrays |

**Key insight:** Most ontology implementations (including our current spec) are strong on Data, adequate on Logic, but weak on Action and Security integration. Palantir treats all four as inseparable.

---

## 2. Semantic Layer: Objects, Properties, Links

### 2.1 Object Types

Palantir's "Object Types" map directly to our Node Types. An Object Type is a class of real-world entity — Employee, Equipment, Transaction, Flight, Patient — with defined properties and relationships.

**GTB mapping:**
```
Palantir Object Type     →  GTB Node Type
─────────────────────────────────────────────
Object Type              →  Node (Party, Account, Product, etc.)
Properties               →  Node schema fields (id, lei, canonicalName, state, etc.)
Link Types               →  Edge Types (owns, isSubsidiaryOf, isSubscribedTo, etc.)
```

### 2.2 Link Types

Relationships between objects. Typed, directional, with cardinality constraints.

**GTB mapping:** Direct 1:1 with our Edge taxonomy. Palantir would model `owns`, `isSubsidiaryOf`, `isSubscribedTo` as Link Types with source/target object type constraints.

### 2.3 Interfaces (Polymorphism)

**This is something our current spec lacks.** Palantir Interfaces provide object type polymorphism — they describe the shape and capabilities of object types that share a common structure.

**Example:** An interface `IHasBalance` could be implemented by `OperatingAccount`, `TradingAccount`, and `CustodyAccount`. Any action or function that needs to read a balance works against the interface, not the concrete type.

**GTB recommendation:** Consider adding an interface/contract layer to our node taxonomy. For example:
- `IIdentifiable` — all nodes with LEI + canonicalName
- `IHasLifecycle` — all nodes with state transitions (Active/Suspended/Terminated)
- `IHasBalance` — OperatingAccount, TradingAccount, CustodyAccount
- `IIsSettlementTarget` — any account that can receive transaction settlement
- `IIsRegulatable` — any party that can be subject to regulatory obligations

This enables polymorphic queries and actions without duplicating logic per concrete type.

---

## 3. Kinetic Layer: Actions & Functions

**This is the most significant gap between Palantir's approach and our current spec.**

### 3.1 Action Types

Structured, governed write-back operations. Not API endpoints — first-class ontology constructs with:
- Input validation (what objects/properties are required)
- Permission requirements (who can invoke)
- Audit trail (automatic, tied to the ontology object)
- Rollback capability (via branching)

**GTB gap:** Our Entity Platform API has POST endpoints (`/relationships`, `/proof/{edgeId}/records`), but they are REST endpoints, not ontology-native actions. They lack:
- Pre-flight validation against business rules (not just schema validation)
- Automatic audit trail tied to the affected objects
- Declarative permission model per action type

### 3.2 Functions

Code-based logic that takes ontology objects as inputs and returns outputs. Can be business rules, ML model invocations, or LLM-driven reasoning. Functions are versioned and audited within the ontology.

**GTB gap:** Our proof chain state derivation ("current state is derived by replaying the event chain") is effectively a function, but it's not modeled as a first-class ontology construct. Same for mandate validation logic.

**Recommendation:** Model critical business logic as named, versioned functions within the ontology:
- `deriveEdgeState(ProofChain) → EdgeState`
- `validateMandateScope(AgentMandate, Operation) → ValidationResult`
- `computeEligibility(Party, ProductDefinition) → EligibilityResult`

---

## 4. Dynamic Layer: Security

Fine-grained, object-level access control that respects semantic relationships.

**GTB alignment:** Our `domain_scope` array on edges is a start, but Palantir's approach is more sophisticated:
- Permissions are inherited through the object graph (if you can see the parent, you can see certain child relationships)
- Permissions apply to actions, not just data reads (can you trigger this action on this object?)
- Agent permissions inherit from human permissions or project permissions

**GTB gap:** Our LOB scoping is flat (CB | CM | WM | ALL). It doesn't model inheritance through relationships or action-level permissions.

---

## 5. Governance: Branching & Proposals

**This is the most architecturally distinctive Palantir concept.**

### 5.1 Branching

Analogous to Git branches, but for operational reality. An AI agent or human proposes a change (e.g., "reroute 50 shipments"), and that proposal exists on a branch. A human reviews and merges.

**Key properties:**
- Branches are isolated — the proposed change doesn't affect main until merged
- Proposals are reviewable — like a Pull Request for business operations
- Merge is atomic — the change either fully applies or doesn't
- Audit trail is inherent — every merge is a recorded decision

### 5.2 Ontology Proposals

An ontology proposal is analogous to a Pull Request. Changes made in a branch are reviewed before integration into Main. Automatically created when a branching proposal is created.

**GTB implication:** This maps directly to our proof chain model, but with a critical difference:
- Our proof chain appends are immediate — once a `ProofRecord` is written, the edge state changes
- Palantir's branching means proposed changes are isolated until reviewed and merged

**Recommendation:** Consider a two-phase write model for high-stakes operations:
1. **Proposed** — change exists on a branch; edge state includes a `pendingChanges` array
2. **Merged** — change is reviewed and applied; proof record is appended; edge state updates

This is particularly relevant for:
- New relationship assertions (currently go straight to `Proposed` state, but the assertion itself is immediate)
- Mandate scope changes (should be reviewed before applying)
- Product subscription changes (should be reviewed before activating)

---

## 6. AIP: AI Agents Operating Within the Ontology

Palantir's AI Platform (AIP) agents are **natively ontology-aware**:
- They query Object Types, not raw databases
- They invoke governed Actions, not arbitrary operations
- They produce auditable outputs that flow through the ontology's audit trail

**Critical architectural decision:** The LLM does not make semantic decisions. The ontology does. The LLM's job is to reason about and communicate results, not to construct them.

**GTB alignment:** This maps directly to our agentic mandate model:
- AgentMandate defines scope → agent can only act on ontology objects within scope
- Pre-flight validation → `POST /mandates/{agentId}/validate` checks scope before action
- Decision trace → `decisionTrace` in agentic proof records captures what the agent observed and decided

**GTB gap:** Our agent model is proof-centric (the proof record validates the action after the fact). Palantir's model is governance-centric (the action can only happen within the ontology's governed framework). Both approaches are valid; ours is more flexible but requires stronger post-hoc validation.

---

## 7. Ontology-Grounded RAG vs. Plain RAG

Relevant for our Entity Platform API design.

| Approach | Query Processing | Retrieval | Context for LLM |
|----------|-----------------|-----------|-----------------|
| **Plain RAG** | Embed query → vector similarity → top-k chunks | Distributional similarity | Raw text chunks |
| **Ontology-Grounded** | Resolve entities → traverse typed relationships → apply rules | Semantic graph traversal | Structured facts + linked documents |

**GTB implication:** Our Entity Platform API should support ontology-grounded queries:
```
// Plain: "show me transactions for ACME"
GET /entities/ACME/relationships

// Ontology-grounded: "show me high-risk transactions linked to ACME's household through beneficial ownership"
GET /entities/ACME/beneficial-owners?filter=risk_level=high&include=transactions
```

The second query requires traversing the semantic graph with typed relationships — exactly what our ontology enables.

---

## 8. Comparison Matrix: Palantir Ontology vs. GTB Canonical Graph

| Aspect | Palantir Ontology | GTB Canonical Graph | Gap? |
|--------|-------------------|---------------------|------|
| **Semantic model** | Object Types + Properties + Links | Node Types + Schema + Edge Types | ✅ Aligned |
| **Polymorphism** | Interfaces (object type contracts) | None — concrete types only | 🔴 Gap |
| **Actions** | First-class Action Types with governance | REST API endpoints | 🟡 Partial |
| **Functions** | Versioned business logic within ontology | Implicit (proof chain derivation) | 🟡 Partial |
| **Security** | Object-level, inherited through graph | Flat LOB scoping (domain_scope) | 🟡 Partial |
| **Governance** | Branching + Proposals (version control for reality) | Append-only proof chains | 🟠 Different approach |
| **AI integration** | AIP agents natively ontology-aware | Agentic mandate model + proof records | ✅ Aligned |
| **Write-back** | Governed actions write to operational systems | Projections are read-only; graph is source of truth | ✅ Aligned |
| **Temporal** | Point-in-time queries via branching history | Point-in-time via proof chain replay | ✅ Aligned |
| **Audit trail** | Inherent (every action is audited) | Proof chain provides audit trail | ✅ Aligned |

---

## 9. Actionable Recommendations for GTB Ontology

Based on this analysis, here are the specific improvements to our canonical graph spec:

### High Priority

1. **Add Interface/Contract layer** — define polymorphic contracts (IHasBalance, IIsSettlementTarget, etc.) that enable cross-type queries and actions without duplication
2. **Model business logic as named functions** — `deriveEdgeState`, `validateMandateScope`, `computeEligibility` as first-class ontology constructs with versioning
3. **Consider two-phase write model** — Proposed → Reviewed → Merged for high-stakes operations (new relationships, mandate changes, product subscriptions)

### Medium Priority

4. **Enhance LOB scoping** — move from flat `domain_scope` array to inherited permissions through the object graph
5. **Action-level permissions** — separate permissions for reading data vs. triggering actions on objects
6. **Agent permission inheritance** — explicit model for how agent permissions derive from human/project permissions

### Low Priority (Future)

7. **Branching for operational changes** — full Git-like branching for business operations (may be overkill for Phase 1)
8. **Ontology SDK** — type-safe code-first API for external developers (aligns with Entity Platform API goals)

---

## 10. What NOT to Copy from Palantir

Not everything in Palantir's model applies to our context:

- **Proprietary lock-in** — Palantir's ontology is locked inside Foundry. Our ontology must be platform-agnostic (works with Neo4j, PostgreSQL, or Delta Lake)
- **FDE implementation model** — Palantir embeds engineers. We're building for self-service by bank teams
- **Monolithic ontology** — Palantir tends toward a single enterprise ontology. Our approach of dimension-based modular specs is better for incremental delivery
- **Over-engineering risk** — Palantir's ontology is comprehensive by design. We should start narrow (one product line) and expand incrementally

---

## Sources

1. Palantir Architecture Center — "The Ontology system" (palantir.com/docs/foundry/architecture-center/ontology-system)
2. Palantir Foundry Docs — "Overview · Ontology" (palantir.com/docs/foundry/ontology/overview)
3. Palantir Foundry Docs — "Review ontology proposals" (palantir.com/docs/foundry/ontologies/review-ontology-proposals)
4. Industry analysis — "Palantir's Secret Weapon Isn't AI — It's Ontology" (dev.to, 2026)
5. Industry analysis — "The Missing Semantic Layer That Makes Enterprise AI Actually Work" (superml.dev, 2026)
6. GitHub — palantir-ontology-strategy (Leading-AI-IO, CC BY 4.0)

---

_End of Palantir Ontology Analysis_
