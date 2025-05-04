```mermaid
flowchart TD
    A[Blueprint Submitted via Port or GitHub] --> B[PORC Validates and Stores Blueprint]
    B --> C[PORC Renders Terraform Configs]
    C --> D{Execution Path?}
    D -->|GitHub Action| E[Run terraform plan]
    D -->|PORC CLI| F[POST /api/v2/runs (plan)]
    E --> G[PORC Records Plan Status]
    F --> G
    G --> H{Approval Required?}
    H -->|Yes| I[Validate Change Record in ServiceNow]
    H -->|No| J[Proceed]
    I --> J
    J --> K{Apply Trigger}
    K -->|GitHub Action| L[Run terraform apply]
    K -->|PORC CLI/API| M[POST /api/v2/apply]
    L --> N[Sentinel Policy Evaluation]
    M --> N
    N --> O[Run Outcome Logged in Mongo]
    O --> P[Audit Trail & Metrics Streamed to Datadog/Dynatrace]
```