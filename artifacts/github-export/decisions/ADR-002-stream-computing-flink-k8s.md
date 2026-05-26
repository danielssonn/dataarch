# ADR-002: Stream Computing — Apache Flink on Kubernetes (AKS)

**Status:** Proposed  
**Date:** 2026-05-26

## Context

Confluent gives us events. For this platform we need:
- Real-time correlation across domains.
- Complex event processing (CEP) for kinetic decisions.
- Stateful windowing for reporting, statements, cash flow forecasting, liquidity monitoring.

We must avoid “dumb pipes” and ad hoc lambdas.

## Options Considered

| Option                    | Pros                             | Cons                                     |
|---------------------------|----------------------------------|------------------------------------------|
| Apache Flink (on K8s)     | Exactly-once, CEP, stateful, scalable, mature. | More complex to operate than serverless functions. |
| Cloud serverless (e.g., Event Grid + Functions) | Simple for lightweight logic. | Not ideal for stateful correlation, CEP, or long-lived joins. |
| Spark Streaming (Databricks) | Native in lakehouse. | Higher latency, less suitable for complex real-time CEP. |

## Decision

Use **Apache Flink on Kubernetes (AKS)** as the primary stream computation engine, integrated with Confluent and Databricks:
- RocksDB as state backend.
- Checkpointing every 30–60 seconds to Azure Blob Storage.
- Exactly-once semantics for critical decision jobs.

## Consequences

- Enables real-time kinetic incident correlation, vendor risk monitoring, rule enforcement.
- Provides foundation for reporting, statements, cash flow forecasting, liquidity monitoring.
- Flink is treated as a core platform service, not optional.
