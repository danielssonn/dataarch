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

## 11. Expanded Industry Comparison: Palantir, Stardog, and the Ontology Landscape

The following section extends the initial Palantir analysis with a broader industry comparison, drawing on additional primary sources including the Leading-AI-IO Palantir Ontology Strategy book (CC BY 4.0) and Stardog's published architecture.

### 11.1 Palantir Foundry: Deep Architecture (Updated)

**Source:** Leading-AI-IO/palantir-ontology-strategy — "The Palantir Impact: Ontology Strategy Connecting Data and AI"

#### Core Architecture Principles

Palantir's ontology design is built on three non-negotiable principles:

1. **Operational Layer, Not Analytical Layer** — Data is not a record of the past; it is the engine that drives the real world. The ontology is a "digital twin" that replicates real-world business on a system, serving as the layer where data directly drives business operations.

2. **Convergence of Noun and Verb** — Systems are the integration of "Objects (nouns)" and "Actions (verbs)." The model encompasses not only states such as customers and parts (semantics), but also kinetic elements such as orders and status changes (kinetics).

3. **Governance of Reality: Version Control for the Real World** — The immense power to rewrite real-world operations demands absolute governance. Even in an era where AI autonomously makes proposals, Ontology achieves both extreme speed and governance through "branching" and "review."

#### Semantic + Kinetic Integration

Palantir's ontology explicitly divides into:

**Semantic Elements (The World of Nouns: Meaning)**
- **Object Type:** A type representing a real-world concept (noun), generating object instances using data sources as input.
- **Property:** The attributes of an object type.
- **Link Type:** Relationships between object types, with source/target constraints.

**Kinetic Elements (The World of Verbs: Action)**
- **Action Type:** A governed operation that modifies ontology state. Each action declares inputs, pre-flight rules, effects, permissions, and governance mode.
- **Function:** Versioned business logic units that take ontology objects as inputs and return outputs. Can be business rules, ML model invocations, or LLM-driven reasoning.
- **Dynamic Security:** Fine-grained, object-level access control that respects semantic relationships.

#### Branching & Proposal Lifecycle

Palantir's branching model is the most architecturally distinctive concept:

```
[Create Working Branch] → [Change on Ontology] → [Submit Proposal]
                                                ↓
                                        [Under Review]
                                                ↓
                                    ┌───────────┴───────────┐
                                    ↓                       ↓
                               [Sent Back] ← Reject    [Merge to Main]
                                    ↓                       ↓
                              [Change on Ontology]    [Reflect Immediately]
```

Key properties:
- Branches are isolated — proposed changes don't affect main until merged
- Proposals are reviewable — like a Pull Request for business operations
- Merge is atomic — the change either fully applies or doesn't
- Audit trail is inherent — every merge is a recorded decision
- Branches are tied to a "single ontology" — centrally managed

#### The Approvals App

Palantir provides a dedicated "Approvals" app for complex organizations:
- Centralizes approval workflows across diverse stakeholders (department heads, compliance officers, data owners)
- Seamlessly integrates peer reviews and compliance checks
- Provides complete transparency: "when, who, and for what reason the change was approved"

#### Restricted Views (RVs) and Multi-Dataset Objects (MDOs)

Access control operates at two levels:
- **Restricted Views (RVs):** Row-level control — which object instances a user can see
- **MDOs:** Column/property-level control — which properties of an object a user can see

This enables governance like "customer purchase history is shared company-wide, but personally identifiable names and phone numbers can only be seen by specific departments."

#### Action Log: The Ultimate Audit Trail

In Foundry, every action submission is modeled as an "object type itself" and recorded permanently. Corresponding 1-to-1 with the Action type, a log object detailing who, when, and what data was rewritten is automatically generated for each submission and linked to the edited target object.

**This is the closest industry equivalent to our Proof Registry concept.**

#### AI FDE: Forward Deployed AI Engineers

Palantir provides an interactive agent called "AI FDE" that:
- Translates natural language requests into Foundry operations
- Creates data transformation pipelines, repository management, and ontology construction/maintenance
- Strictly respects user's existing permissions
- Always presents a branch proposal for review before any change affects main

This significantly reduces the risk of misuse or excessive exposure of sensitive data, allowing humans and AI to collaborate safely.

### 11.2 Stardog: RDF-Native Knowledge Graph Platform

**Source:** Stardog blog posts (2024-2026), Stardog documentation, BCBS-239 compliance analysis

#### Core Architecture

Stardog is an RDF-compliant knowledge graph engine with a focus on semantic reasoning, rules, and security:

- **RDF/OWL Native:** Built on W3C standards (RDF, RDFS, OWL 2). Ontologies are formal OWL 2 DL ontologies with reasoning capabilities.
- **Inference Engine:** Built-in rule-based reasoning. Stardog supports custom SWRL rules and SPARQL CONSTRUCT rules for deriving new facts from existing data.
- **Graph-Based Security:** Row-level, column-level, and graph-traversal-based access control. Security policies are expressed as SPARQL queries.

#### Key Differentiators

1. **Reasoning-Native:** Unlike Palantir (which uses a proprietary object/link model), Stardog leverages OWL 2 DL reasoning. This means:
   - Class hierarchies are automatically inferred (if A subclassOf B, and B subclassOf C, then A is implicitly subclassOf C)
   - Property chains can be defined (if A knows B, and B worksAt C, then A knowsEmployeeOf C)
   - Consistency checking is built in (ontology contradictions are detected automatically)

2. **Virtual Knowledge Graphs:** Stardog can federate across heterogeneous data sources (SQL, NoSQL, file systems) without physically moving data. The knowledge graph acts as a semantic layer over existing systems.

3. **Voicebox (LLM Integration):** Stardog's LLM-powered assistant uses "Semantic Parsing" rather than RAG:
   - User asks natural language question
   - LLM translates to SPARQL query (not vector similarity search)
   - SPARQL executes against the knowledge graph
   - Results are 100% grounded in enterprise data — no hallucination

4. **BCBS-239 Compliance Focus:** Stardog explicitly targets banking compliance:
   - Unifies siloed risk data across the enterprise
   - Traces data from origin to report
   - Provides semantic understanding of data (not just access)
   - Enables natural language interrogation without hallucinations

#### Stardog vs. GTB: What We Can Learn

| Aspect | Stardog | GTB Canonical Graph | Relevance |
|--------|---------|---------------------|-----------|
| **Formal ontology** | OWL 2 DL with reasoning | Informal type system | 🟠 Stardog's reasoning could help us detect ontology inconsistencies |
| **Inference rules** | SWRL/SPARQL CONSTRUCT rules | Implicit (proof chain derivation) | 🟡 Our proof chain derivation is effectively inference, but Stardog's formal rules could make it more explicit |
| **Graph security** | SPARQL-based policies | Flat domain_scope arrays | 🟠 Stardog's graph-traversal security is more sophisticated |
| **Virtual federation** | Heterogeneous data sources without movement | Physical canonical store | 🟡 Could be useful for legacy data integration |
| **LLM integration** | Semantic Parsing (NL → SPARQL) | REST API + agentic mandates | 🟡 Stardog's approach could inform our Entity Platform API query design |
| **RDF standards** | Full W3C compliance | Proprietary graph model | ✅ Not relevant — we're using Neo4j, not RDF |

#### What Stardog Does That We Don't

1. **Formal reasoning over ontologies** — Stardog can detect contradictions in the ontology itself. Our current spec has no consistency checking mechanism.
2. **Property chain inference** — Stardog can automatically derive transitive relationships. We currently require explicit edges for all relationships.
3. **Virtual knowledge graphs** — Stardog can federate across sources without ETL. We're building a physical canonical store.

### 11.3 Other Notable Ontology Platforms (Brief)

#### Amazon Neptune
- **Focus:** Managed graph database supporting both property graph (Gremlin) and RDF (SPARQL) models
- **Strengths:** Cloud-native, highly scalable, integrated with AWS ecosystem
- **Limitations:** No built-in reasoning, no action/kinetic layer, security is standard IAM-based
- **Relevance to GTB:** Low — Neptune is a database, not an ontology platform. It could serve as our Neo4j alternative but doesn't add architectural insight.

#### Neo4j (Our Chosen Platform)
- **Focus:** Property graph database with Cypher query language
- **Strengths:** Mature ecosystem, strong performance, native graph algorithms, APOC library
- **Limitations:** No built-in reasoning, no action/kinetic layer, security is role-based (not graph-traversal-aware)
- **Relevance to GTB:** High — this is our operational graph store. We need to build the kinetic layer on top of it.

#### IBM Watson Knowledge Studio (Legacy)
- **Focus:** Entity extraction and ontology construction from unstructured text
- **Status:** Largely superseded by IBM's newer AI offerings
- **Relevance to GTB:** Low — focused on NLP, not operational ontology

### 11.4 Synthesis: What the Industry Leaders Agree On

Despite different implementations, Palantir, Stardog, and the broader ontology community converge on these principles:

#### Principle 1: Noun + Verb Integration
All three platforms recognize that an ontology without actions is just a data catalog. Palantir makes this explicit with Action Types. Stardog embeds actions in SPARQL UPDATE transactions with rules. Neo4j requires application-level logic.

**GTB alignment:** Our Section 9 (Kinetic Layer) addresses this correctly. Actions are first-class ontology constructs, not just API endpoints.

#### Principle 2: Governance Before Speed
Palantir's branching/proposal model and Stardog's transactional reasoning both prioritize governance. Neither platform allows uncontrolled writes to the ontology.

**GTB alignment:** Our two-phase write model (Proposed → Reviewed → Merged) and Proof Registry provide this governance. However, we should consider whether our proof chain appends need a review gate before becoming canonical.

#### Principle 3: Security as First-Class Concern
All three platforms treat security as integral to the ontology, not bolted on:
- Palantir: RVs + MDOs with inheritance through the object graph
- Stardog: SPARQL-based security policies with graph-traversal awareness
- Neo4j: Role-based access control (RBAC) with limited graph awareness

**GTB gap:** Our `domain_scope` array is flat. We should explore inherited permissions through the relationship graph.

#### Principle 4: AI Grounding in Ontology
All three platforms recognize that AI/LLMs need to be grounded in enterprise ontology, not free-floating:
- Palantir: AIP agents operate natively within the ontology
- Stardog: Voicebox uses Semantic Parsing (NL → SPARQL) for hallucination-free answers
- Neo4j: GraphRAG patterns for LLM grounding

**GTB alignment:** Our agentic mandate model provides this grounding. Agents can only act within their defined scope.

### 11.5 Updated Comparison Matrix

| Aspect | Palantir Foundry | Stardog | Neo4j | GTB Canonical Graph |
|--------|-----------------|---------|-------|---------------------|
| **Semantic model** | Object Types + Properties + Links | RDF/OWL 2 with reasoning | Property graph (nodes + relationships) | Node Types + Schema + Edge Types |
| **Formal reasoning** | ❌ No | ✅ OWL 2 DL + SWRL rules | ❌ No | ❌ No |
| **Polymorphism** | ✅ Interfaces | ✅ OWL class hierarchies | ❌ No | ✅ Interfaces (Section 9) |
| **Actions** | ✅ First-class Action Types | ⚠️ SPARQL UPDATE + rules | ❌ No (app-level) | ✅ Action Types (Section 9) |
| **Functions** | ✅ Versioned business logic | ✅ SWRL rules | ❌ No | ✅ Functions (Section 9) |
| **Security** | ✅ RVs + MDOs + inheritance | ✅ SPARQL policies + traversal | ⚠️ RBAC only | ⚠️ Flat domain_scope |
| **Governance** | ✅ Branching + Proposals | ✅ Transactional reasoning | ❌ No | ✅ Two-phase write + Proof Registry |
| **AI integration** | ✅ AIP + AI FDE | ✅ Voicebox (Semantic Parsing) | ⚠️ GraphRAG patterns | ✅ Agentic mandate model |
| **Write-back** | ✅ Governed actions | ✅ SPARQL UPDATE | ❌ No (app-level) | ✅ Proof chain appends |
| **Temporal** | ✅ Branching history | ⚠️ Extension required | ❌ No | ✅ Proof chain replay |
| **Audit trail** | ✅ Action Log | ✅ Transaction log | ❌ No | ✅ Proof Registry |
| **Standards** | ❌ Proprietary | ✅ W3C RDF/OWL | ⚠️ OpenCypher | ❌ Proprietary |
| **Platform lock-in** | 🔴 High | 🟡 Medium | 🟢 Low | 🟢 Low |

### 11.6 Final Recommendations (Updated)

Based on this expanded analysis, here are the refined recommendations:

#### Must-Have (Already in Spec)
1. ✅ **Kinetic Layer** — Interfaces, Actions, Functions (Section 9)
2. ✅ **Two-Phase Write Model** — Proposed → Reviewed → Merged
3. ✅ **Proof Registry** — Immutable audit trail
4. ✅ **Agentic Mandate Model** — Governance for AI agents

#### Should-Add (Gap Identified)
5. 🟠 **Inherited Security** — Move from flat `domain_scope` to permissions that inherit through the relationship graph (inspired by Palantir RVs + Stardog graph-traversal security)
6. 🟠 **Formal Consistency Checking** — Add an ontology validation layer that detects contradictions in the type system (inspired by Stardog's OWL reasoning)
7. 🟡 **Property Chain Inference** — Consider transitive relationship derivation for beneficial ownership chains (inspired by Stardog's property chains)

#### Nice-to-Have (Future)
8. 🟢 **Semantic Parsing Layer** — Natural language → graph query translation (inspired by Stardog Voicebox)
9. 🟢 **Virtual Federation** — Semantic layer over legacy sources without full ETL (inspired by Stardog Virtual KGs)
10. 🟢 **Branching for Operations** — Full Git-like branching for business operations (inspired by Palantir)

---

## Sources

1. Palantir Architecture Center — "The Ontology system" (palantir.com/docs/foundry/architecture-center/ontology-system)
2. Palantir Foundry Docs — "Overview · Ontology" (palantir.com/docs/foundry/ontology/overview)
3. Palantir Foundry Docs — "Review ontology proposals" (palantir.com/docs/foundry/ontologies/review-ontology-proposals)
4. Industry analysis — "Palantir's Secret Weapon Isn't AI — It's Ontology" (dev.to, 2026)
5. Industry analysis — "The Missing Semantic Layer That Makes Enterprise AI Actually Work" (superml.dev, 2026)
6. GitHub — palantir-ontology-strategy (Leading-AI-IO, CC BY 4.0) — "The Palantir Impact: Ontology Strategy Connecting Data and AI"
7. Stardog Blog — "Enterprise AI Requires the Fusion of LLM and Knowledge Graph" (Dec 2024)
8. Stardog Blog — "Taming the Risk Hydra: Stardog and the Future of BCBS-239 Compliance" (Jun 2025)
9. Stardog Blog — "25 Years in Semantics: Building the Cognitive Backbone of the Enterprise" (May 2026)
10. IBM — "What is an Ontology?" (ibm.com/think/ontology)

---

_End of Palantir Ontology Analysis (Expanded)_
