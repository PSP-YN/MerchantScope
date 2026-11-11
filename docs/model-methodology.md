# Model methodology and evaluation

## Features
Baseline window: first 60 days. Evaluation window: most recent 30 days. Features include daily transaction count, average ticket, refund rate, failed-payment rate, late-hour share, and top-five pseudonymous customer concentration.

## Detection
- Rolling-window comparisons use merchant-specific baselines.
- Rule signals expose observed current values and baselines.
- Isolation Forest is fit on cross-merchant feature vectors with a fixed random seed; its decision function is an anomaly signal, not a fraud probability.
- NetworkX represents merchant-to-device/customer/settlement relationships. Shared identifiers are investigative leads, never proof.
- Structured context events are marked unverified by default. Context does not erase independent graph or payment signals.

## Score
Weights are behaviour 25%, category consistency 25%, graph 25%, payment anomalies 15%, unresolved context 10%. Missing behavioural history removes behaviour and payment dimensions from the denominator. Confidence is separate from severity.

## Evaluation
The evaluation script compares static thresholds with TRACE on deterministic scenario labels. The split is chronological: baseline data precedes current-window features. It reports precision, recall, F1, false-positive rate, legitimate merchant false-positive rate, and category F1. Detection delay is not estimated because adjudicated event-level timestamps are unavailable.

## Limitations
Synthetic scenarios are deliberately constructed and do not represent actual fraud base rates. Metrics must not be presented as real-world performance. Production calibration requires authorized representative data and independent validation.
