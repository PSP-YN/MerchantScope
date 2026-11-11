# Model methodology and evaluation

## Features
Baseline window: first 60 days. Evaluation window: most recent 30 days. Features include daily transaction count, average ticket, refund rate, failed-payment rate, late-hour share, and top-five pseudonymous customer concentration.

## Detection
- Rolling-window comparisons use merchant-specific baselines.
- Rule signals expose observed current values and baselines.
- Isolation Forest is fit on cross-merchant historical baseline feature vectors (first 60 days) with a fixed random seed, then scores current-window features (latest 30 days). Its decision function is an anomaly signal, not a fraud probability.
- NetworkX represents merchant-to-device/customer/settlement relationships. Shared identifiers are investigative leads, never proof.
- Structured context events are marked unverified by default. Context does not erase independent graph or payment signals.

## Score
Default weights are behaviour 25%, category consistency 25%, graph 25%, payment anomalies 15%, unresolved context 10%. They can be overridden with TRACE_WEIGHT_BEHAVIOUR, TRACE_WEIGHT_CATEGORY, TRACE_WEIGHT_GRAPH, TRACE_WEIGHT_PAYMENT, and TRACE_WEIGHT_CONTEXT; restart the API after changing them. Missing behavioural history removes behaviour and payment dimensions from the denominator. Confidence is separate from severity.

## Evaluation
The evaluation script compares static thresholds with TRACE on deterministic scenario labels. The split is chronological: baseline data precedes current-window features. It reports precision, recall, F1, false-positive rate, legitimate merchant false-positive rate, and category F1. Detection delay is measured in the synthetic benchmark from the known scenario onset to the first 3-day rolling statistical trigger or shared-entity graph trigger. This is a synthetic event-to-signal measure, not a real payment-provider incident SLA.

## Limitations
Synthetic scenarios are deliberately constructed and do not represent actual fraud base rates. Metrics must not be presented as real-world performance. Production calibration requires authorized representative data and independent validation.
