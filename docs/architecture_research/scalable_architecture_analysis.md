# Scalable Architecture Patterns for High-Volume, Sub-Second Document Processing

## Executive Summary and Objectives

Enterprises increasingly expect near-instant document processing across millions of pages and diverse formats: scanned images, PDFs, Office documents, and spreadsheets. This report provides a prescriptive architecture to meet that bar—delivering throughput at scale while reliably achieving sub-second per-document latencies for common formats. The core architectural strategy combines event-driven ingestion with queue-based load leveling, stream-first processing where latency matters, and containerized microservices orchestrated by Kubernetes for elastic scaling and operational resilience. The approach applies cloud-native design principles to ensure portability, observability, and disciplined operations.

The objectives are threefold. First, the system must sustain high throughput for bulk workloads (1000+ documents per day, with capacity headroom for growth and bursts). Second, it must achieve sub-second latency for format-specific paths that are amenable to accelerated extraction, while gracefully degrading to higher-latency paths for complex formats only when necessary. Third, it must be reliable: tolerant to downstream spikes and faults, with clear controls for retries, backoff, idempotency, and dead-letter queues to prevent data loss or duplication.

The recommended high-level architecture is:
- Event-driven ingestion and asynchronous processing to decouple intake from downstream compute, enabling parallelization and natural load leveling via queues and streams.[^6][^7][^8]
- Stream-first processing with Apache Flink for low-latency, stateful pipelines where event-time semantics and windowing are required; Spark is used for batch-heavy analytics or less latency-sensitive workloads.[^16]
- Kubernetes for container orchestration, with Horizontal Pod Autoscaler (HPA) to elastically scale stateless workers and gateways using CPU, memory, and custom metrics.[^9]
- Cloud-native engineering practices (Twelve-Factor App) for config, logging, disposability, and concurrency to achieve operational scale and portability.[^1]

We conclude with three actionable reference implementations—Kafka-first for high-throughput event streaming, RabbitMQ-first for traditional queueing with complex routing, and a balanced hybrid—that engineering teams can tailor to their existing platforms and compliance constraints. The design choices are grounded in authoritative sources on event-driven architecture, microservices, Kubernetes autoscaling, messaging trade-offs, and resilience patterns.[^6][^7][^8][^2][^3][^4][^9][^10][^11][^12][^16]

### Target Outcomes and SLAs

Sub-second latency is feasible for a large subset of common document types when extraction is format-aware and minimized LLM usage is balanced with rule-based extraction. Recent experimental results on enterprise-scale document processing show that table-based methods can achieve near-perfect accuracy with total latencies around 0.3–1.6 seconds across DOCX, XLSX, and many PDFs, and image-based pipelines can realize approximately 0.6 seconds per document with high accuracy by pairing OCR with targeted LLM steps rather than naive end-to-end multimodal inference.[^17] Sustaining bulk throughput requires an architecture that routes each document to the most efficient method for its format while maintaining strict idempotency, error isolation, and backpressure controls to protect downstream dependencies.

## Workload Profile and Performance Requirements

The processing pipeline handles heterogeneous documents, typically including:
- Images (PNG/JPG) representing scanned pages.
- PDFs ranging from vector text to complex multi-column layouts.
- Office documents (DOCX, XLSX) with structured tables and embedded content.

Operationally, we must support an ingestion burst profile—arrivals are uneven throughout the day and may spike during business hours. The system should process 1000+ documents per day with sub-second average end-to-end latency for the dominant formats, while absorbing bursts through queue buffering and autoscaling. Practically, the workload decomposes into two classes:

- Fast-path: well-structured documents (DOCX, XLSX, many PDFs) that lend themselves to table-based extraction with minimal LLM usage, achieving 0.3–1.6 seconds per document at high accuracy.[^17]
- Slow-path: image-heavy or complex PDFs (multi-column, dense tables) requiring OCR and more sophisticated extraction; latencies increase if end-to-end multimodal inference is used naïvely.[^17]

The pipeline must preserve strict guarantees across at-least-once delivery:
- Idempotency: repeated processing of the same document must not produce duplicates or inconsistent state.
- Ordering: preserved per partition/key when necessary to maintain correctness (e.g., document version sets).
- Backpressure: rate-control and queue-leveling prevent overload of stores and downstream services under burst load.[^10]

To situate the target outcomes, Table 1 summarizes representative performance results for format-aware extraction methods reported in recent work. The “Total Time” column demonstrates feasibility for sub-second and low-seconds latencies across common formats.

To illustrate representative outcomes for different methods and formats, the following table aggregates results from enterprise-scale experiments.[^17]

Table 1: Representative performance results by format and method

| Format | Method                            | Precision | Recall | F1    | Success Rate | Total Time (s) |
|--------|-----------------------------------|-----------|--------|-------|--------------|----------------|
| PNG    | PaddleOCR table                   | 0.998     | 0.997  | 0.997 | 100%         | 0.6            |
| DOCX   | Docling table                     | 1.000     | 1.000  | 1.000 | 100%         | 0.3            |
| XLSX   | MarkItDown table                  | 1.000     | 1.000  | 1.000 | 100%         | 0.3            |
| PDF    | Docling table                     | 1.000     | 1.000  | 1.000 | 100%         | 1.6            |

These results substantiate the architectural imperative: route each document to the best method for its format, reserve heavier inference for cases where it adds unique value, and minimize end-to-end generation when spatial or structural signals suffice.

### Document Types and Extraction Complexity

Format-aware routing is central to achieving sub-second latencies. Table-based extraction methods deliver near-perfect accuracy with minimal LLM usage for structured documents (DOCX, XLSX, many PDFs), while direct or multimodal LLM methods—though consistent—introduce significant inference latencies (13–15 seconds) that are incompatible with sub-second targets.[^17] Image-based pipelines benefit from OCR paired with targeted LLM steps (e.g., coordinate-aware extraction) rather than naive end-to-end multimodal approaches; this yields major speedups (e.g., 54× faster than multimodal for certain image cases) while maintaining high accuracy.[^17] Complex PDFs and image-heavy documents may require multi-step pipelines and mixed models; these should be treated as slow-path exceptions and isolated from fast-path traffic.

## Core Architectural Patterns for Scale

### Microservices Architecture

Microservices provide a disciplined decomposition around business capabilities and bounded contexts, enabling independent scaling, deployment, and fault isolation.[^2] For document processing, the decomposition typically includes an ingestion service, routing/dispatcher, extraction workers, a persistence service, and a notification service. Each service owns its data store (database-per-service) and exposes APIs for well-scoped operations; cross-service interactions are decoupled via asynchronous messaging and an API gateway for synchronous calls. The gateway handles cross-cutting concerns such as authentication, rate limiting, and TLS termination, offloading these tasks from business logic and improving security posture.[^2][^3]

Key design principles include:
- Loose coupling and high cohesion: model services around domain boundaries; avoid shared schemas and libraries that entangle deployments.[^2]
- Asynchronous messaging: use queues/streams to level load, prevent chatty APIs, and reduce network latency sensitivity.[^2][^3]
- Private data storage: each service persists its own data; use materialized views or event-carried state for read-side needs without coupling to internal schemas.[^2][^3]
- Observability: instrument services with logs, metrics, and distributed tracing (e.g., OpenTelemetry) to track processing across service boundaries.[^2]

### Event-Driven Architecture (EDA)

Event-driven architecture (EDA) is well-suited for high-volume document processing because it decouples producers from consumers and supports continuous event flows with near real-time reaction.[^6][^7][^8] A practical pattern taxonomy includes:

- Publish-subscribe: documents and extraction events are published to topics; downstream services subscribe as needed (e.g., persistence, audit, notifications).[^5]
- Competing consumers: multiple workers consume from a shared queue/stream, parallelizing processing and increasing throughput.[^5]
- Consumer groups: each event is processed by exactly one consumer within the group, enabling scalable parallel processing with ordering guarantees per partition/key.[^5]
- Partitioning: topics are partitioned to increase concurrency and preserve ordering semantics for related documents (e.g., by document set ID).[^5]
- Shock absorber: queues buffer bursts, protecting downstream services from overload; processors consume at steady rates.[^5][^10]
- Guaranteed delivery with idempotency: ensure no data loss in the presence of failures; implement deduplication and replay-safe consumers.[^5]
- Dead-letter queues (DLQs): isolate poison messages for diagnosis and controlled reprocessing.[^5]

EDA’s benefit is two-fold: scalability through parallel consumer patterns and resilience through buffering, isolation, and explicit error handling.

### Cloud-Native Design (Twelve-Factor App)

The Twelve-Factor App methodology provides a foundation for building scalable, portable, and observable services.[^1] Critical factors for this workload include:
- Config: store configuration in the environment; avoid hard-coding and enable per-environment overrides.
- Backing services: treat queues, caches, and databases as attached resources to swap or scale independently.
- Processes: design stateless services; persist state in backing stores to enable elasticity.
- Concurrency: scale out via the process model; use workers aligned with queues/topics.
- Disposability: fast startup and graceful shutdown; ensure idempotent processing and safe termination.
- Logs: treat logs as event streams; centralize and correlate across services for traceability.
- Dev/prod parity: align environments to minimize surprises during deployment; support continuous delivery.

These practices reduce operational friction and align with Kubernetes scaling, autoscaling, and disposability requirements.

## Messaging and Event Transport

Apache Kafka and RabbitMQ are proven messaging substrates but differ in their design, operational model, and typical use cases.[^4] Kafka is stream-first: persistent logs, partitioned topics, consumer groups, and pull-based consumption favor high-throughput event streaming, replay, and long-term storage. RabbitMQ is queue-first: exchanges and bindings support complex routing (topics, headers, direct), with push-based consumption and per-queue competing consumers suited to traditional messaging patterns.

To clarify the trade-offs, Table 2 summarizes key differences and their implications for document processing workloads.

Table 2: Kafka vs RabbitMQ comparison

| Dimension                | Apache Kafka                                                                 | RabbitMQ                                                                   |
|-------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Architecture            | Persistent log; partitioned topics; consumer groups                           | Queues with exchanges and bindings; routing keys/headers                   |
| Consumption Model       | Pull; consumers control pace; replay supported                                | Push; broker pushes to consumers; prefetch controlling backpressure        |
| Scalability             | Horizontal scale via partitions; high throughput at scale                     | Scale via queues and additional brokers; throughput improves with more nodes |
| Storage                 | Long-lived retention; stream storage; supports event sourcing                 | Transient by default; persistence configurable; not intended for long-term logs |
| Ordering                | Per-partition ordering; global ordering requires single partition             | Per-queue FIFO; ordering affected by competing consumers                   |
| Typical Use Cases       | Event streaming, audit logs, replay, stream processing                        | Task queues, RPC, complex routing, background jobs                         |
| Ecosystem               | Streams API, Connect, Schema Registry, Tiered Storage (roadmap/evolution)     | Plugins, wide client language support, integration gateways                |
| TCO Considerations      | Higher storage costs at scale; more managed options available                 | Lower storage footprint; may require additional components for streaming   |

For sub-second document processing:
- Choose Kafka when high-throughput event streaming, replay, partitioned parallelism, and durable logs are core requirements (e.g., multi-tenant pipelines with audit and stateful stream processing).
- Choose RabbitMQ when traditional queue semantics, complex routing, and task-worker patterns suffice; combine with DLQs and backoff policies to isolate errors and prevent overload.[^4]

In both cases, adopt DLQs for poison messages, idempotency keys for deduplication, and format-aware routing metadata attached to messages to enable dispatch to the right extraction method.

## Stream and Batch Processing Frameworks

Document processing pipelines differ in their latency sensitivity and statefulness. Stream-first frameworks such as Apache Flink are designed for continuous, low-latency processing with event-time semantics, windowing, and flexible state management.[^16] Spark’s micro-batch model excels at batch analytics and integrated ecosystems; it is a strong fit for large-scale retrospective analysis but imposes higher latencies for streaming.[^16]

Table 3 contrasts Flink and Spark for this workload.

Table 3: Flink vs Spark comparison

| Dimension                | Apache Flink                                                      | Apache Spark                                                        |
|-------------------------|-------------------------------------------------------------------|----------------------------------------------------------------------|
| Processing Model         | True streaming runtime; low-latency pipelines                      | Micro-batch streaming; higher latency than Flink                     |
| Windowing                | Event-time and processing-time windows; session windows            | Time-based windows; less flexible than Flink                         |
| State Management         | Advanced, flexible state for real-time computations                | Stateful operations via RDs/DataFrames; less specialized for streaming |
| Fault Tolerance          | Distributed snapshots; rapid recovery with minimal disruption      | RDD-based lineage and reconstruction                                 |
| Performance Orientation  | Real-time analytics; low-latency stream processing                 | Batch-oriented; strong ecosystem for analytics                       |
| Ecosystem                | Integrates well with Kafka; less broad than Spark’s                | Mature ecosystem (SQL, ML, graph)                                    |
| Use Cases                | Stream-first pipelines, event-time processing, low-latency SLAs    | Batch analytics, ETL, micro-batch streaming with relaxed latency     |

A balanced strategy uses Flink for the real-time pipeline—routing, transformation, and stateful control—and Spark for downstream analytics, reporting, and ad-hoc queries. This separation optimizes latency where it matters while retaining Spark’s rich analytics capabilities.

### When to Use Flink vs Spark

Use Flink when:
- You need sub-second end-to-end latency for document routing and extraction control.
- Event-time semantics and windowing (e.g., session-aware batching or watermarking) are required.
- Stateful predicates drive routing decisions or deduplication.[^16]

Use Spark when:
- Batch-heavy analytics dominate and latency requirements are relaxed.
- Integrated SQL/ML/graph tooling is a priority and streaming is micro-batched.[^16]

## Containerization and Orchestration

Docker packaging provides consistency across environments; Kubernetes provides the control plane for scheduling, service discovery, load balancing, and autoscaling.[^15] In a document processing system, stateless ingestion gateways and extraction workers scale horizontally under load; stateful services (databases, stores) remain separate. An API gateway terminates TLS, authenticates clients, and routes to upstream services while offloading cross-cutting concerns.[^2][^3]

Kubernetes Horizontal Pod Autoscaler (HPA) is the primary mechanism for elastic scaling. HPA adjusts replica counts based on CPU, memory, custom, or external metrics using a control loop that evaluates desired replicas against observed metrics, tolerance, and stabilization windows.[^9] Table 4 provides a configuration cheat sheet for HPA in this workload.

Table 4: HPA configuration cheat sheet

| Parameter/Field                                   | Purpose/Behavior                                                                                 | Notes/Default                                      |
|---------------------------------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------------|
| metrics (CPU, memory, custom, external)           | Drives scaling decisions                                                                          | Use container resource metrics for granularity[^9] |
| targetAverageUtilization (e.g., CPU 60%)          | Desired utilization across pods                                                                   | Set per workload; avoid masking hot containers[^9] |
| tolerance                                         | Prevents scaling thrashing on small metric changes                                                | Default ~10%; configurable at cluster level[^9]    |
| stabilizationWindowSeconds                        | Smooths scale-down; uses highest recommendation over window                                        | Default ~300s for scale-down[^9]                   |
| behavior.policies (scaleUp/scaleDown)             | Controls rate of change (Pods or Percent) and selection policy (Max, Min, Disabled)               | Defaults allow aggressive scale-down[^9]           |
| sync period                                       | HPA control loop evaluation interval                                                               | Default ~15s; configurable[^9]                     |
| multiple metrics                                  | HPA evaluates each metric; largest desired replica count chosen                                    | Enables conservative scaling[^9]                   |
| missing metrics handling                          | Excludes failing pods; conservatively assumes 0% for scale-up                                      | Dampens instability during pod churn[^9]           |
| containerResource metric                          | Scale on specific container CPU/memory (e.g., extraction worker)                                   | Kubernetes v1.30+; granular scaling[^9]            |
| custom/external metrics                           | Scale on business-relevant signals (e.g., queue depth, lag)                                        | Requires adapters; align with backlog thresholds   |

For multi-tenant systems, consider partitioning topics and dedicating consumer groups per tenant to limit blast radius and enable tenant-aware autoscaling. Managed Kubernetes offerings (e.g., EKS) provide HPA support aligned with cloud operational practices.[^14]

### Autoscaling Design

Define autoscaling thresholds that reflect actual work, not only generic CPU. In this pipeline:
- Scale on queue depth or stream lag to catch intake spikes early; use custom metrics for topic partition backlog.
- Scale workers on container CPU/memory where extraction is compute-intensive; add external metrics for document arrival rates.
- Balance scale-up aggressiveness with stability windows to prevent oscillation; tune policies to allow fast scale-up during bursts and conservative scale-down to avoid thrashing.[^9]

## Load Balancing Strategy

Load balancing distributes requests across healthy instances to maximize throughput and minimize latency. At Layer 7 (application layer), content-based routing can direct documents to specialized services based on format, size, or routing hints. East-west traffic within the cluster is handled via service mesh or standard Kubernetes services, while north-south ingress terminates at an API gateway.[^13][^2][^3]

Table 5 compares common algorithms and their suitability for document routing.

Table 5: Load balancing algorithms comparison

| Algorithm                     | How It Works                                           | Pros                                                       | Cons                                                       | Suitability for Document Routing               |
|------------------------------|--------------------------------------------------------|------------------------------------------------------------|------------------------------------------------------------|------------------------------------------------|
| Round Robin                  | Cyclical distribution across instances                 | Simple; fair when instances are similar                    | Ignores current load; may send traffic to busy servers     | Good default for homogeneous workers           |
| Least Connections            | Route to instance with fewest active connections       | Adaptive; better for variable request complexity           | Overhead tracking connections; not capacity-aware          | Useful when requests have varied durations     |
| Weighted (Round Robin/Least) | Assign weights based on instance capacity              | Better resource utilization in heterogeneous pools         | Manual tuning; potential misallocation                     | Fit for mixed-capacity clusters                |
| Hash-based                   | Hash on client/key to select instance                  | Affinity; preserves ordering per key without sticky sessions | Risk of hot spots if key distribution is skewed            | Good for per-document or per-tenant affinity   |
| Geo-location                 | Route based on client/server geography                 | Latency reduction; regional compliance                     | Operational complexity; potential underutilization         | Applicable for multi-region deployments        |
| Resource-based               | Choose instance by real-time CPU/memory/I/O            | Fits workload to resources dynamically                     | Monitoring overhead; stale metrics can misguide routing    | Strong for elastic worker pools                |

Implement rate limiting at the gateway to protect upstream services and enforce fairness, and use health checks and circuit breakers to avoid sending traffic to unhealthy instances.[^11][^13]

### Gateway and Service Mesh Considerations

The API gateway centralizes authentication, authorization, TLS termination, and coarse-grained rate limiting; it also performs content-based routing for document intake and can aggregate responses for client-facing operations.[^2][^3] Service meshes add mTLS, traffic shaping, and circuit breaking at the mesh layer, offloading resilience from application code and standardizing policies across services.[^2]

## Fault Tolerance and Resilience Patterns

Resilience patterns prevent localized failures from cascading across the system. The Circuit Breaker pattern monitors dependency health and blocks requests to failing services, transitioning through closed, open, and half-open states to balance recovery and protection.[^11] Retry patterns must include exponential backoff and jitter to avoid synchronized retries and thundering herds; idempotency ensures retried messages do not corrupt state.[^11] DLQs isolate problematic messages for analysis and controlled reprocessing, protecting the main pipeline’s throughput.[^5]

Table 6 provides a fault tolerance playbook mapping patterns to symptoms and risks.

Table 6: Fault tolerance playbook

| Symptom/Risk                                   | Pattern                | Action                                                                                 | Risks/Considerations                                            |
|------------------------------------------------|------------------------|----------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| Repeated downstream failures                    | Circuit Breaker        | Trip after threshold; fail fast; probe in half-open state                              | Configure thresholds/timers per dependency; avoid long timeouts[^11] |
| Transient errors (network glitches)             | Retry with Backoff     | Retry with exponential backoff + jitter; bound attempts                                | Ensure idempotency; avoid amplifying load during incidents[^11] |
| Poison messages (unprocessable documents)       | DLQ + Isolation        | Route to DLQ; analyze; replay after fix                                                | Track DLQ volume; prevent unbounded growth[^5]                  |
| Spike in arrival rate                           | Load Leveling (Queue)  | Buffer in queue; workers consume at controlled rate                                    | Avoid unbounded backlog; tune autoscaling on backlog[^10]       |
| Dependency overload (store/API)                 | Bulkhead               | Isolate resources per service/tenant; limit concurrent requests                        | Prevents cross-component contagion; requires resource partitioning[^2][^3] |
| Cascading failures across services              | Circuit Breaker + Rate Limit | Combine fast-fail with rate limits; degrade gracefully                              | Instrument state transitions; test recovery paths[^11]          |

### Sagas and Distributed Transactions

For multi-step document workflows spanning microservices (e.g., extract, enrich, validate, persist), sagas break the transaction into local steps with compensating actions for rollback.[^2][^3] Apply event-carried state transfer and read-side materialized views to avoid distributed transactions and maintain service autonomy. Align the saga orchestration with EDA and stream processing to ensure correct state transitions under at-least-once delivery and partial failures.

## Performance Optimization for Sub-Second Latency

Achieving sub-second latencies hinges on method selection tuned to document format. Table-based extraction with minimal LLM usage is consistently fast for structured documents; OCR plus targeted LLM is effective for image-heavy inputs; naive multimodal approaches should be avoided for latency-sensitive paths.[^17] Additionally, reduce end-to-end latency by:
- Parallelizing per-document processing where safe (e.g., partition by document set or tenant).
- Collocating compute with storage to minimize I/O overhead.
- Caching derived data where beneficial (e.g., template metadata, configuration).
- Avoiding heavy serialization formats for internal messaging; use efficient, compact formats to reduce CPU overhead.

### Backpressure and Load Leveling

Queues act as shock absorbers between intake and processing, smoothing bursts and decoupling ingestion from downstream rates.[^10] Combine queue-based load leveling with HPA policies that respond to backlog thresholds, and apply rate limiting to protect shared resources. Tune autoscaling to scale up quickly when backlog grows and scale down conservatively to prevent oscillation; configure HPA stabilization windows and behavior policies accordingly.[^9][^10]

## Reference Architectures and Technology Selection Guide

We present three actionable reference implementations. Each shares microservices decomposition and Twelve-Factor alignment but differs in messaging and processing framework choices to match operational context and team skill sets.

### Reference A: Kafka + Flink + Kubernetes (Stream-First)

- Components: Kafka topics with partitions keyed by document ID or tenant; consumer groups for parallel processing; Flink stream pipeline for event-time processing, stateful deduplication, and windowing; Kubernetes HPA for workers; API gateway; DLQ for failed messages.
- Data flow: Document intake published to Kafka; Flink jobs route and transform events; extraction workers consume from topics; persistence service stores results; audit events published to separate topics.
- Pros: High throughput, replay, ordered per-partition processing, low-latency streaming, robust stateful processing; strong fit for multi-tenant workloads and continuous event flows.[^4][^16]
- Cons: Operational complexity; storage costs for long-lived streams; requires Kafka and Flink expertise.[^4][^16]

### Reference B: RabbitMQ + Kubernetes (Queue-Centric)

- Components: Queues with exchanges for routing; per-format queues; DLQ; backoff policies; Kubernetes HPA on CPU/memory or custom metrics (queue depth); API gateway; workers as competing consumers.
- Data flow: Document intake enqueued; workers consume, competing for messages; persistence service writes results; errors routed to DLQ with retry policies.
- Pros: Simpler operational model for task queues; rich routing patterns; good fit for traditional microservice messaging and RPC.[^4]
- Cons: Not optimized for long-term event streaming or replay; per-queue ordering; throughput scaling often requires multiple brokers.[^4]

### Reference C: Hybrid Messaging + Stream Processing

- Components: Use RabbitMQ for intake and immediate task distribution; bridge to Kafka for downstream analytics and replay; Spark for batch analytics; Kubernetes for orchestration.
- Data flow: Intake routes through RabbitMQ; lightweight workers perform fast-path extraction; selected events flow to Kafka; Spark jobs run periodic analytics; DLQs and retries at intake layer.
- Pros: Balances operational simplicity for intake with analytics and durability of streams; leverages RabbitMQ routing and Kafka replay; Spark’s analytics ecosystem.[^4][^16]
- Cons: Increased architectural complexity; dual platform operations; careful governance needed to avoid fragmentation.[^4][^16]

Table 7 aligns stack choices to workload attributes and operational preferences.

Table 7: Stack selection matrix

| Attribute/Preference          | Kafka + Flink                    | RabbitMQ + K8s                   | Hybrid (RabbitMQ + Kafka + Spark)         |
|-------------------------------|----------------------------------|----------------------------------|-------------------------------------------|
| Throughput (events/sec)       | Very high                        | High (with more brokers)         | High (intake high; downstream scalable)   |
| Latency (per document)        | Sub-second feasible               | Sub-second feasible              | Sub-second for fast-path; analytics slower |
| Operational Complexity        | Higher                           | Lower                            | Higher (dual ops)                         |
| Routing Sophistication        | Topic-based; schema-driven       | Rich exchanges/bindings          | Rich intake; stream analytics downstream  |
| Replay/Audit Needs            | Strong (log retention)           | Limited                          | Strong via Kafka                          |
| Team Expertise                | Kafka/Flink                      | RabbitMQ/K8s                     | Mixed                                     |
| Best Fit                      | Stream-first, multi-tenant       | Traditional queueing             | Intake simplicity + downstream analytics  |

## Implementation Roadmap

A phased approach mitigates risk and builds operational maturity.

Phase 1: Foundations
- Deploy API gateway and Kubernetes cluster; define microservices boundaries; implement config management per Twelve-Factor.[^1][^2]
- Instrument observability: logs as event streams, metrics, distributed tracing; establish SLOs for latency and throughput.[^2]

Phase 2: Messaging and Load Leveling
- Choose Kafka or RabbitMQ; implement queues/streams; enable DLQ and backoff policies.[^4][^5]
- Add rate limiting at gateway; introduce HPA with initial CPU/memory targets; define custom metrics for queue depth/backlog.[^9][^10][^13]

Phase 3: Fast-Path Extraction
- Implement format-aware routing; deploy fast-path methods for DOCX/XLSX/PDF; minimize LLM usage for sub-second targets; enforce idempotency keys.[^17]
- Integrate resilience patterns (circuit breaker, retries) for downstream calls.[^11]

Phase 4: Autoscaling and Observability
- Tune HPA behavior policies and stabilization windows; add container resource metrics for key workers; establish alerting on backlog and lag.[^9]
- Expand tracing across ingestion to persistence; refine SLO dashboards and error budgets.

Phase 5: Load Testing and Fault Injection
- Conduct throughput tests to validate target capacity; inject failures (network, dependency) to verify circuit breakers, DLQs, and sagas.[^11][^5]
- Iterate routing and scaling thresholds to ensure sub-second latencies under realistic burst profiles.

Phase 6: Production Rollout
- Gradual rollout with canaries; monitor key metrics; scale clusters based on validated thresholds; finalize runbooks and on-call procedures.

## Risk, Compliance, and Observability

Data privacy and compliance (PII handling, audit trails, sovereignty) must be enforced via gateway policies, encryption in transit (mTLS), and strict access controls (RBAC). At-least-once delivery necessitates idempotency and deduplication strategies across consumers to prevent duplicates, with ordering preserved per partition/key when required by business rules.[^2][^11] SLOs and error budgets should track end-to-end latency, throughput, and DLQ rates; circuit breaker state changes and retry outcomes must be observable to diagnose and prevent cascading failures.[^11]

### Operational Risks and Mitigations

- Backlog growth during bursts: Mitigate via queue-based load leveling, rate limiting, and autoscaling on backlog metrics; monitor queue depth and consumer lag.[^10]
- Hot partitions: Prevent by improving partitioning keys (hash on tenant/document set), adjusting topic counts, and distributing traffic across partitions; observe skew metrics.[^5]
- Poison messages: Route to DLQ; analyze and fix; set bounds on DLQ size; avoid unbounded retries that consume resources.[^5]
- Regional failover: Use global load balancers; design multi-region routing with circuit breaker thresholds tuned per region; test recovery paths under controlled failover.[^11]

## Appendices

Glossary
- API Gateway: Front door for clients; routes requests, handles auth, TLS termination, and cross-cutting concerns.[^2][^3]
- Circuit Breaker: Fault tolerance pattern that blocks calls to failing dependencies and probes recovery in half-open state.[^11]
- Consumer Group: Set of consumers that share partition workloads, ensuring exactly-once processing per partition.[^5]
- Dead-Letter Queue (DLQ): Queue for messages that cannot be processed successfully; isolates poison messages for later analysis.[^5]
- Horizontal Pod Autoscaler (HPA): Kubernetes controller that scales pods based on metrics to match demand.[^9]
- Idempotency: Property where repeated processing yields the same result; essential for at-least-once delivery.
- Shock Absorber: Pattern using queues to buffer bursts and smooth downstream load.[^5][^10]

Configuration Templates (Illustrative)
- HPA targeting CPU utilization for extraction workers:
  - metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
- HPA with behavior policies and stabilization window:
  - behavior:
    - scaleUp:
        policies:
          - type: Percent
            value: 100
            periodSeconds: 15
    - scaleDown:
        policies:
          - type: Percent
            value: 10
            periodSeconds: 60
  - stabilizationWindowSeconds: 300
- Kafka consumer group config (per-tenant partitioning):
  - partitions: 12 (per tenant)
  - key.serializer: TenantDocumentKeySerializer
- RabbitMQ queue bindings:
  - exchange: doc intake
  - bindings:
    - routing key: format.pdf
    - queue: pdf-processing
  - DLQ: pdf-dlq; retry: exponential backoff with jitter

Performance Testing Checklist
- Define document mix (PNG, PDF, DOCX, XLSX) and average/peak arrival rates.
- Instrument queue depth, consumer lag, end-to-end latency histograms.
- Validate HPA scaling: scale-up under backlog growth; scale-down stability.
- Inject failures: dependency timeouts, broker node failures, poison messages.
- Verify idempotency and deduplication under retries.
- Audit logging and tracing across services; confirm SLO dashboards.

Information Gaps
- Managed Kafka vs RabbitMQ operational cost at target throughput and retention policies.
- Latency percentiles (p50/p95/p99) under bursty workloads for specific frameworks.
- Exact throughput limits for topic partitions and consumer groups based on message size, key distribution, and disk I/O.
- Hardened performance tuning guidelines for extreme burst traffic (e.g., batch uploads).
- Compliance controls for PII and audit trails tailored to document content.
- Disaster recovery RPO/RTO objectives and multi-region failover validation specifics.
- Network topology implications (service mesh, mTLS overhead) on throughput/latency.

## References

[^1]: The Twelve-Factor App. https://12factor.net/
[^2]: Microservices Architecture Style (Microsoft Learn). https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices
[^3]: 7 Essential Microservices Design Patterns (Atlassian). https://www.atlassian.com/microservices/cloud-computing/microservices-design-patterns
[^4]: Apache Kafka vs. RabbitMQ Comparison (Quix). https://quix.io/blog/apache-kafka-vs-rabbitmq-comparison
[^5]: Event-Driven Architecture Patterns (Solace). https://solace.com/event-driven-architecture-patterns/
[^6]: What is EDA? (AWS). https://aws.amazon.com/what-is/eda/
[^7]: Event-Driven Architecture (Confluent). https://www.confluent.io/learn/event-driven-architecture/
[^8]: Event-Driven Architecture Style (Microsoft Learn). https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/event-driven
[^9]: Horizontal Pod Autoscaling (Kubernetes Docs). https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
[^10]: Queue-Based Load Leveling Pattern (Microsoft Learn). https://learn.microsoft.com/en-us/azure/architecture/patterns/queue-based-load-leveling
[^11]: Circuit Breaker Pattern (Microsoft Learn). https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
[^12]: What is Load Balancing? (AWS). https://aws.amazon.com/what-is/load-balancing/
[^13]: 10 Load Balancing Techniques (Medium). https://vertisystem.medium.com/10-load-balancing-techniques-mastering-the-art-of-distributed-computing-9ab053ad138f
[^14]: Scale pod deployments with HPA (Amazon EKS Docs). https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html
[^15]: Docker vs Kubernetes: Comprehensive Comparison (Better Stack). https://betterstack.com/community/guides/scaling-docker/docker-vs-kubernetes/
[^16]: Flink vs. Spark Comparison (DataCamp). https://www.datacamp.com/blog/flink-vs-spark
[^17]: Hybrid OCR-LLM Framework for Enterprise-Scale Document Information Extraction (arXiv). https://arxiv.org/html/2510.10138v1