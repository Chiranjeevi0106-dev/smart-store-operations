# Network & Edge Infrastructure
## Smart Store Operations — Phase 3

---

## 1. Edge Node Specification

### Selected: NVIDIA Jetson Orin NX 8GB

| Spec | Jetson Orin NX 8GB | Google Coral Dev Board | **Decision** |
|------|-------------------|----------------------|-------------|
| AI Performance | 70 TOPS (INT8) | 4 TOPS (INT8) | **Orin NX wins** — 17.5× more compute |
| GPU | 1024-core Ampere | None (Edge TPU only) | Orin NX handles multiple models |
| CPU | 6-core Arm Cortex-A78AE | 4-core Cortex-A53 | Orin NX 3× faster per-core |
| RAM | 8 GB LPDDR5 | 1 GB LPDDR4 | Orin NX handles larger models |
| Storage | NVMe SSD support | eMMC 8 GB | Orin NX better for video buffering |
| TensorRT | Full support (INT8) | Not supported | Critical for inference optimization |
| Multi-model | 3+ concurrent models | 1 model at a time | Orin NX runs shelf + queue + LP |
| Power | 10–25W | 2–3W | Acceptable with PoE |
| Price | ₹45,000 | ₹12,000 | Orin NX justified by capability |
| OS | JetPack 6 (Ubuntu) | Mendel Linux | Better ecosystem support |

**Justification:** Each store requires concurrent inference for 3 workloads:
1. YOLOv9 shelf detection (20 camera streams)
2. RT-DETR queue detection (3 camera streams)
3. MediaPipe pose + behaviour classification

The Coral Dev Board's 4 TOPS cannot handle this combined workload. The Orin NX's 70 TOPS provides comfortable headroom for all three models simultaneously, plus future model additions.

**Deployment: 3 nodes per store** (aisle zone, checkout zone, entrance zone).

---

## 2. Network Topology

### Per-Store Architecture

```
                    ┌─────────────────┐
                    │   ISP Uplink    │
                    │  100 Mbps min   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   4G LTE        │ ← Failover
                    │   Backup        │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Edge Router    │
                    │  + Firewall     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴──────┐ ┌────┴────┐ ┌──────┴───────┐
     │  PoE Switch 1 │ │PoE Sw 2 │ │  Mgmt Switch │
     │  (Cameras +   │ │(Sensors │ │  (POS + IT)  │
     │   Edge Nodes) │ │ + RFID) │ │              │
     │  VLAN 10      │ │ VLAN 20 │ │  VLAN 30     │
     └───────────────┘ └─────────┘ └──────────────┘
```

### VLAN Segmentation

| VLAN ID | Name | Purpose | Subnet |
|---------|------|---------|--------|
| 10 | Cameras | IP cameras + Jetson Orin NX nodes | 10.{store}.10.0/24 |
| 20 | Sensors | Weight sensors, RFID readers, EAS gates | 10.{store}.20.0/24 |
| 30 | POS/Mgmt | POS terminals, management access | 10.{store}.30.0/24 |
| 40 | Guest | Staff WiFi (isolated) | 10.{store}.40.0/24 |

### PoE Budget

| Device Type | Count | Power/Device | Total Power |
|-------------|-------|-------------|-------------|
| 4K PoE cameras | 20 | 15W | 300W |
| Jetson Orin NX | 3 | 25W | 75W |
| RFID readers | 6 | 25W | 150W |
| WiFi APs | 4 | 15W | 60W |
| **Total** | | | **585W** |

**Switch Spec:** 2× 24-port PoE+ switches, 370W PoE budget each (740W total, 21% headroom).

---

## 3. MQTT Topic Schema

```
stores/
  {store_id}/
    shelf/
      oos              QoS 2  — Out-of-stock alerts
      planogram        QoS 1  — Planogram compliance updates
      state            QoS 0  — Fused shelf state (high volume)
    queue/
      status           QoS 0  — Queue depth updates (every 5s)
      alert            QoS 2  — Queue threshold alerts
    lp/
      alert            QoS 2  — Loss prevention alerts
      behaviour        QoS 1  — Behaviour classification events
    sensor/
      weight           QoS 0  — Weight sensor telemetry (2 Hz)
      rfid             QoS 0  — RFID tag read events
    restock/
      task             QoS 2  — New restock tasks
      complete         QoS 1  — Task completion confirmations
    system/
      health           QoS 1  — Edge node health metrics
      heartbeat        QoS 0  — Heartbeat (retained message)
```

**Retained Messages:** Only `system/heartbeat` — allows new subscribers to immediately know node status.

---

## 4. Offline Resilience

### 24-Hour Local Buffer

**Storage:** SQLite database on each edge node (`/var/lib/smartstore/buffer/event_buffer.db`)

| Buffer Parameter | Value |
|-----------------|-------|
| Max buffer size | 2 GB |
| Events per hour (peak) | ~180,000 |
| 24-hour capacity | ~4.3M events (~1.5 GB) |
| Sync-on-reconnect | FIFO order, batch size 1,000 |
| Conflict resolution | Last-write-wins with server timestamp |
| Duplicate detection | Event ID + timestamp dedup at cloud ingest |

### Sync-on-Reconnect Strategy

1. Edge detects WAN reconnection via MQTT broker ping
2. Buffer reader queries unsynchronised events (ORDER BY created_at ASC)
3. Batch upload to Kafka/Kinesis in chunks of 1,000 events
4. Cloud ingest validates: dedup by event_id, reject if timestamp > 24h stale
5. Mark events as synced in local buffer
6. Purge synced events older than 48 hours

---

## 5. SLA Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Edge node uptime | ≥ 99.5% | Prometheus `up` metric |
| Alert latency (edge → dashboard) | ≤ 50 ms (local), ≤ 500 ms (cloud) | End-to-end timing |
| Sensor data lag | ≤ 2 seconds | Timestamp delta |
| Queue depth update interval | ≤ 5 seconds | Frame processing interval |
| RFID reconciliation latency | ≤ 8 seconds | EAS gate → alert time |
| Inference latency (p95) | ≤ 80 ms per frame | Prometheus histogram |
| Offline buffer sync time | ≤ 30 minutes for 24h backlog | Sync completion metric |
| API uptime (cloud) | ≥ 99.9% | Health check monitoring |

---

*Document Control: v1.0 | Classification: Internal*
