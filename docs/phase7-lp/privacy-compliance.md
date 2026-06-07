# Privacy Compliance Document — DPDP Act 2023
## Smart Store Operations — Phase 7: Loss Prevention

**Version:** 1.0 | **Date:** April 2026 | **Owner:** Data Protection Officer

---

## 1. Applicable Law

The **Digital Personal Data Protection Act, 2023** (DPDP Act) of India governs the processing of digital personal data. This document demonstrates compliance for all customer data processing within the Smart Store Operations platform.

---

## 2. Data Processing Principles

| Principle | Implementation |
|-----------|---------------|
| **Lawful Purpose** | All data processing serves legitimate business interests: inventory management, customer service, and theft prevention |
| **Purpose Limitation** | Data used only for shelf monitoring, queue management, and loss prevention — never for marketing profiling |
| **Data Minimization** | Only skeleton pose data processed for behaviour analytics — no facial features extracted. Weight/RFID data contains no PII |
| **Storage Limitation** | Video clips: 90 days. Sensor data: 30–90 days. Audit trail: 7 years (regulatory requirement) |
| **Accuracy** | Real-time processing ensures data currency. Stale tracking data purged every 10 minutes |

---

## 3. Personal Data Inventory

| Data Type | Contains PII? | Processing Location | Retention |
|-----------|--------------|--------------------| ----------|
| Shelf weight readings | No | Edge node | 90 days |
| RFID tag reads | No (EPC codes only) | Edge node → Cloud | 90 days |
| Overhead camera frames | Potential (human figures) | Edge node ONLY | Not stored (real-time processing) |
| Pose skeleton data | No (anonymized points) | Edge node | Session only |
| Customer tracking IDs | Pseudonymous (no real identity) | Edge node | Session only (max 2 hours) |
| Video clips (LP alerts) | Yes (human figures, faces blurred) | Edge node → S3 (encrypted) | 90 days |
| POS transaction data | No (aggregated) | Cloud | 1 year |
| LP audit trail | Yes (officer IDs) | Cloud (TimescaleDB) | 7 years |

---

## 4. Technical Privacy Controls

### 4.1 On-Device Processing (Edge-First Architecture)

**All raw camera data is processed on the edge node (Jetson Orin NX). No raw video or camera frames leave the device.**

```
Camera → RTSP stream → Edge Node (inference) → Structured data only → Cloud
                              ↓
                    Raw video discarded after processing
```

### 4.2 Face Anonymization

Before any video footage is stored or shared:

1. **DeepFace anonymization** applied to all detected faces
2. Gaussian blur (kernel size 99×99) on face regions
3. Anonymization performed **on-device** before any transfer
4. Original (pre-blur) frames are never stored or transmitted

### 4.3 Pseudonymous Tracking

- Customer tracking IDs (`CUST-XXXXXX`) are randomly generated per session
- No correlation to real identity, loyalty cards, or payment data
- Tracking IDs expire and are purged after 2 hours maximum
- No cross-session tracking capability

### 4.4 Encryption

| Layer | Standard |
|-------|----------|
| In-transit (all communications) | TLS 1.3 |
| At-rest (S3 video clips) | AES-256 (AWS KMS) |
| At-rest (TimescaleDB) | Transparent Data Encryption (TDE) |
| MQTT broker | TLS 1.3 on port 8883 |

---

## 5. Data Retention & Deletion Policy

| Data Type | Active Retention | Archive | Deletion |
|-----------|-----------------|---------|----------|
| Raw camera frames | Real-time only | None | Immediate (after inference) |
| Video clips (LP) | 90 days (S3) | None | Auto-delete at 90 days |
| Sensor telemetry | 30 days (TimescaleDB) | S3 Glacier (90 days) | Auto-delete at 120 days |
| Shelf state data | 90 days (TimescaleDB) | S3 Parquet (1 year) | Auto-delete at 1 year |
| Queue events | 90 days (TimescaleDB) | S3 Parquet (1 year) | Auto-delete at 1 year |
| LP alerts | 1 year (TimescaleDB) | S3 Archive (7 years) | Auto-delete at 7 years |
| LP audit trail | Indefinite (compliance) | — | No deletion (legal requirement) |

**Automated Enforcement:** TimescaleDB retention policies and S3 lifecycle rules enforce deletion automatically. No manual deletion required.

---

## 6. Data Subject Rights

Under DPDP Act 2023, data principals (customers) have the following rights:

| Right | Implementation |
|-------|---------------|
| **Right to Access** | Since we process no identifiable customer data (faces blurred, IDs pseudonymous), individual access requests are not applicable |
| **Right to Correction** | N/A — no personally identifiable records maintained |
| **Right to Erasure** | Customer tracking data auto-expires within 2 hours. Video clips auto-deleted at 90 days. On request: manual purge within 72 hours |
| **Right to Grievance Redressal** | Contact: Data Protection Officer at dpo@smartstore.co.in |
| **Right to Nominate** | Supported via DPO office |

---

## 7. Incident Response

### Data Breach Protocol

1. **Detection** — Automated monitoring for unauthorized access attempts
2. **Containment** — Isolate affected systems within 1 hour
3. **Assessment** — Determine scope and data types affected within 4 hours
4. **Notification** — Notify Data Protection Board of India within 72 hours (if PII involved)
5. **Remediation** — Implement fixes, update security controls
6. **Post-Incident Review** — Root cause analysis, lessons learned

---

## 8. Third-Party Data Sharing

| Scenario | Data Shared | Safeguards |
|----------|-------------|------------|
| Cloud infrastructure (AWS) | Encrypted structured data only | DPA signed, data in ap-south-1 region |
| WMS integration | SKU IDs, restock quantities | No PII, API key authentication |
| Law enforcement (on request) | LP video clips (faces blurred) | Court order required, DPO approval, logged in audit trail |

**No raw video or facial data is ever shared with third parties.**

---

## 9. Compliance Checklist

- [x] Data Protection Officer appointed
- [x] Privacy Impact Assessment completed
- [x] All camera processing on-device (no raw video transmitted)
- [x] Face anonymization (DeepFace) applied before any storage
- [x] Data retention policies automated
- [x] Encryption at rest and in transit (TLS 1.3 / AES-256)
- [x] Pseudonymous tracking (no real identity linkage)
- [x] Audit trail for all LP actions (immutable, append-only)
- [x] Incident response procedure documented
- [x] Data Processing Agreement with AWS
- [x] Staff privacy training included in onboarding
- [x] Annual privacy audit scheduled

---

**Data Protection Officer:** ________________  
**Signature:** ________________  
**Date:** ________________

*Document Control: v1.0 | Classification: Confidential | Review: Annual or on regulatory change*
