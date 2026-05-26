# 07 — Stream Computing Plan

**Project:** Nexus Global Transaction Banking Platform  
**Type:** Apache Flink runtime, jobs, and use cases  
**Status:** Draft for Daniel's review

## 1. Purpose

Flink is the stream computation layer: not dumb pipes, but real-time, stateful processing on top of Confluent. It:
- Correlates events across domains.
- Enforces kinetic rules.
- Drives real-time analytics (reporting, statements, forecasting, liquidity).

## 2. Runtime

- Deployment:
  - Flink on Kubernetes (AKS), integrated with Confluent and Databricks.
- Semantics:
  - Exactly-once for critical decision jobs.
  - At-least-once with idempotent sinks for analytics.
- Reliability:
  - Checkpointing every 30–60 seconds to Azure Blob Storage.
  - RocksDB as state backend; persistent and recoverable.

## 3. Core Flink Jobs

- Kinetic Incident Correlation:
  - Correlates actions, transactions, relationships, vendor events in real time.
  - Outputs: review_queue events, compensating_actions, governance events.

- Vendor Risk + Containment:
  - Monitors vendor-hosted events for anomalies and schema drift.
  - Outputs: containment alerts, review items.

- Real-Time Rule Enforcement:
  - Uses business_rules + function_definitions to validate actions on the fly.
  - Outputs: alerts and control events on violations.

- Reporting + Statements:
  - Aggregates payment and ledger events per customer/account.
  - Outputs: reporting-ready and statement-ready streams → Delta Lake.

- Cash Flow Forecasting:
  - Maintains per-entity projected cash flows (T+0/T+1/T+7/T+30).
  - Inputs: payments, sweeps, pools, vendor flows.
  - Outputs: forecasts to Delta Lake; alerts on threshold breaches.

- Liquidity Monitoring:
  - Continuously tracks liquidity positions (per-entity/pool/currency).
  - Detects breaches/concentrations in rolling windows.
  - Outputs: risk alerts and kinetic actions (e.g., sweep, limit adjustments).

## 4. Integration with Governance

All Flink decisions are governed:
- Bound to mandates.
- Logged as governance.audit-events.
- Linked via SHA-256 chains into proof_records.
- No opaque behavior.
