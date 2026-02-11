Page 1
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
 AI Paper Trading Agent
 Startup-Style Product Plan v7.2.1 (Institutional-grade Patch)
A compliance-first, research-grade paper trading platform that uses public market data only and executes
no real trades. This document is designed to be a reproducible portfolio artifact that survives technical
interview scrutiny.
v7.2.1 patch scope: (1) tightens SAFE_MODE exit staleness to a single conservative value, (2) makes
position sizing clip behavior explicitly logged and reported, and (3) keeps all other v7.2 specs unchanged
(no scope expansion).
0) Non-negotiables
•
Simulation-only: no brokerage integration, no live orders, no KYC/SSN required.
•
Strict causality: at decision time t, use only data timestamped <= t (Exchange Event Time).
•
No optimistic fills: no mid-price fills; use depth-walk VWAP with explicit costs and latency.
•
Fail closed: integrity uncertainty or excessive staleness halts trading and may terminate the run.
•
Reproducibility: deterministic replay must match live-run outputs on the same recorded stream and
seed.
•
AI discipline: parameters are discrete and pre-registered; no invented values; no combinatorial grid
search.
1) Executive Summary
v7.2.1 is a micro-patch to v7.2. It only closes two remaining scrutiny points: SAFE_MODE stale-book exits
and volatility-scaled sizing clipping transparency.
•
SAFE_MODE exit staleness: max_safe_mode_exit_staleness is now fixed at 2.0 seconds (no 3.0
option).
•
Sizing clipping transparency: if vol-scaled sizing requests a notional above
max_position_value_usd, the clip is logged and reported.
2) Scope and Compliance Boundaries
This system is a paper trading simulator. It does not place real trades and is not intended to provide
financial advice. It is built as a research artifact and engineering portfolio piece.
•
Public data only (order book snapshots + incremental updates).
•
No account-level or private order data required.
•
No market manipulation behavior; no attempt to influence markets.
•
Spot long-only (or flat-only): BUY opens when flat; SELL exits to flat.
3) KPIs and Definition of Done
Category
KPI
MVP target
Reliability
Uptime (collector + engine)
>= 99% during scheduled run window
Integrity
Trading during INVALID book
0 (must be impossible by design)
v7.2.2
v7.2.2
v7.2.2
v7.2.2
•
This plan targets L2 order-book venues (CEX/CLOB). AMM venues are out-of-scope.
•
If Polymarket: use CLOB endpoints; AMM-only markets excluded.
•
Data: public L2 snapshots+diffs; no private/account-level data.
•
Behavior: paper-only; no market manipulation.
•
Trading: spot long-only (or flat-only); BUY opens flat, SELL exits flat.

Page 2
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
Reproducibility
Replay equivalence
Exact match: trades/fills/equity curve
(same stream + config + seed)
Realism
Cost stress transparency
Mandatory 2D cost maps with defined
axes and correlated stress scenario
Safety
Kill switch response
Immediate halt on HARD_STOP; run
termination policy applied
deterministically
Transparency
Sizing clipping disclosure
Always log requested vs clipped
notional; report sizing_clipped_rate
(%)
Definition of Done: a reviewer can run (a) a short live paper simulation and (b) a deterministic replay of
the same recorded stream and reproduce the same outputs and final report.
4) Architecture (modular, testable)
•
Collector: WebSocket depth updates + REST snapshots; heartbeat; raw event recorder (JSONL).
•
OrderBookState: snapshot/diff reconstruction; strict continuity; bounded reorder buffer; resync
controller; staleness monitor.
•
Signal Engine: OBI features; rolling quantile triggers; Minimum Activity Filter; momentum gate; noise
persistence filters.
•
Paper Broker: order lifecycle; depth-walk VWAP fills with explicit depth bounds; fees; latency model
(observe and execute).
•
Risk Manager: sizing (fixed or vol-scaled); max position value; daily loss cap; kill switch; sizing clip
logger.
•
Replay: event-time deterministic simulator; equivalence tests; seed enforcement.
•
Reporting: daily summaries + institutional final report (edge thickness, cost maps, failure modes,
sizing-clip transparency).
Raw event recording (MVP): JSON Lines (one JSON object per line). Each record includes: message
type, exchange_event_time, local_arrival_time_ns, and the raw payload.
v7.2.2

Page 3
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
5) Data Integrity: Snapshot/Diff + Reordering Window
Order book correctness is treated as the highest-risk area. The system must never compute signals from
an invalid state.
5.1 Continuity invariants for diff ranges [U, u]
•
Discard duplicates/old updates: if u <= lastUpdateId.
•
Initial bridging (after snapshot): apply only if U <= lastUpdateId+1 <= u; then lastUpdateId := u.
•
Steady-state: prefer U == prev_u + 1, but allow bounded reordering within a window before declaring
failure.
5.2 Bounded reorder buffer
•
Maintain a buffer keyed by U; attempt to chain events so that each applied event satisfies U == prev_u
+ 1.
•
Buffer attempts are limited by reorder_window_ms and max_buffer_events (Appendix).
•
If chaining cannot be restored within the bounds, treat it as integrity failure -> HARD_STOP -> resync.
5.3 Staleness state machine
State
Trigger (example)
Behavior
NORMAL
staleness <= 1.0s
Trading allowed (subject to risk rules)
SAFE_MODE
1.0s < staleness <= 5.0s
Block new entries; continue managing existing
position under SAFE_MODE rules
HARD_STOP
staleness > 5.0s OR integrity failure
Halt trading; apply HARD_STOP policy
(including open position handling)
5.4 SAFE_MODE behavior (patched: stricter exit staleness)
•
Block new entry orders (no new BUY).
•
Continue monitoring existing position for time stop and risk stops using Exchange Event Time only.
•
If an exit condition triggers, attempt exit using the last valid book only if time_since_last_valid_book
<= max_safe_mode_exit_staleness.
•
If exit triggers but the last valid book is older than max_safe_mode_exit_staleness, escalate
immediately to HARD_STOP (fail closed) and apply the HARD_STOP open-position policy.
•
All SAFE_MODE decisions are logged with exchange_event_time and last_valid_book_age_seconds.
Policy note: max_safe_mode_exit_staleness is fixed at 2.0 seconds in this spec to avoid defensibility
issues from stale execution inputs.
5.5 HARD_STOP policy (open position handling)
•
HARD_STOP is terminal for the run. No further trading decisions are executed after a
HARD_STOP.
•
If flat: terminate run and mark status=HARD_STOP_TERMINATED.
•
If position open: terminate run and mark status=HARD_STOP_TERMINATED_OPEN_POSITION.
v7.2.2

Page 4
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
•
In the open-position case, compute a conservative exposure-only liquidation estimate using the last
valid book (if available) and record it separately; do not count it as realized PnL and do not include
post-HARD_STOP performance in headline metrics.
•
Report must explicitly show: termination reason, time in states, and whether termination occurred
while holding a position.
v7.2.2

Page 5
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
6) Signal Design: OBI + Gates (anti-churn, anti-overfit)
6.1 Base signal: multi-level Order Book Imbalance (OBI)
•
Compute OBI from bid/ask depth across N levels with decay weighting by distance to mid.
•
Entry trigger: OBI exceeds rolling quantile threshold (e.g., Q95). Exit trigger: opposite threshold (e.g.,
Q05) or stop/time rules.
6.2 Minimum Activity Filter (entry gate)
•
Volatility floor: block entries if realized_vol_bps(vol_window) < vol_min_bps.
•
Spread sanity: block entries if spread_bps exceeds a robust gate (rolling percentile or IQR-based; fully
parameterized in Appendix).
•
Cooldown timing: cooldown is measured from last exit time (SELL fill time) using Exchange Event
Time.
•
Noise persistence: require K consecutive updates or T ms persistence before a trigger is valid.
6.3 Momentum confirmation (gate only; validated)
Momentum confirmation is used as a gate to reduce false positives, not as a separate alpha source. It is
fully parameterized and validated via ablation tests.
•
Definition: signed return over momentum_window_seconds must align with OBI direction and exceed
momentum_min_bps.
•
Allowed calculation modes: simple_return (MVP). EWM is v1.1+ only.
•
Ablation requirement: report OBI-only vs momentum-only vs both; report correlation between OBI
trigger and momentum gate.
v7.2.2

Page 6
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
7) Order Lifecycle, Retry Safety, and Stops
7.1 Order lifecycle state machine
State
Meaning
Transitions
IDLE
No active order
On signal -> PENDING
PENDING
Await simulated fill after execute
latency
-> FILLED or FAILED or EXPIRED (TTL)
FILLED
Execution completed
Update position -> IDLE
FAILED
Insufficient depth / invalid state
Optional retry with re-validation OR drop ->
IDLE
EXPIRED
TTL elapsed before fill
Drop signal -> IDLE
7.2 Retry policy (signal re-validation + price deterioration guard)
•
MVP allows max_retries in {0,1}.
•
A FAILED order may be retried only if: (a) time_since_signal <= order_ttl_ms AND (b) the full entry
condition is still valid (OBI + Minimum Activity Filter + momentum gate + noise persistence).
•
Price deterioration guard: if expected VWAP at retry time is worse than original trigger VWAP by more
than max_price_deterioration_bps, drop the signal.
7.3 Stops and stop execution
•
Stop-loss and take-profit triggers are defined in bps relative to entry price (trigger logic).
•
Stop execution uses depth-walk market (bid ladder for sells).
•
Behavior if max_slippage_vs_trigger_bps is exceeded: execute_and_log (MVP fixed). Stops are risk
controls and must execute; threshold is for incident reporting.
v7.2.2

Page 7
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
8) Execution Realism: Depth-walk VWAP + Tail
Latency
8.1 Depth-walk VWAP fills with explicit allowed depth bounds
•
BUY consumes ask ladder; SELL consumes bid ladder; fill price is VWAP across consumed levels.
•
Allowed depth is bounded by two constraints: (1) max_fill_depth_levels and (2)
max_fill_impact_bps vs mid at trigger time.
•
If either constraint is exceeded, the order becomes FAILED (conservative). This prevents optimistic
'infinite depth' fills.
•
Fees applied on filled notional; all assumptions logged.
8.2 Latency modeling (observe vs execute) with tail stress
observe_latency and execute_latency are modeled separately. In high-vol regimes, latency stress
increases tail risk by scaling both lognormal mu and lognormal sigma using discrete multipliers.
•
High-vol regime definition: if realized_vol_bps(high_vol_window_minutes) exceeds the rolling
percentile threshold (high_vol_threshold_percentile) computed from the last
high_vol_lookback_hours, apply tail multipliers; otherwise multipliers=1.0.
•
Calibration source: execute latency calibrated from REST RTT percentiles during a short calibration
window; store latency_fit.json.
•
Latency floor: derived from calibrated p05 (no hard-coded unrealistically low floor).
8.3 Latency calibration failure handling (concrete fallback values)
•
Startup failure (first hour of a run): continue with the fixed conservative fallback profile (Appendix) and
log incident using_fallback_latency_profile.
•
Mid-run failure (after first hour): HARD_STOP (fail closed) and terminate run under HARD_STOP
policy.
•
Fallback values are fixed by the selected profile and stored in run metadata for replay equivalence.
9) Risk Management and Position Sizing (patched:
sizing clip transparency)
Risk exposure must be comparable across regimes. v7.2.1 keeps sizing simple: fixed notional or
volatility-scaled notional with bounded scalars and a hard max position cap.
•
Hard cap: max_position_value_usd fixed (MVP).
•
Sizing modes: fixed_notional or vol_scaled_notional (MVP allowed).
•
Sizing clip rule: if requested_notional_usd (after scaling) exceeds max_position_value_usd, the
executed notional is clipped to the cap.
•
Mandatory logging for every entry decision: requested_notional_usd, executed_notional_usd,
clipping_ratio (executed/requested), and clip_flag (true/false).
•
Mandatory report metric: sizing_clipped_rate = % of entry attempts where clip_flag=true, plus
average clipping_ratio when clipped.
v7.2.2
v7.2.2

Page 8
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
10) Replay Validation, Timestamp Semantics, and
Determinism
Replay equivalence is a correctness proof only if the system is deterministic and time semantics are
unambiguous.
10.1 Timestamp definitions (must be logged)
•
Exchange Event Time: timestamp embedded in the exchange message. This is the only timebase
allowed for strategy decisions and replay.
•
Local Arrival Time: time when the message arrives on the local machine. Allowed only for monitoring
and latency measurement.
10.2 Determinism rules (seed policy)
•
All trading logic (cooldowns, holding time, stop timing, staleness) uses Exchange Event Time only.
•
System time calls (time.time(), datetime.now()) are forbidden in decision logic and allowed only for
telemetry/logging.
•
Replay seed policy: replay must use the same RNG seed as the original run. Seed is stored in run
metadata and experiments.yml.
•
Equivalence tests: identical trades/fills/equity curve for the same stream + config + seed.
v7.2.2

Page 9
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
11) Test Plan (patched)
•
Unit tests: U/u continuity, bounded reorder buffer behavior, gap detection,
SAFE_MODE/HARD_STOP transitions.
•
SAFE_MODE exit staleness cap: if last_valid_book_age_seconds > max_safe_mode_exit_staleness
and exit triggers -> HARD_STOP and terminal status is set.
•
Sizing clip behavior: deterministic clip when requested_notional_usd > max_position_value_usd;
verify logs and sizing_clipped_rate aggregation.
•
HARD_STOP open position: termination is deterministic; exposure-only liquidation estimate recorded;
post-stop PnL is excluded.
•
Execution depth bounds: FAIL when max_fill_depth_levels or max_fill_impact_bps exceeded.
•
Signal gate tests: spread gate (both methods) blocks entries correctly; cooldown uses last-exit time;
momentum gate correctness under fixed window/threshold.
•
Order lifecycle tests: FAILED -> re-validation -> retry/drop; price deterioration guard blocks bad
retries.
•
Determinism tests: replay must not depend on wall clock; seed must match original run.
•
Fuzz tests: empty bids/asks, abnormal spread spikes, negative/zero prices or quantities, duplicate u
with different content, malformed JSON, missing fields.
v7.2.2

Page 10
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
12) Reporting Package (edge thickness + uncertainty)
12.1 Required outputs (auto-generated)
•
Equity curve + drawdown; trade stats; holding time; time-to-fill distribution.
•
Cost attribution: fees vs slippage vs latency impact.
•
Mandatory 2D break-even maps: grid over (fee_bps, extra_slippage_bps) with boundary overlays:
profit=0, profit factor=1, Sharpe=0.
•
Correlated adverse scenario: evaluate the diagonal region where fee_bps and extra_slippage_bps are
both high (mimics high-vol conditions).
•
Regime-conditional performance + failure mode narrative ('when it fails').
•
Ablation tests: OBI-only vs momentum-only vs both; correlation between triggers and gates.
•
Sizing clip transparency: report sizing_clipped_rate (%), average clipping_ratio (when clipped), and
show a small table by regime (low/mid/high vol).
•
Termination transparency: if run ends in HARD_STOP, report headline metrics as 'incomplete run'
and include time-in-state and termination reason.
12.2 Uncertainty and headline claims
•
Avoid p-value based claims for short paper runs.
•
Report trade-level bootstrap CIs; also report day-level bootstrap CIs (bootstrap over daily PnL).
•
Cap configurations (<= 6) and pre-register; freeze config for the live run.
v7.2.2

Page 11
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
13) Parameter Appendix (v7.2.1 - discrete,
reproducible)
All tunables are discrete and must be pre-registered in experiments.yml. No hidden defaults and no
AI-invented values.
13.1 Raw event recording
Parameter
Allowed values (MVP)
Notes
raw_event_format
jsonl
One JSON object per line;
streaming-friendly; easiest for
debugging/replay
13.2 Order book reconstruction
Parameter
Allowed values (MVP)
Notes
reorder_window_ms
50, 100, 200
Time window to resolve out-of-order
updates
max_buffer_events
50, 200, 500
Max buffered events inside the window
13.3 SAFE_MODE and HARD_STOP
Parameter
Allowed values (MVP)
Notes
max_safe_mode_exit_staleness
2.0 seconds (fixed)
If last valid book older than this when
exit triggers -> HARD_STOP
hard_stop_terminal
true
HARD_STOP terminates the run
(deterministic)
hard_stop_open_position_policy
terminate_and_exposure
_only
If position open: compute
exposure-only liquidation estimate; do
not realize PnL
13.4 Minimum Activity Filter + spread gate + cooldown
Parameter
Allowed values (MVP)
Notes
vol_window_minutes
1, 3, 5
Realized vol over past window
vol_min_bps
2, 3, 5
Block entries if vol < floor
spread_gate_method
rolling_percentile OR
iqr_based
Choose one method and freeze
spread_gate_percentile
90, 95, 99 (if
rolling_percentile)
Rolling percentile of spread_bps
spread_gate_multiplier
1.0, 1.5 (if rolling_percentile)
Gate: spread <= pN * multiplier
spread_gate_k
1.0, 1.5, 2.0 (if iqr_based)
Gate: spread <= p75 + k*IQR
cooldown_seconds
0, 15, 30
Cooldown measured from last EXIT time
(SELL fill)
persistence_K
3, 5, 8
Consecutive-update requirement
persistence_T_ms
100, 200, 500
Time persistence alternative
13.5 Momentum gate
v7.2.2

Page 12
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
Parameter
Allowed values (MVP)
Notes
momentum_window_seconds
5, 10, 30
Short horizon only
momentum_min_bps
0.5, 1.0, 2.0
Gate threshold
momentum_calc
simple_return
EWM only in v1.1+
13.6 Order retry safety
Parameter
Allowed values
Meaning
order_ttl_ms
500, 1000, 2000
Signal validity horizon for retry
max_retries
0, 1
At most one retry
max_price_deterioration_bps
5, 10
Drop if retry VWAP worsens beyond
this
13.7 Execution depth bounds
Parameter
Allowed values (MVP)
Notes
max_fill_depth_levels
3, 5, 10
Max book levels consumed during
depth-walk
max_fill_impact_bps
10, 20, 50
Max VWAP impact vs mid at trigger
time; exceed -> FAILED
13.8 Latency model (tail latency + failure fallback values)
Parameter
Allowed values (MVP)
Notes
observe_latency_source
ws_heartbeat_rtt
Monitoring metric
execute_latency_mode
independent_lognormal
MVP default
execute_latency_calibration
rest_rtt_percentiles
Calibration window; store
latency_fit.json
high_vol_window_minutes
15, 30
Window for realized_vol_bps used
in high-vol detection
high_vol_lookback_hours
24 (fixed)
Lookback for rolling percentile
threshold
high_vol_threshold_percentile
75, 90
Apply tail stress when current vol
exceeds this percentile
high_vol_mu_multiplier
1.0, 1.5, 2.5
Stress multiplier for lognormal mu
high_vol_sigma_multiplier
1.0, 1.5, 2.0
Stress multiplier for lognormal
sigma (tail)
latency_floor_source
calibrated_p05
Floor derived from measured
percentiles
latency_calib_fail_policy
startup_fallback_then_midru
n_hard_stop
Startup: use fixed fallback; Mid-run:
HARD_STOP
fallback_latency_profile
conservative_v1 (fixed)
Concrete fallback values below
Fallback profile: conservative_v1 (concrete values)
Field
Value
Notes
v7.2.2

Page 13
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
fallback_execute_mean_ms
200
Used to derive lognormal
parameters (stored in metadata)
fallback_execute_std_ms
100
Conservative jitter
fallback_high_vol_mu_multiplier
2.5
Applied when high-vol regime
detected
fallback_high_vol_sigma_multiplier
2.0
Heavy tail stress
13.9 Cost stress axes (2D map definitions)
Parameter
Allowed values (MVP)
Notes
fee_bps_grid
2, 5, 10, 20
Override fee in bps for cost maps
(simulation parameter; no claim
about exchange fees)
extra_slippage_bps_grid
0, 2, 5, 10, 20
Additional adverse slippage applied
on top of depth-walk VWAP to
stress hidden frictions
correlated_adverse_region
fee_bps>=10 AND
extra_slippage_bps>=10
Must report results for the high-high
corner explicitly
13.10 Position sizing
Parameter
Allowed values (MVP)
Notes
sizing_mode
fixed_notional OR
vol_scaled_notional
Choose and freeze per run
base_notional_usd
250, 500, 1000
Baseline notional (requested
before cap)
reference_window_hours
6, 24
Vol estimate window (MVP)
min_scalar
0.3, 0.5
Lower bound on scaling
max_scalar
1.5, 2.0
Upper bound on scaling
(requested before cap)
max_position_value_usd
1500 (fixed)
Hard cap; if requested > cap,
executed is clipped and must be
logged/reported
13.11 Stop execution
Parameter
Allowed values (MVP)
Notes
stop_exec_mode
depth_walk_market
Use bid ladder for sells
allow_worse_fill
true
Stops are risk controls; must
execute
max_slippage_vs_trigger_bps
10, 20
Threshold for incident reporting
behavior_if_exceeded
execute_and_log
MVP fixed behavior
13.12 Replay seed policy
Parameter
Allowed values (MVP)
Notes
replay_seed_policy
match_original_seed
Replay must reuse the same seed
stored in run metadata
v7.2.2

Page 14
AI Paper Trading Agent - Startup Plan v7.2.1 (Patch)
14) MVP Roadmap (startup execution)
•
M0 Spec Freeze (1-2 days): finalize parameters; define acceptance criteria and test gates; lock
report template.
•
M1 Data Integrity (3-5 days): snapshot/diff sync; bounded reorder buffer;
SAFE_MODE/HARD_STOP; recorder; incidents.
•
M1.5 Replay Equivalence (2-3 days): event-time determinism; seed enforcement; equivalence tests.
•
M2 Execution Realism (3-5 days): depth-walk VWAP with depth bounds; latency calibration + tail
stress; retry re-validation; stop execution; tests.
•
M3 Live Paper Run (2-4 weeks): freeze config; daily reports; incident tracking; sizing_clipped_rate
tracking; uptime KPI; termination transparency if HARD_STOP occurs.
•
M4 Institutional Report (3-4 days): 2D break-even maps (fee_bps, extra_slippage_bps) + correlated
stress + failure analysis + ablations + bootstrap CIs.
15) Intentionally excluded (MVP)
•
Multi-venue arbitrage: high complexity; increases failure surface; defer to Phase 2.
•
Complex ML signals: excluded to avoid overfitting and preserve interpretability.
•
Full matching-engine simulation with partial fills: defer; MVP remains conservative with FAIL +
controlled retry.
•
Marketing-level statistical claims: replaced by bootstrap CIs and disciplined experiment caps.
16) Final deliverables (portfolio-ready)
•
Repo with runbook + deterministic replay + tests.
•
SQLite DB + exports (trades, equity curve, incidents, latency_fit.json, run_metadata.json).
•
Final report with mandatory 2D break-even maps (fee_bps, extra_slippage_bps) including boundary
overlays and correlated adverse region summary.
•
Sizing clip transparency section: sizing_clipped_rate (%), average clipping_ratio, and a small
by-regime table.
•
Pre-registered experiments.yml (config frozen during live run).
•
Raw event recordings in JSONL for replay/debug.
•
If HARD_STOP terminates the run: a clearly labeled 'incomplete run' report with termination
diagnostics.
v7.2.2
