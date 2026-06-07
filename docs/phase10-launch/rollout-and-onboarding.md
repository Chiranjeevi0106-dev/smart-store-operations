# Phase 10 — Rollout Checklist & Onboarding Playbook
## Smart Store Operations

---

## 1. Phased Rollout Plan

### Week 21 — Shadow Mode (Pilot: 2 Stores)

| Task | Description | Owner | Status |
|------|-------------|-------|--------|
| Select pilot stores | Choose 2 stores with best infrastructure readiness scores | PM | ☐ |
| Deploy all edge services | CV inference, queue tracking, LP analytics running | DevOps | ☐ |
| Shadow mode config | Alerts generated but NOT sent to staff; logged for analysis | ML Eng | ☐ |
| Parallel manual audits | Continue existing manual processes alongside | Store Mgr | ☐ |
| Dashboard access | Manager dashboard live for observation only | Frontend | ☐ |
| Monitoring setup | Grafana dashboards active, PagerDuty alerts for system health | DevOps | ☐ |

### Week 22 — KPI Comparison

| Metric | Pilot Stores | Control Stores | Pass Criteria |
|--------|-------------|----------------|---------------|
| mAP@0.5 (shelf detection) | Measured | N/A | ≥ 0.92 |
| False positive rate (LP) | Measured | N/A | ≤ 5% |
| Stockout rate | Measured | Measured | Pilot ≤ Control − 10% |
| Queue wait time | Measured | Measured | Pilot ≤ Control − 15% |
| System uptime | Measured | N/A | ≥ 99.5% |
| Staff feedback score | Survey | Survey | ≥ 3.5/5 |

**Go/No-Go Decision:** All criteria must pass. Steering committee sign-off required.

### Week 22–23 — Graduated Rollout

| Week | Stores | Mode |
|------|--------|------|
| 22 | STORE-001, STORE-002 | Live (alerts active) |
| 23 | STORE-003, STORE-004, STORE-005 | Live |
| 24 | STORE-006, STORE-007, STORE-008 | Live |

### Go-Live Checklist (per store)

- [ ] All edge nodes online and healthy (3× Jetson Orin NX per store)
- [ ] All cameras streaming and CV inference running (≤80ms/frame)
- [ ] All shelf sensors reporting (weight + RFID)
- [ ] MQTT broker operational, all topics publishing
- [ ] Offline buffer tested (disconnect WAN for 1 hour, verify sync-on-reconnect)
- [ ] Manager dashboard accessible and showing live data
- [ ] Staff handheld app installed on all devices
- [ ] Staff training completed (≥80% attendance)
- [ ] Alert routing configured (manager + LP officer notifications)
- [ ] WMS integration verified (restock tasks flowing)
- [ ] POS integration verified (RFID reconciliation working)
- [ ] Grafana monitoring dashboards live
- [ ] Incident runbook distributed to store manager + IT
- [ ] Emergency rollback procedure documented and tested

---

## 2. Full Automation Rules

### Restock Automation

| Confidence Level | Action | Human Review |
|-----------------|--------|-------------|
| ≥ 95% | Auto-dispatch RestockTask to WMS | No (audited post-facto) |
| 70–94% | Create task, require human approval | Yes (manager approves in app) |
| < 70% | Log only, no task created | N/A |

### Model Promotion Rules

| Condition | Action |
|-----------|--------|
| mAP drops below 0.88 (7-day rolling) | Trigger retraining pipeline |
| New SKUs > 5% of planogram | Trigger retraining pipeline |
| Retraining complete + regression tests pass | Auto-promote to staging |
| Staging validation passes (24h) | Auto-promote to production (OTA) |
| A/B test winner (p < 0.05, 2+ weeks) | Auto-promote winner to all stores |

### Alert Escalation Rules

| Condition | Action |
|-----------|--------|
| LP alert unacknowledged > 5 min | Escalate to store manager |
| LP alert unacknowledged > 15 min | Escalate to regional LP |
| Queue wait > 6 min, all lanes open | Alert regional operations |
| Edge node offline > 10 min | PagerDuty alert to IT |
| Edge node offline > 1 hour | Dispatch field technician |

---

## 3. New Store Onboarding Playbook

### Target: Onboard in ≤ 3 weeks

#### Week 1 — Site Preparation

| Day | Task | Owner |
|-----|------|-------|
| 1 | Site survey using Phase 1 checklist | Field Engineer |
| 1 | Network assessment and PoE switch installation | IT |
| 2 | Ceiling mounting for cameras (20 positions) | Installation |
| 2 | Shelf sensor installation (48 sensors) | Installation |
| 3 | RFID antenna installation (24 antennas) | Installation |
| 3 | EAS gate installation at exit | Installation |
| 4 | Cabling completion and cable management | Installation |
| 4 | PoE switch configuration, VLAN setup | IT |
| 5 | Edge node rack mounting (3× Jetson Orin NX) | IT |
| 5 | UPS installation and power testing | Electrical |

#### Week 2 — Configuration & Calibration

| Day | Task | Owner |
|-----|------|-------|
| 6 | Edge node provisioning (run Ansible playbook) | DevOps |
| 6 | MQTT broker configuration | DevOps |
| 7 | Camera focusing and positioning fine-tuning | Field Engineer |
| 7 | Weight sensor calibration (tare all shelves) | Field Engineer |
| 8 | RFID reader power tuning and tag read verification | RF Engineer |
| 8 | EAS gate sensitivity calibration | LP Tech |
| 9 | Store-specific SKU data import | Data Team |
| 9 | Planogram golden images capture (all aisles) | CV Engineer |
| 10 | SKU-specific model fine-tuning (transfer learning, 2-hour training) | ML Engineer |

#### Week 3 — Testing & Training

| Day | Task | Owner |
|-----|------|-------|
| 11 | Model deployment to edge nodes (OTA) | DevOps |
| 11 | End-to-end integration testing | QA |
| 12 | Shadow mode activation (48 hours) | DevOps |
| 12 | Staff training session 1: Floor staff + barcode app | Trainer |
| 13 | Staff training session 2: Manager dashboard | Trainer |
| 13 | Staff training session 3: LP officers + alert handling | Trainer |
| 14 | Shadow mode analysis + calibration adjustments | ML Engineer |
| 14 | Go/No-Go review meeting | PM + Store Mgr |
| 15 | **GO-LIVE** 🚀 | All |

### Post-Onboarding (Week 4)

- [ ] Daily health check for first 5 days
- [ ] KPI comparison vs baseline (from site survey)
- [ ] Staff feedback survey
- [ ] Model performance review (mAP, false positive rate)
- [ ] Handover to BAU support team

---

## 4. Cost Optimization

### Cloud Cost Reduction Targets: 30%

| Strategy | Savings Est. |
|----------|-------------|
| **Spot instances for ML training** — Use EKS Spot node group for batch training jobs | 60–70% on GPU compute |
| **S3 Glacier archival** — Move data >90 days from TimescaleDB to S3 Glacier | 80% on storage |
| **Reserved instances** — 1-year RI for EKS general nodes, RDS, ElastiCache | 30–40% on always-on compute |
| **Right-sizing** — Monitor actual CPU/memory usage, downsize over-provisioned nodes | 10–20% |
| **Edge-first processing** — Minimize cloud data transfer by processing at edge | Reduces Kinesis + bandwidth costs |
| **Continuous aggregate caching** — TimescaleDB continuous aggregates reduce query compute | Reduces Athena query costs |

### Monitoring

- Monthly cost review via AWS Cost Explorer
- Budget alerts at 80% threshold
- Quarterly optimization review

---

*Document Control: v1.0 | Classification: Internal | Review: Before each store onboarding*
