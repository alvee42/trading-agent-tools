# Market State / Regime Agent (“Weather Report”)

## Purpose

The Market State / Regime Agent is a **non-executing analytical agent** whose sole responsibility is to classify the current ES/NQ market environment in real time and communicate **what type of behavior is statistically likely**.

This agent:
- Does NOT place trades
- Does NOT suggest entries, exits, or sizing
- Does NOT output directional bias

It functions as a **contextual gatekeeper** for all other analytical agents (order flow, structure, confluence, risk).

---

## Core Question

> “What kind of market is this right now, and how reliable are lower-level signals under these conditions?”

---

## Output Contract (Required)

The agent must emit a structured report at a fixed cadence (e.g. every 5 minutes) and on event triggers.

### Required Output Fields

```json
{
  "instrument": "ES | NQ",
  "timestamp": "...",
  "primary_regime": "...",
  "secondary_tag": "... | null",
  "confidence": 0-100,
  "volatility_state": "compressing | normal | expanding | extreme",
  "participation_state": "thin | normal | heavy",
  "balance_state": "balanced | transitioning | imbalanced",
  "trend_quality": "none | weak | clean | extreme",
  "noise_level": "low | medium | high",
  "session_phase": "...",
  "order_flow_reliability_note": "..."
}










Additional Notes: 

Regime Taxonomy (Canonical)
1. Balanced / Rotational

Price rotates around value; mean reversion dominates.

Characteristics

High bar overlap

VWAP acts as gravity

Breakouts frequently fail

Subtypes

Tight balance (compression)

Normal balance

Distribution / migrating balance

2. Trend / Initiative

One side consistently initiates and price accepts movement.

Characteristics

Low overlap

Directional efficiency

VWAP slope meaningful

Subtypes

Clean trend

Grinding trend

Liquidation / cascade

3. Transition / Breakout Attempt

Market attempts to leave balance; acceptance not confirmed.

Characteristics

Range expansion

Increased volume/volatility

High failure rate early

This regime is high risk and must be explicitly flagged.

4. Event-Distorted

Market behavior dominated by scheduled or unscheduled events.

Examples

CPI, FOMC, NFP

Major news headlines

This tag overrides other regimes.

Inputs & Features
Timeframes

1-minute bars

5-minute bars

Optional 15-minute confirmation layer

Price Structure Features

Session range vs rolling historical range (z-score)

True range and ATR slope

Bar overlap ratio (5m)

Directional efficiency (net move / total movement)

Average pullback depth

VWAP slope and distance

Opening range position (ORH / ORL)

Volatility Features

ATR(14) on 5m

ATR slope

Short-term realized volatility vs long-term RV

Volatility of volatility

Participation Features

Volume vs time-of-day expected curve

Volume acceleration / deceleration

Range per unit volume (thin vs heavy participation proxy)

Session Phase Awareness (ES/NQ)

Pre-open

Opening range (first 15–30 min)

Mid-morning

Lunch

Mid-afternoon

Power hour

Close

Metrics must be interpreted relative to session phase.

Decision Logic (High Level)
Step 1: Balance vs Imbalance

Compute competing scores:

Balance score

High bar overlap

VWAP mean reversion

Failed breakout frequency

Low efficiency

Imbalance score

High efficiency

VWAP slope magnitude

Impulse vs pullback asymmetry

Sustained range expansion

Classification:

Balanced if balance score > threshold

Imbalanced if imbalance score > threshold

Otherwise Transition

Step 2: Volatility State

Compressing: ATR slope ↓, RV short < RV long

Expanding: ATR slope ↑, RV short > RV long

Extreme: ATR z-score above threshold

Step 3: Participation State

Compare cumulative volume to expected volume curve:

Thin: below expectation, unstable moves

Heavy: above expectation, cleaner moves

Step 4: Overrides

Scheduled event window → Event-Distorted

Sudden range explosion + structure degradation → Liquidation subtype

Step 5: Confidence Score

Confidence increases with:

Feature agreement

Stability across multiple windows

Confidence decreases with:

Feature conflict

Rapid regime flipping

Human-Readable Output Examples

Balanced / Rotational (Confidence 76)
Volatility: Normal
Participation: Normal
Noise: Medium
Order flow reliability: Reliable only at range extremes; unreliable mid-range.

Trend / Initiative – Clean (Confidence 84)
Volatility: Expanding
Participation: Heavy
Noise: Low
Order flow reliability: Continuation signals favored; fading less reliable.

Transition / Breakout Attempt (Confidence 51)
Volatility: Expanding
Participation: Normal
Noise: High
Order flow reliability: Signals unreliable until acceptance or failure.

Event-Distorted
Order flow reliability: All microstructure warped; interpretation degraded.

ES vs NQ Calibration Notes

NQ

Higher baseline volatility

More stop-runs and false breakouts

Require stricter confirmation for trend

ES

Cleaner balance behavior

VWAP and structure more reliable

Balance regimes more stable

Maintain separate baselines and thresholds per instrument.

Update Cadence
Heartbeat

Every 5 minutes

Full regime report

Event-Driven Alerts

Regime flip with confidence > threshold

Volatility shifts to extreme

Transition → confirmed balance or trend

Event window entry/exit

Tooling & Data Sources
Charles Schwab / thinkorswim API (Applicable Use)

The following can be sourced directly from Schwab / thinkorswim:

Live quotes

Time-based candles (1m, 5m)

Volume

VWAP (calculated client-side)

Session OHLC

Account-agnostic data (no execution required)

This API is sufficient for:

Price-based regime detection

Volatility and participation modeling

Session-aware metrics

Limitations of Schwab / thinkorswim

Limited historical depth for tick-level research

No native market profile or regime labels

DOM depth is not intended for research persistence

This agent does NOT require deep DOM, so these limitations are acceptable.

Non-Goals (Explicit)

This agent will NEVER:

Place or suggest trades

Output “buy/sell” language

Override human discretion

Interpret order flow directly

It exists to define context, not decisions.

Success Criteria

The agent is successful if:

It reduces over-trading during transition/noise

It increases trust in order flow at correct locations

It explains why conditions changed, not just that they did

It makes trading feel slower, calmer, and more selective