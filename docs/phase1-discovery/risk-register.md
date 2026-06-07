# Risk Register
## Smart Store Operations — Top 10 Risks

**Version:** 1.0 | **Date:** April 2026 | **Owner:** Project Manager

---

## Risk Scoring Matrix

**Likelihood:** 1 (Rare) → 5 (Almost Certain)  
**Impact:** 1 (Negligible) → 5 (Critical)  
**Risk Score = Likelihood × Impact** | **Threshold:** ≥12 = Critical, 8–11 = High, 4–7 = Medium, 1–3 = Low

---

## Risk Register

### R-001: Network Unreliability at Store Level

| Attribute | Value |
|-----------|-------|
| **Category** | Infrastructure |
| **Likelihood** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | 16 — CRITICAL |
| **Description** | Store ISP connections are unreliable, causing edge nodes to lose cloud connectivity frequently. Sensor data lost, alerts not delivered. |
| **Mitigation** | (1) 4G LTE failover on all stores. (2) 24-hour local SQLite buffer for offline resilience. (3) Sync-on-reconnect strategy with conflict resolution. (4) MQTT QoS 2 for critical alerts ensures delivery guarantee. |
| **Contingency** | If uplink fails >24h, dispatch field technician. Escalate to ISP with SLA penalty clause. |
| **Owner** | IT Infrastructure Manager |
| **Status** | Open |

---

### R-002: CV Model Accuracy Degradation Over Time

| Attribute | Value |
|-----------|-------|
| **Category** | Machine Learning |
| **Likelihood** | 4 (Likely) |
| **Impact** | 4 (Major) |
| **Risk Score** | 16 — CRITICAL |
| **Description** | Model mAP drops below 0.88 due to new SKUs, seasonal products, shelf layout changes, or lighting variations not seen in training data. |
| **Mitigation** | (1) Continuous monitoring via MLflow — track mAP on 7-day rolling window. (2) Automatic retraining trigger when mAP < 0.88 or new SKUs > 5%. (3) A/B testing framework for model variants. (4) Diverse data augmentation policy. |
| **Contingency** | Fall back to weight sensor + RFID fusion (no CV) for affected aisles. Manual shelf audit for impacted SKUs. |
| **Owner** | ML Engineering Lead |
| **Status** | Open |

---

### R-003: Hardware Supply Chain Delays

| Attribute | Value |
|-----------|-------|
| **Category** | Procurement |
| **Likelihood** | 3 (Possible) |
| **Impact** | 4 (Major) |
| **Risk Score** | 12 — CRITICAL |
| **Description** | Jetson Orin NX, PoE cameras, or shelf sensors face supply delays (global chip shortage, import clearance, vendor stockouts). |
| **Mitigation** | (1) Identify 3 competing vendors per component in RFQ. (2) 10% buffer stock in BoM. (3) Phased rollout — pilot 2 stores first, allowing time to source remaining. (4) Evaluate local vendors with faster lead times. |
| **Contingency** | Substitute with Google Coral Dev Board (pre-validated as backup). Use existing CCTV cameras initially where 4K not available. |
| **Owner** | Procurement Lead |
| **Status** | Open |

---

### R-004: Staff Resistance to Technology Adoption

| Attribute | Value |
|-----------|-------|
| **Category** | Change Management |
| **Likelihood** | 4 (Likely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 12 — CRITICAL |
| **Description** | Store staff perceive system as surveillance or job replacement. Low adoption of handheld app. LP officers ignore alerts. |
| **Mitigation** | (1) Involve store managers in design process (stakeholder interviews). (2) Position as "staff empowerment" not replacement. (3) Training program in local languages (Hindi, Kannada). (4) Gamification — leaderboards for restock response time. |
| **Contingency** | Assign "digital champion" per store for peer training. Provide incentives for app usage in first 3 months. |
| **Owner** | HR + Store Operations |
| **Status** | Open |

---

### R-005: DPDP Act 2023 Compliance Violation

| Attribute | Value |
|-----------|-------|
| **Category** | Legal / Compliance |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 5 (Critical) |
| **Risk Score** | 10 — HIGH |
| **Description** | Customer facial data or PII is inadvertently transmitted to cloud, stored beyond retention period, or shared without anonymisation. Regulatory penalty up to ₹250 Cr. |
| **Mitigation** | (1) All CV processing on-device — no raw video leaves edge node. (2) Automatic face blurring (DeepFace) before any footage share. (3) 90-day auto-deletion policy for video clips. (4) Privacy impact assessment before go-live. (5) Data Protection Officer appointed. |
| **Contingency** | Immediate system pause, forensic audit, engage privacy legal counsel. |
| **Owner** | Data Protection Officer + Legal |
| **Status** | Open |

---

### R-006: False Positive Alert Fatigue

| Attribute | Value |
|-----------|-------|
| **Category** | Operational |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 9 — HIGH |
| **Description** | High false positive rate (>5%) on LP or OOS alerts causes staff to ignore all alerts, defeating the system's purpose. |
| **Mitigation** | (1) Multi-sensor fusion increases confidence — alert only when fused_confidence ≥ 85%. (2) 5-minute alert deduplication cooldown. (3) 3-consecutive-frame threshold for OOS alerts. (4) Staff feedback loop to label false positives → retraining. |
| **Contingency** | Raise alert thresholds to 95% temporarily. Route alerts through a human review queue instead of direct push. |
| **Owner** | ML Engineering + Store Operations |
| **Status** | Open |

---

### R-007: Edge Node Hardware Failure in Production

| Attribute | Value |
|-----------|-------|
| **Category** | Infrastructure |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 9 — HIGH |
| **Description** | Jetson Orin NX failure due to heat, power surge, or component failure. Loss of CV processing for affected zone. |
| **Mitigation** | (1) Thermal management design (heatsink + fan, operating 0–45°C). (2) UPS on all edge nodes. (3) Watchdog process auto-restarts on crash. (4) 1 spare node per store as hot standby. (5) Remote fleet monitoring with auto-alert on node down. |
| **Contingency** | Manual shelf audit for affected zone. Field technician SLA: replacement within 4 hours. |
| **Owner** | IT Field Operations |
| **Status** | Open |

---

### R-008: Budget Overrun

| Attribute | Value |
|-----------|-------|
| **Category** | Financial |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 9 — HIGH |
| **Description** | Total project cost exceeds ₹1.63 Cr budget due to scope creep, hardware price increases, extended timelines, or cloud cost escalation. |
| **Mitigation** | (1) Fixed-price RFQ with vendors. (2) 10% contingency buffer. (3) Phased rollout — validate ROI on pilot before full deployment. (4) Cloud cost monitoring with alerts at 80% budget threshold. (5) Strict scope change control process. |
| **Contingency** | Reduce scope to core modules (shelf + queue) for remaining stores. Defer LP module to Phase 2 funding. |
| **Owner** | Project Manager + Finance |
| **Status** | Open |

---

### R-009: Integration Failure with Existing POS/WMS

| Attribute | Value |
|-----------|-------|
| **Category** | Technical |
| **Likelihood** | 3 (Possible) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 9 — HIGH |
| **Description** | POS or WMS systems lack APIs, have incompatible data formats, or vendor refuses to provide integration access. RFID reconciliation and restock automation blocked. |
| **Mitigation** | (1) POS/WMS API assessment in site survey (Phase 1). (2) Build integration adapters for common POS systems. (3) CSV/SFTP fallback for batch data exchange. (4) Engage POS vendor early for API access. |
| **Contingency** | Deploy middleware (MuleSoft/custom adapter) for data translation. Manual reconciliation workflow as interim. |
| **Owner** | Integration Lead |
| **Status** | Open |

---

### R-010: Scalability Bottleneck at Peak Load

| Attribute | Value |
|-----------|-------|
| **Category** | Performance |
| **Likelihood** | 2 (Unlikely) |
| **Impact** | 3 (Moderate) |
| **Risk Score** | 6 — MEDIUM |
| **Description** | System cannot handle 50,000 sensor events/sec per store during peak hours (festive season, promotions). Kafka lag increases, alerts delayed beyond SLA. |
| **Mitigation** | (1) Load test with 2× peak volume before go-live. (2) Kafka partition scaling plan. (3) Edge-side event batching and deduplication to reduce cloud ingestion. (4) Auto-scaling EKS pods for cloud services. |
| **Contingency** | Increase Kafka partitions and consumer instances. Temporarily reduce sensor telemetry frequency from 1s to 5s. |
| **Owner** | Cloud Architect |
| **Status** | Open |

---

## Risk Summary Dashboard

| Risk ID | Risk | Score | Priority |
|---------|------|-------|----------|
| R-001 | Network Unreliability | 16 | 🔴 Critical |
| R-002 | CV Model Degradation | 16 | 🔴 Critical |
| R-003 | Hardware Supply Delays | 12 | 🔴 Critical |
| R-004 | Staff Resistance | 12 | 🔴 Critical |
| R-005 | DPDP Compliance | 10 | 🟠 High |
| R-006 | False Positive Fatigue | 9 | 🟠 High |
| R-007 | Edge Node Failure | 9 | 🟠 High |
| R-008 | Budget Overrun | 9 | 🟠 High |
| R-009 | POS/WMS Integration | 9 | 🟠 High |
| R-010 | Scalability Bottleneck | 6 | 🟡 Medium |

---

## Review Schedule

- **Weekly** during implementation: Update likelihood/impact based on new information
- **Bi-weekly** in steering committee: Review critical risks, approve mitigations
- **Monthly** post-launch: Review all risks, close resolved, add new emerging risks

---

*Document Control: v1.0 | Classification: Internal | Living document — updated weekly*
