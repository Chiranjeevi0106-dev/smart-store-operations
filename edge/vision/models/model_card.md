# Model Card — YOLOv9-m Shelf Detection
## Smart Store Operations — Phase 4

---

## Model Details

| Attribute | Value |
|-----------|-------|
| **Model Name** | smartstore-shelf-yolov9m |
| **Architecture** | YOLOv9-m (modified) |
| **Version** | 1.0.0 |
| **Task** | Object detection (shelf facing classification) |
| **Input** | RGB image, 640×640 pixels |
| **Output** | Bounding boxes + class labels + confidence scores |
| **Model Size** | ~98 MB (TensorRT INT8) |
| **Inference Target** | ≤ 80 ms on NVIDIA Jetson Orin NX 8GB |
| **Framework** | PyTorch → Ultralytics → TensorRT INT8 |
| **License** | Proprietary (internal use only) |

---

## Classes

| Class ID | Label | Description |
|----------|-------|-------------|
| 0 | `product_present` | Product correctly placed on shelf |
| 1 | `empty_facing` | Empty shelf position (out of stock) |
| 2 | `wrong_product` | Incorrect product in this position |
| 3 | `partial_facing` | Product partially depleted or fallen |

---

## Training Data

| Parameter | Value |
|-----------|-------|
| Total images | ~40,000 (10,000 per category) |
| Train / Val / Test | 70% / 15% / 15% |
| Annotation format | YOLO (bounding box, class) |
| Annotation tool | Label Studio |
| Augmentation | ±15° rotation, ±30% brightness, horizontal flip, mosaic, mixup, HSV jitter |
| Data version | DVC v1.0 (`dvc://shelf-dataset/v1.0`) |

---

## Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| mAP@0.5 | ≥ 0.92 | — (to be measured) |
| mAP@0.5:0.95 | ≥ 0.75 | — |
| Precision | ≥ 0.90 | — |
| Recall | ≥ 0.88 | — |
| Inference latency (p95) | ≤ 80 ms | — |
| Model size | ≤ 120 MB | ~98 MB ✓ |

---

## Intended Use

- **Primary:** Real-time shelf monitoring in grocery retail stores
- **Environment:** Indoor retail, overhead 4K cameras, 4m ceiling height
- **Users:** Automated system (edge inference server)
- **Decision impact:** Triggers OOS alerts and restock tasks

---

## Limitations & Risks

| Limitation | Mitigation |
|-----------|-----------|
| Performance degrades under unusual lighting (direct sunlight glare) | Data augmentation includes brightness/contrast variation |
| New SKUs not in training data may be misclassified | Continuous retraining pipeline (Phase 10), triggered when new SKUs > 5% |
| Reflective packaging can cause false detections | Include reflective product images in training set |
| Model is store-specific (planogram-dependent) | Transfer learning fine-tuning per store during onboarding |
| Adversarial examples possible (unlikely in retail) | Monitor false positive rate, alert on anomalous patterns |

---

## Ethical Considerations

- Model processes product images only — **no customer or staff faces are analyzed**
- All inference runs on-device — **no images transmitted to cloud**
- False positives may trigger unnecessary restock tasks (mitigated by sensor fusion requiring ≥85% confidence across 3 consecutive frames)
- No bias concerns — model classifies products, not people

---

## Monitoring & Retraining

| Trigger | Action |
|---------|--------|
| mAP drops below 0.88 (7-day rolling eval) | Auto-trigger retraining pipeline |
| New SKUs exceed 5% of planogram | Auto-trigger retraining |
| False positive rate exceeds 5% | Alert ML team, manual review |
| Inference latency p95 exceeds 100 ms | Investigate hardware/model issues |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | April 2026 | Initial release — YOLOv9-m fine-tuned on shelf dataset |

---

*Model Card follows Google Model Cards for Model Reporting (Mitchell et al., 2019)*
