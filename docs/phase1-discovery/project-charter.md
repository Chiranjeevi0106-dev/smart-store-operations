# Project Charter — Smart Store Operations Platform

| Field | Value |
|-------|-------|
| **Project Name** | Smart Store Operations — Sensor & CV Platform |
| **Sponsor** | Chief Operating Officer |
| **Project Manager** | TBD |
| **Date** | April 2026 |
| **Version** | 1.0 |

## Objectives
Deploy an integrated IoT + Computer Vision platform across 8 grocery stores to automate shelf monitoring, queue management, and loss prevention — reducing stockouts by 35%, checkout wait times by 28%, and shrinkage by 40%, achieving ≥3× ROI in Year 1.

## Scope

### In Scope
- Shelf weight sensors, RFID, overhead 4K cameras, smart EAS gates across 8 stores
- Edge compute (Jetson Orin NX) for on-device CV inference
- YOLOv9 shelf detection, RT-DETR queue detection, MediaPipe behaviour analytics
- Kafka-based sensor fusion and LSTM restock prediction engine
- Cloud platform on AWS (EKS, S3, TimescaleDB, MLflow)
- React manager dashboard, staff PWA, digital signage integration
- Automated retraining, A/B testing, executive reporting pipelines

### Out of Scope
- Fresh produce quality detection (Phase 2 roadmap)
- Customer mobile app (loyalty, in-store navigation)
- Robotic restocking or automated shelf systems
- Integration with external law enforcement systems

## Stakeholders
| Role | Name | Responsibility |
|------|------|---------------|
| Executive Sponsor | COO | Budget approval, strategic direction |
| Project Manager | TBD | Day-to-day execution |
| Store Managers (×8) | Various | Requirements input, UAT, adoption |
| LP Manager | TBD | LP module requirements, alert validation |
| IT Manager | TBD | Infrastructure, network, integration |
| CFO | TBD | Budget tracking, ROI validation |

## Timeline Summary
| Phase | Duration | Weeks |
|-------|----------|-------|
| 1. Discovery & Requirements | 2 weeks | W1–W2 |
| 2. Hardware Procurement | 3 weeks | W3–W5 |
| 3. Network & Edge Infra | 2 weeks | W5–W7 |
| 4. CV Pipeline | 4 weeks | W7–W11 |
| 5. Sensor Fusion | 3 weeks | W10–W13 |
| 6. Queue Management | 3 weeks | W11–W14 |
| 7. Loss Prevention | 3 weeks | W13–W16 |
| 8. Cloud Platform | 4 weeks | W8–W16 |
| 9. Dashboard & Apps | 4 weeks | W14–W18 |
| 10. Scale & Launch | 4 weeks | W18–W24 |

**Total:** 24 weeks (6 months)

## Budget
| Category | Amount (₹) |
|----------|-----------|
| Project Management | 8,00,000 |
| Hardware (8 stores) | 1,20,00,000 |
| Cloud Infrastructure (Year 1) | 15,00,000 |
| Software & Licenses | 5,00,000 |
| Installation | 12,00,000 |
| Training | 3,00,000 |
| Contingency (10%) | 16,30,000 |
| **Total** | **₹1,79,30,000** |

## Success Criteria
1. Stockout rate ≤ 5.3% (from 8.2% baseline)
2. Avg queue wait ≤ 4.9 min peak (from 6.8 min)
3. Shrinkage ≤ 1.68% of revenue (from 2.8%)
4. System uptime ≥ 99.5%
5. CV model mAP@0.5 ≥ 0.92
6. Year 1 ROI ≥ 3× operating cost

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Executive Sponsor | | | |
| Project Manager | | | |
| IT Manager | | | |
| Finance (CFO) | | | |

*Approval of this charter authorizes the project to proceed to Phase 2.*
