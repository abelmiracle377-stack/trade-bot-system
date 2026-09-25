# Outcome-Driven Learning

The trading agent now has an additive feedback-learning layer. It does not
replace the primary market model, bypass risk controls, or change broker
permissions.

## Loop

1. The normal model generates a probability.
2. A non-zero signal is recorded before execution.
3. After the configured forward horizon has elapsed, the signal is resolved
   against later market data.
4. Resolved outcomes are kept in append-only JSONL storage.
5. Once enough outcomes exist, a logistic calibration model is trained on the
   historical predictions.
6. The candidate is evaluated on later, chronologically held-out outcomes.
7. It is promoted only when its Brier score is no worse than the base
   probability and its held-out accuracy is not materially worse.
8. A promoted calibrator makes a conservative 25% blend adjustment to future
   probabilities.

The primary XGBoost/random-forest/logistic model and all existing risk checks
remain unchanged.

## Persistence

The default state lives under data/runtime/learning/:
- signal_outcomes.jsonl — prediction/outcome event stream
- probability_calibrator.joblib — promoted feedback calibrator

The GitHub Actions paper-trading workflow caches this directory between
scheduled runs. The cache contains no broker credentials. GitHub documents that
cache keys are immutable, so the workflow uses a new run-specific key and a
restore prefix to recover the newest state.

If the learning state is unavailable, the agent starts safely with no feedback
calibrator and continues using the existing base model.

## Safety

- No look-ahead is used to resolve a signal before its forward horizon.
- Feedback is trained chronologically rather than with a random split.
- Promotion requires unseen-outcome validation.
- Risk limits remain the final gate before orders.
- Live trading remains explicitly disabled by default.
