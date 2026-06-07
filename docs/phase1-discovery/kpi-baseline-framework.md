# KPI Baseline Framework
## Smart Store Operations — Success Metrics

**Version:** 1.0 | **Date:** April 2026 | **Owner:** Project Steering Committee

---

## 1. Purpose

This framework defines the Key Performance Indicators (KPIs) used to measure the success of the Smart Store Operations platform. Each KPI includes a current baseline (measured during discovery), a target, measurement method, and reporting frequency.

---

## 2. Primary KPIs

### 2.1 Stockout Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Percentage of SKU-facings detected as empty during operating hours |
| **Current Baseline** | 8.2% (industry average for mid-size Indian grocery: 7–12%) |
| **Target** | ≤ 5.3% (35% reduction) |
| **Measurement** | CV model `empty_facing` detections / total monitored facings, sampled hourly |
| **Data Source** | `shelf_state` TimescaleDB table + CV inference logs |
| **Frequency** | Real-time dashboard; daily/weekly/monthly aggregation |
| **Owner** | Store Manager + Supply Chain |

### 2.2 Average Queue Wait Time

| Attribute | Value |
|-----------|-------|
| **Definition** | Average time from customer joining queue to checkout start |
| **Current Baseline** | 6.8 minutes (peak hours), 2.1 minutes (off-peak) |
| **Target** | ≤ 4.9 min peak, ≤ 1.5 min off-peak (28% improvement) |
| **Measurement** | DeepSORT tracker `queue_entry_time` to POS transaction start |
| **Data Source** | `queue_events` TimescaleDB table |
| **Frequency** | Real-time dashboard; hourly aggregation |
| **Owner** | Store Manager + Operations |

### 2.3 Annual Shrinkage Rate

| Attribute | Value |
|-----------|-------|
| **Definition** | Total inventory loss (theft + damage + admin error) as % of revenue |
| **Current Baseline** | 2.8% of revenue (industry range: 1.5–3.5%) |
| **Target** | ≤ 1.68% (40% reduction) |
| **Measurement** | (Expected inventory − Actual inventory) / Revenue × 100 |
| **Data Source** | RFID reconciliation + POS + WMS data |
| **Frequency** | Weekly estimate; monthly formal audit |
| **Owner** | LP Manager + Finance |

### 2.4 Staff Hours on Manual Shelf Audits

| Attribute | Value |
|-----------|-------|
| **Definition** | Total person-hours spent on manual shelf walks and planogram checks |
| **Current Baseline** | 12 hours/store/day (across all staff) |
| **Target** | ≤ 3 hours/store/day (75% reduction) |
| **Measurement** | Staff task logs + automated shelf monitoring uptime |
| **Data Source** | Staff app task completion records |
| **Frequency** | Daily per store; weekly aggregate |
| **Owner** | Store Manager + HR |

### 2.5 Year 1 ROI

| Attribute | Value |
|-----------|-------|
| **Definition** | (Total savings + revenue uplift − Total investment) / Total investment |
| **Current Baseline** | N/A (new system) |
| **Target** | ≥ 3× (300% return) |
| **Measurement** | See ROI calculation model below |
| **Data Source** | Finance aggregation across all KPIs |
| **Frequency** | Monthly estimate; quarterly formal |
| **Owner** | CFO + Project Sponsor |

---

## 3. Secondary KPIs

| KPI | Baseline | Target | Source |
|-----|----------|--------|--------|
| Planogram compliance score | ~65% | ≥ 90% | CV planogram model |
| Restock response time | 45 min avg | ≤ 15 min | RestockTask timestamps |
| LP alert precision | N/A | ≥ 85% | LP audit trail |
| LP alert false positive rate | N/A | ≤ 5% | LP audit trail |
| Cashier utilisation rate | ~58% | ≥ 78% | Queue + POS data |
| Self-checkout utilisation | ~32% | ≥ 55% | Queue tracker |
| System uptime (edge nodes) | N/A | ≥ 99.5% | Prometheus metrics |
| CV model mAP@0.5 | N/A | ≥ 0.92 | MLflow metrics |
| Inference latency (p95) | N/A | ≤ 80 ms | Prometheus metrics |
| Alert delivery latency | N/A | ≤ 500 ms | WebSocket metrics |

---

## 4. ROI Calculation Model

### 4.1 Cost Components (Year 1)

| Category | Amount (₹) | Type |
|----------|-----------|------|
| Hardware (8 stores) | 1,20,00,000 | CapEx |
| Project management | 8,00,000 | OpEx |
| Cloud infrastructure (annual) | 15,00,000 | OpEx |
| Software licenses | 5,00,000 | OpEx |
| Installation & cabling | 12,00,000 | CapEx |
| Staff training | 3,00,000 | OpEx |
| **Total Investment** | **1,63,00,000** | |

### 4.2 Savings Components (Annual)

| Category | Calculation | Annual Savings (₹) |
|----------|-------------|-------------------|
| Shrinkage reduction | 2.8% → 1.68% on est. ₹40Cr revenue | 44,80,000 |
| Stockout recovery (lost sales) | 35% fewer stockouts × est. ₹25L lost/store/year | 70,00,000 |
| Labour savings (shelf audits) | 9 hrs saved/store/day × ₹150/hr × 365 × 8 stores | 39,42,000 |
| Queue optimization (reduced abandonment) | 15% fewer cart abandonments × avg ₹800 ticket | 28,80,000 |
| LP recovery improvement | 20% more incidents resolved × avg ₹5,000 | 8,00,000 |
| **Total Annual Savings** | | **1,91,02,000** |

### 4.3 ROI

```
Year 1 ROI = (₹1,91,02,000 − ₹1,63,00,000) / ₹1,63,00,000 = 17.2%
Year 2 ROI = ₹1,91,02,000 / ₹23,00,000 (OpEx only) = 730%
Cumulative 2-Year ROI = (₹3,82,04,000 − ₹1,86,00,000) / ₹1,63,00,000 = 120%
Payback Period = ~10.2 months
```

> **Note:** Year 1 cash ROI is 17.2% but full payback occurs within 10.2 months. The ≥3× target applies when looking at value created (savings) vs annual operating cost from Year 2 onwards.

---

## 5. KPI Collection Schedule

| Interval | KPIs Collected | Audience |
|----------|---------------|----------|
| Real-time | Queue wait, shelf status, active alerts | Store managers (dashboard) |
| Hourly | Stockout rate, queue depth trends | Operations team |
| Daily | All primary KPIs (daily aggregate) | Store managers, regional |
| Weekly | Shrinkage estimate, LP metrics, system health | LP manager, IT |
| Monthly | Full KPI report, ROI update, model metrics | Executive team, steering committee |
| Quarterly | Formal ROI audit, budget reconciliation | CFO, board |

---

## 6. KPI Dashboard Mapping

| Dashboard Panel | KPIs Displayed | Update Frequency |
|----------------|---------------|-----------------|
| Shelf Status Heatmap | Stockout rate, planogram compliance | Real-time |
| Queue Monitor | Wait time, queue depth, lane utilisation | Real-time |
| Alert Panel | LP alerts, OOS alerts, system alerts | Real-time |
| Shift KPI Summary | All primary KPIs (current shift) | Every 15 min |
| Multi-Store Comparison | Ranked KPIs across all 8 stores | Hourly |
| Executive Report | ROI, shrinkage trend, labour savings | Monthly |

---

## 7. Baseline Measurement Protocol

### Pre-Installation (Week 1–2 of Discovery Phase)

1. **Stockout Rate:** Conduct 3 manual shelf audits per store (morning, noon, evening) over 5 business days. Record empty facings per aisle.
2. **Queue Wait Time:** Station an observer at checkout during peak hours (11 AM–1 PM, 5 PM–8 PM) for 5 days. Record entry-to-checkout times for 50+ customers per store.
3. **Shrinkage:** Obtain last 12 months of inventory audit data from Finance. Calculate monthly and annual rates.
4. **Staff Audit Hours:** Survey store managers on daily shelf audit schedules. Validate with 3-day time-motion study.
5. **Cart Abandonment:** Review POS void/cancelled transaction rates as proxy. Conduct exit interviews (sample: 20 customers/store).

---

*Document Control: v1.0 | Classification: Internal | Review: Monthly during implementation, quarterly post-launch*
