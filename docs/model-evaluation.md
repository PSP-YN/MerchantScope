# TRACE synthetic benchmark — 11 November 2026

## Result

The CI benchmark generated 100 synthetic merchants (20 in each supported category), including 40 labelled suspicious-drift scenarios and 60 normal or legitimate-change merchants. The first 60 days are used for merchant baselines; the latest 30 days are evaluated.

| Metric | Static threshold | TRACE contextual |
|---|---:|---:|
| Precision | 1.0000 | 1.0000 |
| Recall | 0.5500 | 1.0000 |
| F1 | 0.7097 | 1.0000 |
| False-positive rate | 0.0000 | 0.0000 |
| Legitimate-merchant false-positive rate | 0.0000 | 0.0000 |

TRACE detected 40/40 labelled synthetic scenarios. Mean measured detection delay was 1.65 days (median 1 day). The per-category TRACE F1 was 1.0 in the generated benchmark for bakery, clothing, electronics, grocery and restaurant merchants.

## Interpretation and limitations

These results describe this deterministic synthetic benchmark only. They are not a claim about PayU data, real fraud prevalence, live payment traffic, or production performance. Synthetic scenario labels are not ground truth for real-world criminal activity. The Isolation Forest score is not calibrated as a probability. Detection delay is measured against generated scenario onset and a 3-day rolling statistical/shared-entity trigger. A real pilot requires authorized provider data, independent validation, representative temporal holdouts, drift monitoring and human adjudication.

The full machine-readable report is in `evaluation/reports/synthetic-benchmark-2026-11-11.json`. Re-run it with `python run.py` from the `evaluation` directory; CI also uploads the latest report as a workflow artifact.
