# Dimension Memory Index

Each dimension has its own isolated memory file so context doesn't clobber across workstreams. Read the relevant one before working in that space.

| # | File | What It Covers | When to Reference |
|---|------|---------------|------------------|
| 01 | `dimensions/01-logical-model.md` | Business semantics, entity definitions, product catalog, domain ontology (no tech) | Defining entities, relationships, business rules |
| 02 | `dimensions/02-materialization-strategy.md` | Physical data storage: append-only tables vs current-state views, temporal indexing, CDF pipelines, access-tier routing | Designing how logical model physically lives and ages over time |
| 03 | `dimensions/03-platform-infrastructure.md` | Databricks on Azure, Unity Catalog governance plane, Lakebase instances, Neo4j cluster sizing, networking, compute profiles | Provisioning infra, platform topology decisions |
| 04 | `dimensions/04-api-integration-contract.md` | Entity Platform API surface: REST endpoints, auth patterns, rate limits, LOB integration points, vendor system connectivity | Defining external interfaces and integration contracts |
| 05 | `dimensions/05-governance-trust-layer.md` | Proof chains, evidence anchoring, mandate model (Human→System→Agent), ZKP integration, audit trails, security policies | Regulatory compliance, agent governance, trust architecture |
