# 📄 PDC Contract: secure-deploy

## 📌 Metadata
- **Environment**: prod
- **Region**: us-east
- **Artifact**: webapp
- **Owner**: team-app

---

## 🛠️ Pipeline Type: `promotion`

### 🎯 Stages

#### 🔍 Verify
- **Description**: Metadata and repo hygiene
- **Gates**: `VerifyMetadata`, `SecretScan`

#### 🔐 Secure
- **Description**: License, SBOM, CVEs
- **Gates**: `LicenseScan`, `VulnCheck`

#### 🚀 Promote
- **Description**: Policy and manual approvals
- **Gates**: `PolicyCheck`, `Escalation`

---

## 🔗 Control Flow Diagram

```mermaid
graph LR
  Start(["🔵 Start"]) --> VerifyMetadata["🛡️ Verify Metadata<br><sub>Inputs: app_code, env, repo_url</sub>"]
  VerifyMetadata --> SecretScan["🕵️ Secret Scan<br><sub>Tool: GHAS</sub>"]
  SecretScan --> LicenseScan["📜 License Scan<br><sub>Tool: Wiz, Input: sbom</sub>"]
  LicenseScan --> VulnCheck["🧪 Vulnerability Check<br><sub>Tool: AquaSec</sub>"]
  VulnCheck --> PolicyCheck["📋 Policy Check<br><sub>Condition: all_previous_passed</sub>"]
  PolicyCheck --> Escalation["⚠️ Escalation<br><sub>Condition: manual_approval</sub>"]
```

---

## 🧩 Gate Definitions

### 🛡️ Verify Metadata
- **Inputs**: `app_code`, `env`, `repo_url`

### 🕵️ Secret Scan
- **Tool**: GitHub Advanced Security (GHAS)

### 📜 License Scan
- **Tool**: Wiz
- **Inputs**: `sbom`

### 🧪 Vulnerability Check
- **Tool**: AquaSec

### 📋 Policy Check
- **Condition**: `all_previous_passed`

### ⚠️ Escalation
- **Condition**: `manual_approval`
