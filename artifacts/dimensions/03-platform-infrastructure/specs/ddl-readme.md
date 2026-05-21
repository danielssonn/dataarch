# Transaction Banking Canonical Data Model — Databricks DDL

Delta Lake / Unity Catalog implementation of the canonical graph and proof registry
defined in [Architecture.md](../Architecture.md).

---

## Execution Order

Run files in this sequence. Each step depends on the previous.

```
1.  catalogs/00_create_catalogs.sql
2.  catalogs/01_catalog_grants.sql
3.  _shared/02_row_level_security_functions.sql
4.  tb_canonical/proof/00_schema.sql        ← proof schema first (referenced by all others)
5.  tb_canonical/proof/01_proof_chains.sql
6.  tb_canonical/proof/02_proof_records.sql
7.  tb_canonical/proof/03_current_proof_chains_view.sql
8.  tb_canonical/proof/04_proof_integrity_view.sql
9.  tb_canonical/proof/05_grants.sql
10. tb_canonical/entity/00_schema.sql
11. tb_canonical/entity/01_nodes.sql
12. tb_canonical/entity/02_edges.sql
13. tb_canonical/entity/03_current_nodes_view.sql
14. tb_canonical/entity/04_current_edges_view.sql
15. tb_canonical/entity/05_kyc_view.sql
16. tb_canonical/entity/06_grants.sql
17. tb_canonical/product/00_schema.sql
18. tb_canonical/product/01_nodes.sql
19. tb_canonical/account/00_schema.sql
20. tb_canonical/account/01_nodes.sql
21. tb_canonical/transaction/00_schema.sql
22. tb_canonical/transaction/01_nodes.sql
23. tb_canonical/channel/00_schema.sql
24. tb_canonical/channel/01_nodes.sql
25. tb_canonical/channel/02_entitlements.sql
26. tb_canonical/channel/03_mandates.sql
27. tb_canonical/metrics/00_schema.sql
28. tb_canonical/metrics/01_metric_definitions.sql
29. tb_canonical/metrics/02_canonical_kpis.sql
30. tb_canonical/metrics/03_metric_views.sql
31. tb_cb/00_schema_and_views.sql
32. tb_cm/00_schema_and_views.sql
33. tb_wm/00_schema_and_views.sql
```

Pipelines are deployed as Databricks Jobs after all DDL is complete:
```
pipelines/01_proof_integrity_sweep.sql    — every 15 min
pipelines/02_kpi_computation_job.sql      — hourly
pipelines/03_cb_projection_refresh.sql    — CDF-triggered or scheduled
pipelines/04_entitlement_snapshot_job.sql — CDF-triggered on proof_records
```

---

## Catalog Structure

```
tb_canonical                          ← source of truth (Channels Technology)
├── proof                             ← create FIRST
│   ├── proof_chains                  append-only, Liquid Cluster (edge_id, integrity_status)
│   ├── proof_records                 append-only, Liquid Cluster (chain_id, sequence)
│   ├── current_proof_chains          view: ROW_NUMBER() per chain
│   ├── broken_chains                 view: integrity_status != 'Valid'
│   └── proof_records_masked          view: intent_payload masked by role
├── entity
│   ├── nodes                         append-only, Liquid Cluster (type, state, lei)
│   ├── edges                         append-only, Liquid Cluster (type, from_node_id, state)
│   ├── current_nodes                 view: latest row per id + column masking
│   ├── current_edges                 view: latest row per id + RLS by domain_scope
│   ├── legal_entities                view: active LegalEntity nodes with LEI
│   ├── kyc_status                    view: KYC completion per entity
│   └── ubo_resolution                view: beneficial owner chain
├── product
│   ├── nodes                         append-only, Liquid Cluster (type, state)
│   ├── current_nodes                 view
│   └── adoption_by_definition        view: feeds product_adoption_rate metric
├── account
│   ├── nodes                         append-only, Liquid Cluster (type, state, owner_id)
│   ├── current_nodes                 view
│   └── pool_membership               view: pool hierarchy
├── transaction
│   ├── nodes                         append-only, Liquid Cluster (type, state, settled_account_id, created_at)
│   ├── current_nodes                 view
│   └── stp_eligibility               view: feeds payment_stp_rate metric
├── channel
│   ├── nodes                         channel definitions
│   ├── entitlements                  append-only, Liquid Cluster (party_id, channel_type, state)
│   ├── entitlement_snapshots         append-only, point-in-time captures
│   ├── mandates                      append-only, Liquid Cluster (agent_id, state)
│   ├── current_entitlements          view: active entitlements
│   ├── active_agent_mandates         view: pre-flight check surface
│   └── entitlement_provisioning_time view: feeds entitlement_provisioning_time metric
└── metrics
    ├── metric_definitions            8 canonical KPI definitions (seeded)
    ├── canonical_kpis                append-only time-series fact table
    ├── current_kpis                  view: latest value per metric
    ├── kpi_trend_30d                 view: daily trend
    └── [intermediate metric views]   onboarding_cycle_time_inputs, cross_lob_coverage, etc.

tb_cb                                 ← CB LOB views (never writes to tb_canonical)
├── cb_ext.parties
├── cb_ext.accounts
├── cb_ext.payment_instructions
└── cb_ext.cb_operational_projection  denormalised, refreshed by pipeline

tb_cm / tb_wm                         ← same pattern, CM and WM scoped
```

---

## Key Design Decisions

### Append-Only Everything

All core tables use `TBLPROPERTIES ('delta.appendOnly' = 'true')`. Current state is
always derived by `ROW_NUMBER() OVER (PARTITION BY id ORDER BY created_at DESC) = 1`
in the `current_*` views. This satisfies Architecture invariants 4 and 5 simultaneously
and makes point-in-time queries trivial: filter `WHERE created_at <= @asOf`.

### No Edge Without Proof Chain

`CHECK (proof_chain_id IS NOT NULL AND proof_chain_id != '')` is on every node and edge
table. This is a last-resort guard — the Entity Platform API enforces this at the
application layer, but Delta constraints prevent bypass via direct Spark writes.

### Row-Level Security via domain_scope

The `domain_scope ARRAY<STRING>` column on `entity.edges` is the RLS enforcement point.
`current_edges` view filters: `array_contains(domain_scope, caller_lob) OR array_contains(domain_scope, 'ALL')`.
LOB catalogs (`tb_cb`, `tb_cm`, `tb_wm`) are derived views — they never contain
data from other LOBs because the canonical view already excludes it.

### Column-Level Security on proof_records

`intent_payload` and `signature` on `proof.proof_records` are visible only to
`auditor` and `proof_registry_reader` roles. All other callers see `NULL` via the
`proof_records_masked` view. Raw table access is restricted to `entity_platform_writer`
and `auditor`.

### Liquid Clustering Strategy

| Table | Cluster columns | Dominant query pattern |
|---|---|---|
| `entity.nodes` | `(type, state, lei)` | UBO/ownership chain by type + LEI join |
| `entity.edges` | `(type, from_node_id, state)` | Graph traversal from a known node |
| `proof.proof_records` | `(chain_id, sequence)` | Full chain replay in order |
| `proof.proof_chains` | `(edge_id, integrity_status)` | Integrity sweep + edge lookup |
| `account.nodes` | `(type, state, owner_id)` | Account lookup by owner |
| `transaction.nodes` | `(type, state, settled_account_id, created_at)` | STP queries by account + time |
| `channel.entitlements` | `(party_id, channel_type, state)` | Authorisation check by party |

### Change Data Feed

Enabled on: `entity.nodes`, `entity.edges`, `proof.proof_records`, `transaction.nodes`,
`channel.entitlements`. These tables feed streaming projections and event-driven pipelines.

---

## Reference Files

- `_shared/00_types_and_enums.sql` — all enum values used in CHECK constraints
- `_shared/01_struct_definitions.sql` — STRUCT type definitions (copy-paste into DDL)
- [Architecture.md](../Architecture.md) — full specification
