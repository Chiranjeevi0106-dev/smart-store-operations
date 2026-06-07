# Site Survey Checklist
## Smart Store Operations — Per-Store Assessment

**Version:** 1.0  
**Date:** April 2026  
**Surveyor:** ________________  
**Store ID:** ________________  
**Store Name:** ________________  
**Survey Date:** ________________  
**Store Address:** ________________

---

## 1. Physical Layout & Dimensions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Total floor area (sq ft) | | Target: ~3,500 |
| Ceiling height (m) | | Min 3m for overhead cameras |
| Number of aisles | | |
| Average aisle width (m) | | Min 1.2m for camera FOV |
| Number of shelf bays (total) | | |
| Shelf levels per bay (avg) | | |
| Number of checkout lanes | | |
| Number of entry/exit points | | |
| Backroom/stockroom area (sq ft) | | |
| Loading dock: Yes / No | | |

### Floor Plan Sketch
*Attach a hand-drawn or CAD floor plan showing:*
- [ ] Aisle layout and numbering
- [ ] Checkout lane positions
- [ ] Entry/exit points
- [ ] Backroom access points
- [ ] Electrical panel locations
- [ ] Server room / IT closet location
- [ ] High-value fixture locations (spirits, electronics, cosmetics)

---

## 2. Ceiling & Mounting Assessment

| Parameter | Value | Notes |
|-----------|-------|-------|
| Ceiling type | Drop / Exposed / Concrete | |
| Ceiling load capacity (kg/m²) | | For camera mounts |
| Existing ceiling mounts | | Quantity and type |
| Conduit access above ceiling | Yes / No | For cable routing |
| HVAC vent locations conflicting | | Mark on floor plan |
| Lighting type | LED / Fluorescent / Mixed | Affects CV accuracy |
| Lighting uniformity (1–5) | | 5 = very uniform |
| Natural light sources | | Windows, skylights — cause glare |

---

## 3. WiFi & Network Infrastructure

### 3.1 Current WiFi

| Parameter | Value | Notes |
|-----------|-------|-------|
| WiFi standard | 802.11 ac / ax / n | |
| Number of access points | | |
| AP brand/model | | |
| Signal strength - Front of store (dBm) | | Measure w/ WiFi analyser |
| Signal strength - Centre aisles (dBm) | | Target: ≥ -65 dBm |
| Signal strength - Backroom (dBm) | | |
| Dead zones identified | | Mark on floor plan |
| 2.4 GHz channel congestion | Low / Medium / High | |
| 5 GHz channel availability | | |

### 3.2 Wired Network

| Parameter | Value | Notes |
|-----------|-------|-------|
| ISP provider | | |
| Uplink bandwidth (Mbps) | | Min 100 Mbps required |
| ISP SLA (uptime %) | | |
| Number of network switches | | |
| Switch brand/model | | |
| PoE capable switches | Yes / No | |
| PoE available ports | | For cameras + sensors |
| PoE budget available (W) | | Each camera ~15W |
| Existing VLAN configuration | | |
| Firewall in place | Yes / No | Brand/model: |
| 4G LTE backup | Yes / No | |
| 4G signal strength (bars) | | |
| Patch panel location | | |
| Cable runs possible (Y/N per zone) | | |

---

## 4. Existing CCTV System

| Parameter | Value | Notes |
|-----------|-------|-------|
| CCTV installed | Yes / No | |
| Number of cameras | | |
| Camera resolution | | |
| Camera brand/model | | |
| NVR brand/model | | |
| Storage capacity (TB) | | |
| Retention period (days) | | |
| PoE cameras | Yes / No | |
| Camera positions suitable for reuse | | Mark on floor plan |
| Camera positions needing relocation | | |
| Overhead (bird's-eye) cameras | Yes / No | Critical for queue detection |
| Analytics capability (built-in) | Yes / No | |
| ONVIF compatible | Yes / No | |

---

## 5. Shelf Fixture Assessment

### 5.1 Shelf Types

| Fixture Type | Quantity | Dimensions (H×W×D cm) | Material | Sensor Compatible |
|-------------|----------|----------------------|----------|-------------------|
| Standard gondola | | | Steel / Wood | |
| End-cap display | | | | |
| Refrigerated case | | | | Check IP rating |
| Freezer section | | | | Check temp range |
| Pegboard / hanging | | | | Different sensor needed |
| Bulk bin | | | | Weight sensor only |

### 5.2 Shelf Sensor Installation Feasibility

| Parameter | Value | Notes |
|-----------|-------|-------|
| Shelf surface: flat/textured | | Flat needed for weight sensors |
| Power outlet proximity per aisle | | For PoE injectors |
| Shelf depth tolerance for sensor | | Sensor: ~3 mm thick |
| Price tag rail type | | For RFID antenna mounting |
| Shelf dividers present | Yes / No | Affects camera FOV |
| Max weight per shelf (kg) | | Sensor must handle max + product |

---

## 6. RFID Readiness

| Parameter | Value | Notes |
|-----------|-------|-------|
| Existing RFID tagging | None / Partial / Full | |
| If partial: tagged categories | | |
| Tag type in use | | UHF EPC Gen 2 preferred |
| Source-level tagging by suppliers | Yes / No | |
| In-store tagging feasible | Yes / No | Staff capacity? |
| RFID reader infrastructure | None / Partial | |
| Metal shelf interference tested | Yes / No | UHF reflects off metal |
| Liquid product interference noted | Yes / No | UHF absorbed by water |
| High-value items (RFID priority) | | List categories |
| Estimated SKU count (total) | | |
| Estimated SKU count (high-value) | | |

---

## 7. POS System Assessment

| Parameter | Value | Notes |
|-----------|-------|-------|
| POS vendor | | |
| POS software version | | |
| Number of POS terminals | | |
| POS connectivity | Ethernet / WiFi | |
| POS API available | Yes / No | For transaction data |
| POS data export format | CSV / JSON / XML / API | |
| Barcode scanner type | 1D / 2D / Both | |
| Payment terminals | | Brand/model |
| Receipt printer type | | Thermal / Impact |
| SCO terminals | Yes / No | Quantity: |
| SCO vendor | | |
| Loyalty system integrated | Yes / No | |
| POS transaction logs accessible | Yes / No | For RFID reconciliation |

---

## 8. Electrical & Power

| Parameter | Value | Notes |
|-----------|-------|-------|
| Main power supply (V/Hz) | | 230V/50Hz standard |
| UPS installed | Yes / No | Capacity: |
| UPS runtime (min) | | Min 30 min for graceful shutdown |
| Spare circuit breaker slots | | |
| Power outlet density (per aisle) | | |
| Generator backup | Yes / No | |
| PoE power budget needed (W) | | Calculate: cameras + APs + sensors |
| Dedicated IT power circuit | Yes / No | |

---

## 9. Entry/Exit Points & EAS

| Parameter | Value | Notes |
|-----------|-------|-------|
| Number of customer entry points | | |
| Number of customer exit points | | |
| Entry width (m) | | For EAS gate sizing |
| Existing EAS system | None / AM / EM / RF | |
| EAS vendor/model | | |
| EAS false alarm rate (daily avg) | | |
| EAS gate power outlets nearby | Yes / No | |
| Network drops near gates | Yes / No | For smart EAS |
| Emergency exit points | | Mark on floor plan |
| Staff-only entrances | | |

---

## 10. Environmental Conditions

| Parameter | Value | Notes |
|-----------|-------|-------|
| Indoor temp range (°C) | | Edge nodes: 0–45°C |
| Humidity range (%) | | For electronics longevity |
| Dust level | Low / Medium / High | IP rating consideration |
| Vibration sources nearby | | Refrigerators, HVAC |
| Refrigerated aisles temp (°C) | | For sensor IP rating |
| Freezer section temp (°C) | | May need heated enclosures |

---

## 11. Survey Summary & Readiness Score

| Category | Score (1–5) | Critical Issues |
|----------|-------------|-----------------|
| Physical layout suitability | | |
| Network readiness | | |
| Power infrastructure | | |
| Shelf fixture compatibility | | |
| RFID readiness | | |
| CCTV upgrade feasibility | | |
| POS integration readiness | | |
| Environmental suitability | | |
| **Overall Readiness** | **/5** | |

### Required Pre-Installation Work

- [ ] _______________________________________________
- [ ] _______________________________________________
- [ ] _______________________________________________
- [ ] _______________________________________________
- [ ] _______________________________________________

### Estimated Pre-Installation Cost: ₹ _______________

### Photos Attached

- [ ] Front entrance (for EAS gate sizing)
- [ ] Each aisle (for camera placement)
- [ ] Ceiling close-up (for mounting assessment)
- [ ] IT closet / server room
- [ ] Electrical panel
- [ ] POS terminals
- [ ] Existing CCTV equipment
- [ ] Shelf fixtures (each type)
- [ ] Backroom / stockroom

---

**Surveyor Signature:** ________________ **Date:** ________________  
**Store Manager Acknowledged:** ________________ **Date:** ________________

---

*Document Control: v1.0 | Classification: Internal | One per store — 8 surveys required*
