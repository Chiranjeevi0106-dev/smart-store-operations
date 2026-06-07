# Stakeholder Interview Guide
## Smart Store Operations Platform

**Version:** 1.0  
**Date:** April 2026  
**Prepared by:** Project Discovery Team  
**Sprint:** 1 of 2 (Discovery Phase)

---

## 1. Interview Logistics

| Parameter | Value |
|-----------|-------|
| Duration | 45–60 minutes per session |
| Format | In-person preferred; video call acceptable |
| Recording | With consent; transcribed for analysis |
| Participants | 1 interviewer + 1 note-taker per session |
| Follow-up | Written summary shared within 48 hours |

---

## 2. Store Manager Interview (30 Questions)

### 2.1 Daily Operations & Pain Points

1. Walk us through a typical day from store opening to closing. Where do you lose the most time?
2. How do you currently detect out-of-stock items on the shelf? What is your average response time?
3. How many staff hours per week are spent on manual shelf audits and planogram compliance checks?
4. What is your current process for restocking? How is priority determined?
5. How often do customers complain about product unavailability? Do you track lost sales?
6. What are your peak hours, and how does shelf depletion vary throughout the day?

### 2.2 Queue & Checkout Experience

7. What is the average customer wait time during peak hours? How do you measure this today?
8. How do you decide when to open or close checkout lanes?
9. What percentage of customers abandon their cart due to long queues?
10. Do you have self-checkout? If so, what is the utilisation rate?
11. How do you handle sudden customer surges (festive days, promotions)?

### 2.3 Shrinkage & Loss Prevention

12. What is your current estimated shrinkage rate as a percentage of revenue?
13. What loss prevention measures are currently in place (CCTV, guards, EAS)?
14. How often do you review CCTV footage? Is it proactive or only after incidents?
15. What are the most commonly stolen or lost item categories?
16. How do you handle internal (employee) vs external (customer) shrinkage?

### 2.4 Technology Readiness

17. Rate your comfort level with adopting new technology on a scale of 1–10. What concerns do you have?
18. What devices do your floor staff currently use (handheld scanners, smartphones)?
19. How reliable is your in-store WiFi? Are there known dead zones?
20. What software systems do you currently use for inventory management?

### 2.5 Success Criteria

21. If this system could solve one problem perfectly, what would it be?
22. What would a "successful" implementation look like to you after 6 months?
23. What are your biggest concerns about implementing this system?

---

## 3. Loss Prevention (LP) Manager Interview (20 Questions)

### 3.1 Current LP Operations

1. Describe your current loss prevention workflow from detection to resolution.
2. How many LP incidents are logged per week/month per store?
3. What is your average response time from alert to intervention?
4. What percentage of incidents result in recovery vs write-off?
5. How do you currently identify repeat offenders?

### 3.2 Technology & Tools

6. What EAS/anti-theft system is currently installed? What is the false alarm rate?
7. How many CCTV cameras per store? What is the coverage percentage?
8. Do you have any analytics on the CCTV footage (heatmaps, behaviour)?
9. What is the retention period for CCTV footage? Is it adequate for investigations?
10. Do you use any people-counting or traffic-analytics tools?

### 3.3 Behavioural Indicators

11. What suspicious behaviours do your LP officers look for?
12. Rank these in order of priority: concealment, ticket switching, sweethearting, refund fraud, organized retail crime.
13. Which store zones have the highest shrinkage?
14. Are there specific times of day or days of the week with elevated risk?

### 3.4 Privacy & Compliance

15. Are you familiar with the Digital Personal Data Protection (DPDP) Act 2023?
16. What is your current data retention policy for video and customer data?
17. What are your requirements for face anonymisation in shared footage?
18. How do you handle incidents involving minors?

### 3.5 Vision for Improvement

19. What capabilities would an ideal LP system provide that you don't have today?
20. What is an acceptable false positive rate for automated alerts? (Currently aiming ≤5%)

---

## 4. IT Infrastructure Manager Interview (20 Questions)

### 4.1 Current Infrastructure

1. Describe the network architecture at each store (switches, routers, ISP, uplink bandwidth).
2. What is the current WiFi standard and coverage map per store?
3. Do you have PoE switches installed? If yes, how many spare PoE ports per store?
4. What is the current server or compute infrastructure at the store level?
5. Describe the WAN connectivity between stores and head office.

### 4.2 Connectivity & Reliability

6. What is your average network uptime per store over the last 12 months?
7. Do you have 4G/LTE failover for WAN? If not, what is the typical downtime impact?
8. What is the latency between store and head office/cloud services?
9. How are firmware and software updates currently rolled out to in-store devices?
10. What is your current backup and disaster recovery strategy?

### 4.3 Security & Compliance

11. What network security measures are in place (firewalls, VPN, segmentation)?
12. Do you follow any specific security frameworks (ISO 27001, PCI-DSS)?
13. How are access credentials managed for in-store devices?
14. What is the policy for TLS/SSL certificates? Who manages rotation?
15. How is PII data handled in transit and at rest?

### 4.4 Integration Points

16. What POS system is in use (vendor, version, API availability)?
17. What WMS/ERP system is used for inventory management?
18. Are there existing APIs or data feeds for sales, inventory, or staffing data?
19. What monitoring and alerting tools are currently in place (Nagios, Zabbix, etc.)?
20. What is your capacity for supporting new IoT devices (bandwidth, DHCP, monitoring)?

---

## 5. Finance / CFO Interview (15 Questions)

### 5.1 Current Costs

1. What is the annual revenue per store and overall for the 8-store chain?
2. What is the current cost of shrinkage as a percentage of revenue?
3. What is the annual cost of manual shelf audits (labour hours × rate)?
4. What is the estimated cost of stockout-related lost sales per store per month?
5. What is the current spend on loss prevention (staff, technology, insurance)?

### 5.2 Investment Parameters

6. What is the approved budget for this project? (Current guidance: ₹8L project + ₹1.2 Cr hardware)
7. What ROI timeline is expected? (Target: Year 1 ROI ≥ 3×)
8. How do you measure ROI — revenue lift, cost reduction, or both?
9. Is there a preference for CapEx vs OpEx spending model?
10. What is the maximum acceptable payback period?

### 5.3 Risk Tolerance

11. What financial risk factors are you most concerned about for this project?
12. How do you currently quantify the cost of checkout queue delays (lost customers)?
13. What insurance implications does improved loss prevention have?
14. Are there any tax benefits or incentives for technology adoption we should factor in?
15. What financial KPIs should the executive dashboard display?

---

## 6. Interview Analysis Framework

### Scoring Matrix

After all interviews, score each response area on:

| Dimension | Scale | Weight |
|-----------|-------|--------|
| Pain Severity | 1–5 (5 = critical) | 30% |
| Current Workaround Effort | 1–5 (5 = very manual) | 25% |
| Technology Readiness | 1–5 (5 = highly ready) | 20% |
| Expected Impact | 1–5 (5 = transformative) | 25% |

### Priority Mapping

```
Pain Severity × Current Workaround Effort = Implementation Priority Score
Technology Readiness × Expected Impact = Adoption Likelihood Score
```

Plot all features on a 2×2 matrix (Priority vs Adoption Likelihood) to determine Phase 1 deployment features.

---

## 7. Post-Interview Actions

- [ ] Transcribe and share summaries with interviewees for validation
- [ ] Score all responses using the analysis framework
- [ ] Identify common themes across all stakeholder groups
- [ ] Map conflicts (e.g., finance wanting ROI fast vs IT needing infrastructure prep)
- [ ] Feed findings into KPI Baseline Framework and Risk Register
- [ ] Present consolidated findings to steering committee within 5 business days

---

*Document Control: v1.0 | Classification: Internal | Review Cycle: Before each interview round*
