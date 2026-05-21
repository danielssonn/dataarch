# Global Transaction Banking — Architecture Dimensions

## Structure Overview
Architecture decomposed into 5 independent dimensions. Each has its own artifact directory and isolated memory file so context doesn't clobber across workstreams.

```
artifacts/dimensions/
├── 01-logical-model/{specs,diagrams,research}       # Business semantics — no tech refs
├── 02-materialization-strategy/{specs,diagrams,research}   # Physical data model & access patterns
├── 03-platform-infrastructure/{specs,diagrams,research}    # Databricks + supporting stack topology
├── 04-api-integration-contract/{specs,diagrams,research}   # External API surface & integration contracts
└── 05-governance-trust-layer/{specs,diagrams,research}     # Proof chains, mandates, ZKP

memory/dimensions/                                     # Per-dimension memory files (isolated)
```

## Memory System
- `memory/dimensions/index.md` — master index of all dimension memories. Read this before working in any specific dimension to understand what's tracked where.
- Each file: current state, key decisions made for that domain only, open questions scoped to it. No cross-dimension bleed unless explicitly noted as a dependency with reference link.
