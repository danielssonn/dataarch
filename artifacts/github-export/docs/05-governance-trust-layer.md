# 05 — Governance & Trust Layer

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Mandates, proof, auditability, compliance  
**Status:** Draft for Daniel's review

## 1. Core Ideas

Governance is not an add-on. It is built into the runtime:

- Every relationship has a proof chain.
- Every action traces back to a mandate.
- Every decision is auditable and reconstructible.

## 2. Mandate Hierarchy

- HumanMandate (root):
  - Signed by a human with real authority.
  - Defines what categories of automation are permitted.

- SystemMandate (intermediate):
  - Delegated from HumanMandate.
  - Defines which systems may act under the human mandate.

- AgentMandate (execution):
  - Delegated from SystemMandate.
  - Defines exact permitted operations, limits, constraints.
  - Versioned per agent.

Rule:
- No agent action executes without a valid, non-expired AgentMandate with an intact delegation chain.

## 3. Proof Registry

Design:
- Append-only.
- Event-sourced (state derived by replay).
- Cryptographically integrity-checked (SHA-256 hash chains).
- Stored in PostgreSQL, mirrored via CDC to Delta Lake.

Key behaviors:
- Every edge has exactly one proof chain.
- Proof records capture:
  - What happened (event).
  - Who did it (actor).
  - Under what authority (mandate, role).
  - Through which channel.
- Disputes, revocations, and challenges are explicit events, never silent updates.

## 4. Stream-Level Audit

Streaming (Confluent) and Flink integrate directly:

- governance.audit-events:
  - Every significant action (relationship, KYC, mandate, edge transition).
  - All Flink-driven decisions include rule IDs and input sets.
- governance.mandate-events:
  - Mandate creation, revocation, scope changes.
  - Ensures fast propagation to consumers.

This enables:
- Real-time audit for compliance.
- Reconstructibility: “Show us exactly what the system saw and decided.”

## 5. Compliance & ZKP

- ZKP hooks (future):
  - For sensitive validations (e.g., agent acted within scope) without exposing underlying policy or client data.
- Column-level masking:
  - In proof_records (for intent_payload, signature) for non-privileged consumers.
