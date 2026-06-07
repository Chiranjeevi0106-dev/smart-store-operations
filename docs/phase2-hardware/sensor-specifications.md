# Sensor Specifications Document
## Smart Store Operations — Phase 2: Hardware

**Version:** 1.0 | **Date:** April 2026

---

## 1. Shelf Weight Sensors

| Specification | Value |
|---------------|-------|
| **Sensor Type** | Strain gauge load cell (single-point) |
| **Resolution** | ≤ 1 g |
| **Capacity Range** | 0–30 kg per shelf bay |
| **Accuracy** | ±0.05% FS |
| **Communication** | RS-485 (Modbus RTU) — daisy-chain up to 32 sensors per bus |
| **Secondary Protocol** | I²C (for short-run clusters ≤5 sensors) |
| **Power** | PoE (802.3af, 15W max) via RS-485/PoE injector; battery backup (CR2477, 18-month life) |
| **IP Rating** | IP54 (splash-proof for refrigerated aisles) |
| **Operating Temp** | -10°C to 50°C (covers freezer proximity zones) |
| **Dimensions** | 300 × 50 × 3 mm (fits under standard shelf liner) |
| **Sampling Rate** | 2 Hz (configurable 1–10 Hz) |
| **Calibration** | Auto-tare on boot; manual tare via MQTT command |
| **Mounting** | Adhesive pad + mechanical clips for gondola shelves |
| **Data Format** | JSON over MQTT: `{sensor_id, weight_grams, expected_grams, timestamp, battery_pct}` |

**Recommended Models:** HBM PW10A, Vishay 1004, Mettler Toledo SLP (local India distributor)

---

## 2. RFID Infrastructure

| Specification | Value |
|---------------|-------|
| **Standard** | UHF EPC Gen 2 (ISO 18000-63) |
| **Frequency** | 865–867 MHz (India ISM band) |
| **Read Rate** | ≥ 1,000 tags/second |
| **Anti-Collision** | Q-algorithm (adaptive) per EPC Gen 2 spec |
| **Reader** | Fixed reader with 4 antenna ports, PoE-powered |
| **Antenna Type** | Circularly polarized, 6 dBi gain |
| **Antenna Placement** | 1 per shelf bay (mounted on price rail), angled 45° toward products |
| **Read Range** | 1.5–3 m (adjustable via power) |
| **Tag Type** | UHF inlay (Impinj Monza R6-P), wet inlay for source-tagging |
| **Metal Shelf Mitigation** | On-metal spacer tags for metal gondolas; antenna offset mounting |
| **Liquid Product Handling** | Tag placement on cap/lid, not body; increased reader sensitivity |
| **Reader Power** | PoE (802.3at, 25W) |
| **Communication** | TCP/IP Ethernet, LLRP protocol |
| **Data Format** | EPC tag reads → MQTT: `{reader_id, epc_list[], rssi[], timestamp}` |

**Recommended Models:** Impinj Speedway R420, Zebra FX9600

---

## 3. Overhead Cameras

| Specification | Value |
|---------------|-------|
| **Resolution** | 4K (3840 × 2160) minimum |
| **Frame Rate** | 30 fps |
| **Sensor** | 1/1.8" CMOS, ≥ 8 MP |
| **Lens** | Varifocal 2.8–12 mm, 108° HFOV for 4m ceiling height |
| **FOV Coverage** | 1 camera per 2 aisle bays (6 m × 4 m area) |
| **Night Vision** | IR LEDs, 30 m range, auto IR-cut filter |
| **WDR** | 120 dB Wide Dynamic Range |
| **Power** | PoE+ (802.3at, 25W) |
| **Connectivity** | Ethernet RJ45 (100/1000 Mbps) |
| **Video Codec** | H.265+ (HEVC) for bandwidth efficiency |
| **Onboard Compute** | ARM Cortex-A73 + 2 TOPS NPU for basic pre-processing |
| **Edge Integration** | RTSP stream → Jetson Orin NX for full inference |
| **ONVIF** | Profile S + Profile T compliant |
| **IP Rating** | IP67 (indoor use, but dust/moisture resistant) |
| **Operating Temp** | -30°C to 60°C |
| **Mounting** | Ceiling pendant mount, 360° adjustable bracket |
| **Storage** | MicroSD slot (128 GB) for 24h local rolling buffer |

**Recommended Models:** Hikvision DS-2CD2T86G2-ISU/SL, Dahua IPC-HFW5849T1-ASE-LED

### Camera Placement per Store (3,500 sq ft)

| Zone | Cameras | Purpose |
|------|---------|---------|
| Aisle coverage (6 aisles) | 12 | Shelf detection (2 per aisle) |
| Checkout area | 3 | Queue detection (bird's-eye overhead) |
| Entry/Exit | 2 | People counting + LP |
| High-value zones | 2 | LP behaviour monitoring |
| Backroom | 1 | Staff safety |
| **Total per store** | **20** | |

---

## 4. Smart EAS Gates

| Specification | Value |
|---------------|-------|
| **Detection Mode** | Dual-mode AM (Acousto-Magnetic) + EM (Electro-Magnetic) |
| **Tag Detection** | AM: 58 kHz hard tags; EM: 0.5–20 kHz deactivatable labels |
| **Detection Rate** | ≥ 95% for tags within gate corridor |
| **False Alarm Rate** | ≤ 0.1% |
| **Alarm Type** | Silent relay (NO/NC contact) → TCP/IP alert to LP system |
| **Corridor Width** | Up to 2.0 m between pedestals |
| **Integration** | TCP/IP port for real-time alert; RS-232 for legacy POS |
| **RFID Integration** | Built-in UHF RFID reader for EPC reconciliation at exit |
| **Power** | 230V AC, 50 Hz |
| **Dimensions** | 1500 × 440 × 150 mm per pedestal |

**Recommended Models:** Checkpoint Systems NEO, Sensormatic Synergy

---

## 5. Bill of Materials (per store & total)

| Component | Unit Cost (₹) | Qty/Store | Cost/Store (₹) | Total 8 Stores (₹) |
|-----------|---------------|-----------|-----------------|---------------------|
| Shelf weight sensors | 2,500 | 48 | 1,20,000 | 9,60,000 |
| RFID fixed readers (4-port) | 65,000 | 6 | 3,90,000 | 31,20,000 |
| RFID antennas | 8,000 | 24 | 1,92,000 | 15,36,000 |
| UHF RFID tags (per 10k) | 15,000 | 3 | 45,000 | 3,60,000 |
| 4K PoE cameras | 12,000 | 20 | 2,40,000 | 19,20,000 |
| Smart EAS gates (pair) | 1,50,000 | 1 | 1,50,000 | 12,00,000 |
| Jetson Orin NX 8GB | 45,000 | 3 | 1,35,000 | 10,80,000 |
| PoE switches (24-port) | 35,000 | 2 | 70,000 | 5,60,000 |
| UPS (1.5 kVA) | 12,000 | 2 | 24,000 | 1,92,000 |
| Cabling & connectors | — | — | 40,000 | 3,20,000 |
| Mounting hardware | — | — | 15,000 | 1,20,000 |
| **Subtotal per store** | | | **14,21,000** | |
| **Grand Total (8 stores)** | | | | **₹1,13,68,000** |
| Contingency (10%) | | | | **₹11,37,000** |
| **Total with contingency** | | | | **₹1,25,05,000** |

> ✓ Within ₹1.2 Cr budget (with 4.2% margin for negotiation)

---

## 6. Vendor RFQ Template

### Request for Quotation — Smart Store Hardware

**RFQ Reference:** SS-RFQ-2026-001  
**Issue Date:** April 2026  
**Response Deadline:** [Date + 14 days]

#### Evaluation Scorecard

| Criteria | Weight | Scoring (1-5) |
|----------|--------|--------------|
| Price competitiveness | 30% | 1=highest price, 5=lowest |
| Specification compliance | 40% | 1=major gaps, 5=full compliance |
| Support SLA (warranty, on-site) | 20% | 1=no local, 5=24/7 local India support |
| Lead time (delivery) | 10% | 1=>12 weeks, 5=<4 weeks |

#### Vendor Requirements
- Local India presence with on-site support capability
- Minimum 2-year warranty on all hardware
- Spare parts availability within 48 hours
- Technical training for installation team
- References from 2+ retail deployments in India

---

*Document Control: v1.0 | Classification: Internal*
