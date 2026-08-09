# Market data analysis — target-side listing snapshots

## What changed (2026-08-08)

The gatherer now stores a snapshot of the **target (sell) side** of every flip on
each reprice: the up to 10 cheapest sell offers for the flip's target query,
with **seller, price, and how long the listing has been active**.

### Why
The trade API's `POST /search` returns up to **100** matching offer IDs, but
`GET /fetch` only hands back **10** full listings per request (400 if you send
more). We already make one search + one fetch per flip — we were just slicing
`ids[:5]` and throwing the listing detail away. Capturing all 10 costs **zero
extra requests**; we only stopped discarding data we already fetched.

### Where it lives
- New table `listing_snapshots` in the gatherer's `flips.db` (schema migration v7):
  ```
  id          INTEGER PRIMARY KEY AUTOINCREMENT
  flip_id     TEXT        — which flip
  fetched_ms  INTEGER     — epoch ms of this fetch (batch key)
  rank        INTEGER     — 0 = cheapest (search sort order)
  seller      TEXT        — listing.account.name
  amount      REAL        — listing.price.amount
  currency    TEXT        — listing.price.currency (non-divine kept too)
  indexed_ms  INTEGER     — listing.indexed → active_for = now − indexed_ms
  ilvl        INTEGER     — item.ilvl (sanity)
  rarity      TEXT        — item.rarity (sanity)
  ```
  Indexes on `(flip_id, fetched_ms)` and `(fetched_ms)`.
- **Active duration is derived at read time** (`now − indexed_ms`), not stored as
  a precomputed age that would go stale.
- **60-day TTL**: `prune_listings(60)` runs from the existing `_prune_history()`
  on every `save_price`.
- **Source side is not snapshotted** (only priced); manual / ninja-target flips
  skip (no query → no sellers).

### Code
- `gatherer/gatherer/schema.py` — migration v7 (table + indexes).
- `gatherer/gatherer/store.py` — `save_listings()` (bulk insert, one commit per
  flip), `prune_listings()`, `db_size_bytes()` (main DB + WAL, real `ls -l` size).
- `gatherer/gatherer/pricer.py` — `_collect_divine_prices` slices `[:10]` and
  returns listing rows; `_fetch_prices` persists target-side snapshots.
- `gatherer/gatherer/server.py` — `GET /api/status` reports `db_size` bytes.

### Volume / sizing notes
- Per full scan: 144 flips × up to 10 rows ≈ 1,440 rows, one commit per flip.
  Target queries are narrower than source, so `total` is often well under 100 —
  real snapshots are usually fewer than 10 rows.
- SQLite is **not compressed** and we're keeping it that way (native SQLite has
  no compressed storage; the file is measured in MB — not worth the complexity).
- The `-wal` file is SQLite's crash-safe write buffer, NOT a data log; it
  self-bounds (~4 MB, auto-checkpoints). Keep WAL on — snapshots share the file
  with `flips`/`prices`/`price_history` (never-delete data); disabling journaling
  would risk corrupting all of it on a crash.
- The SPA shows a `DB x MB` pill (main + WAL) next to the rate-limit pills to
  monitor growth. Watch it; the 60-day prune is the lever if it grows too fat.

---

# P(sell ≤ T) market analysis — implementation plan

## Overview

Estimate per-flip probability of selling within 1d/3d/7d from listing snapshots.
Algorithm: Gamma-Poisson competing risks (SOLD vs PRICEDROP), no ML, no training.
All compute runs locally (Pi too constrained). Gatherer only exports raw data.

## Decisions (settled)

| Item | Decision |
|------|----------|
| `my_price` | Cheapest listing price in current snapshot (you always post at cheapest) |
| Queue position | Count active sellers at that exact price already present in snapshot |
| Horizons | 1d, 3d, 7d |
| Recent 48h events | Treat disappeared-in-last-48h as SOLD (market is slow, unlikely to come back) |
| `refresh_tier` | `high` (fast=true, ~2-5min Δt) / `low` (fast=false, ~30min Δt) |
| `item_type` | Base name from GROUPS dict in `app/pypoe/db/bases.py` |
| Location | Local app (Pi too constrained for 7-day window compute) |
| Data sync | Incremental watermark, follow `history.py` pattern exactly |

## Known limitations

- L1: λ_sell and λ_drop modeled as independent competing risks (unverifiable Tsiatis bias)
- L2: Method-of-moments Gamma requires var > mean — guard fallback to Poisson
- L3: SOLD/PRICEDROP disambiguation uses 48h seller reappearance check; last
  48h of window has no forward data — events there are **treated as SOLD** (explicit
  decision per above; market is slow, unlikely to return)
- L4: FIFO queue-position assumes oldest-listed-first consumption (approximation)
- L5: τ_decay=6h is a calibration constant, not learned
- L6: refresh_tier mitigates informative sampling (fast vs slow repricing) but is a proxy
- L7: my_queue_position requires reliable (seller,price) first-seen timestamps

---

## Phase 1 — Data plumbing (gatherer side)

### 1.1 — `Store.listings_since()` query method

**File:** `gatherer/gatherer/store.py` (~after `prune_listings()` at line 366)

```python
def listings_since(self, since_ms: int = 0) -> list[dict]:
    rows = self._conn.execute(
        "SELECT flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity"
        " FROM listing_snapshots WHERE fetched_ms > ?"
        " ORDER BY fetched_ms",
        (since_ms,),
    ).fetchall()
    return [
        {
            "flip_id": r[0], "fetched_ms": r[1], "rank": r[2],
            "seller": r[3], "amount": r[4], "currency": r[5],
            "indexed_ms": r[6], "ilvl": r[7], "rarity": r[8],
        }
        for r in rows
    ]
```

**Exit condition:** returns `[]` when no new snapshots. No pagination needed —
snapshots are sparse (<10 rows per flip per reprice, ~144 flips → ~1440 rows/scan).

### 1.2 — `GET /api/listings?since=<epoch_ms>` handler

**File:** `gatherer/gatherer/server.py`

Register in `do_GET()` (line 85-101):

```python
elif path == "/api/listings":
    self._handle_get_listings(params)
```

Add handler (mirror `_handle_get_history` pattern at line 265):

```python
# ── GET /api/listings?since=<epoch_ms> ─────────────────────

def _handle_get_listings(self, params):
    since = 0
    raw = params.get("since", [None])[0]
    if raw:
        try:
            since = int(raw)
        except ValueError:
            self._reply_json(400, {"error": "invalid since parameter"})
            return
    self._reply_json(200, {"rows": _store.listings_since(since)})
```

**Response shape:** `{"rows": [{flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity}, ...]}`

### 1.3 — `GathererClient.listings(since)` client method

**File:** `app/pypoe/flipper/gatherer_client.py` (~after `history()` at line 60)

```python
def listings(self, since_ms: int = 0) -> dict:
    resp = requests.get(f"{self._base}/api/listings", params={"since": since_ms}, timeout=30)
    resp.raise_for_status()
    return resp.json()
```

---

## Phase 2 — Data plumbing (local app side)

### 2.1 — Local listings mirror module

**File:** `app/pypoe/analysis/mirror.py` (new)

Follow `history.py` pattern exactly. Same structure: `_DB`, `_lock`, `_connect()`, `max_ms()`, `sync()`.

```
app/pypoe/analysis/
├── __init__.py
└── mirror.py
```

**Schema** (mirrors gatherer `listing_snapshots`):

```sql
CREATE TABLE IF NOT EXISTS listing_snapshots (
    flip_id      TEXT    NOT NULL,
    fetched_ms   INTEGER NOT NULL,
    rank         INTEGER NOT NULL,
    seller       TEXT    NOT NULL,
    amount       REAL    NOT NULL,
    currency     TEXT    NOT NULL,
    indexed_ms   INTEGER NOT NULL,
    ilvl         INTEGER,
    rarity       TEXT,
    PRIMARY KEY (flip_id, fetched_ms, rank)
)
```

**`sync(client)` function:**
```python
def sync(client: GathererClient) -> int:
    since = max_ms()
    data = client.listings(since)
    rows = data.get("rows", [])
    with _lock:
        conn = _connect()
        added = 0
        for r in rows:
            cur = conn.execute(
                "INSERT OR IGNORE INTO listing_snapshots"
                " (flip_id, fetched_ms, rank, seller, amount, currency, indexed_ms, ilvl, rarity)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (r["flip_id"], r["fetched_ms"], r["rank"], r["seller"],
                 r["amount"], r["currency"], r["indexed_ms"],
                 r.get("ilvl"), r.get("rarity")),
            )
            added += cur.rowcount
        cutoff_ms = int((time.time() - HISTORY_DAYS * 86400) * 1000)
        conn.execute("DELETE FROM listing_snapshots WHERE fetched_ms < ?", (cutoff_ms,))
        conn.commit()
    return added
```

- `_DB = Path(...) / "data" / "listings.db"` (same location as `history.db`)
- `HISTORY_DAYS = 60` (match gatherer prune)
- `_lock = threading.Lock()`
- `max_ms()` returns `MAX(fetched_ms)` from local DB, 0 if empty
- Sync loop: call from `api.py` `_sync_loop()` alongside `history.sync()`, same 300s interval

### 2.2 — Sync loop integration

**File:** `app/pypoe/flipper/api.py`

In the existing `_sync_loop()` (around line 326), add alongside `history.sync()`:

```python
import pypoe.analysis.mirror as listings_db

# inside _sync_loop():
listings_db.sync(_gatherer)
```

---

## Phase 3 — Event classification engine

### 3.1 — File structure (all new)

```
app/pypoe/analysis/__init__.py    # Public entry: analyze_flip()
app/pypoe/analysis/mirror.py      # Phase 2 — local sync
app/pypoe/analysis/engine.py      # Phase 3 — event classification
app/pypoe/analysis/prior.py       # Phase 4 — Gamma prior fitting
app/pypoe/analysis/survival.py    # Phase 5 — posterior + CIF + projections
```

### 3.2 — Core data types

```python
# engine.py
@dataclass
class IntervalEvent:
    """What happened in one snapshot interval for one flip."""
    delta_t_hours: float           # t_i - t_{i-1} in hours
    k_sell: int                    # SOLD events at/below cheapest price
    k_drop: int                    # PRICEDROP events at/below cheapest price
    censored: bool                 # True if visibility cutoff dropped

@dataclass
class Exposure:
    """Aggregate across all intervals for a group."""
    k_sell_total: int
    k_drop_total: int
    t_exposure_hours: float

# prior.py
@dataclass
class GammaParams:
    alpha: float
    beta: float
```

### 3.3 — `classify_events()` — per flip

**File:** `app/pypoe/analysis/engine.py`

```python
def classify_events(
    flip_id: str,
    snapshots_7d: list[dict],       # all snapshots for this flip, last 7 days,
                                    # sorted by fetched_ms ASC
    now_ms: int,                    # current epoch ms
) -> list[IntervalEvent]:
```

**Algorithm (step by step):**

1. Group snapshots by `fetched_ms` → each group = one snapshot moment.
   Each snapshot moment `S_i` has:
   - `threshold_i` = price (amount) at rank 9 (position 10, 0-indexed) — the visibility cutoff
   - `offers_i` = set of `(seller, amount)` pairs visible in this snapshot

2. If only one snapshot moment exists: return `[]` (nothing to classify).

3. For each consecutive pair `(S_{i-1}, S_i)`:

   a. **Cheapest price at t_{i-1}**: `cheapest = min(amount for (seller, amount) in offers_{i-1})`
   
   b. **Identify disappeared offers**: offers in `S_{i-1}` but not in `S_i`, with `amount <= cheapest`
   
   c. For each disappeared offer:
      - If `threshold_i >= threshold_{i-1}` (cutoff did NOT drop) → **TRUE EVENT**
        - Check: does same `seller` reappear in ANY later snapshot (within 7-day window, within 48h after `t_i`), at `amount <= cheapest`?
        - YES → `k_drop += 1` (PRICEDROP)
        - NO → `k_sell += 1` (SOLD)
        - IMPORTANT: if `t_i` is within last 48h of `now_ms`, forward check is unreliable → **treat as SOLD**
      - If `threshold_i < threshold_{i-1}` (cutoff dropped) → **CENSORED**
        - The offer may still be on market, just fell out of top 10
        - `censored = True` for this interval
        - The interval's `delta_t` contributes to exposure but events are unsure

   d. Build `IntervalEvent`:
      ```python
      delta_t_hours = (t_i - t_{i-1}) / 3600000
      IntervalEvent(
          delta_t_hours=delta_t_hours,
          k_sell=k_sell,
          k_drop=k_drop,
          censored=censored,
      )
      ```

4. Return list of `IntervalEvent`.

**Edge cases handled:**
- No snapshots → empty list
- Single snapshot → empty list
- No events in interval → `k_sell=0, k_drop=0`, still have `delta_t_hours` for exposure
- Seller reappears after 48h → counts as SOLD (48h window is hard)
- `threshold_i` is None (fewer than 10 listings) → no visibility cutoff, treat as not dropped

### 3.4 — `aggregate_exposures()` — across flips of same type

```python
def aggregate_exposures(
    all_events: dict[str, list[IntervalEvent]],  # flip_id -> events
    flips: dict[str, FlipMeta],                  # flip_id -> (item_type, fast)
) -> dict[tuple[str, str], Exposure]:
    """Group events by (item_type, refresh_tier) and sum."""
```

- `item_type` = extract base type from flip's `name` field (e.g. "Royal Plate" from "royal plate 29")
- `refresh_tier` = `"high"` if `fast=true`, `"low"` if `fast=false`
- For each `(item_type, tier)` key, sum `k_sell`, `k_drop`, `t_exposure` across all flips
- For censored intervals, only accumulate `t_exposure` up to the point of censoring
  (if the interval had multiple events and was censored, `t_exposure` is still the full `delta_t` —
  the flag only means we don't trust the k counts, not that time didn't pass)

**Fallback chain (when a group has < 20 intervals):**
```python
def resolve_tier(exposures_by_tier, exposures_by_type, global_exposure):
    for key in [(item_type, "high"), (item_type, "low")]:
        if exposures_by_tier.get(key) and _interval_count[key] >= 20:
            return key, exposures_by_tier[key]
    # drop tier
    if _interval_count_by_type[item_type] >= 20:
        return (item_type,), exposures_by_type[item_type]
    # global market-wide
    return ("global",), global_exposure
```

Count intervals as: number of `IntervalEvent` objects (not sum of k), since each interval is one observation.

---

## Phase 4 — Gamma-Poisson prior

### 4.1 — `fit_prior()` 

**File:** `app/pypoe/analysis/prior.py`

```python
def fit_prior(
    exposures: dict[tuple[str, ...], Exposure],
    interval_counts: dict[tuple[str, ...], int],
) -> dict[tuple[str, ...], dict[str, GammaParams]]:
    """Returns {(key): {'sell': GammaParams, 'drop': GammaParams}} for each group key."""
```

**Algorithm per group key:**

1. Collect all per-interval rates from each flip in the group:

   For each `IntervalEvent` from each flip in this group:
   ```python
   if k_sell > 0 and delta_t_hours > 0:
       rates_sell.append(k_sell / delta_t_hours)
   if k_drop > 0 and delta_t_hours > 0:
       rates_drop.append(k_drop / delta_t_hours)
   ```
   
   NOTE: intervals with `k=0` contribute `t_exposure` to the sum but we skip `rate=0`
   entries because a zero-rate interval that's very short (e.g. 2 minutes, 0 events) 
   would produce a `rate=0` that drags the mean down. Instead, zero-event intervals
   are captured through the total T_exposure in the posterior (Phase 5). This is
   equivalent to treating the Gamma as fit on positive-event-rate intervals and the 
   total non-event time as captured through the denominator.

2. Compute:
   ```python
   mean_rate = statistics.mean(rates)
   var_rate = statistics.variance(rates)  # requires >= 2 rates
   ```

3. Guard 1 — zero/negative rates:
   ```python
   if not rates:
       # can't fit anything — caller should use DEFAULT_PRIOR, return None
       return None
   ```

4. Guard 2 — close-to-zero variance (step 4a from algorithm):
   ```python
   epsilon_rel = 1e-4
   var_safe = max(var_rate, epsilon_rel * mean_rate**2, 1e-6)
   ```

5. Guard 3 — underdispersion (step 4b):
   ```python
   if var_safe <= mean_rate:
       # fallback: pure Poisson, no shrinkage
       return {"lambda": mean_rate, "is_poisson": True}
   ```

6. Normal Gamma fit (method of moments):
   ```python
   alpha = mean_rate**2 / var_safe
   beta = mean_rate / var_safe
   return GammaParams(alpha=alpha, beta=beta)
   ```
   
   NOTE: `beta` here is the RATE parameter (`θ = 1/β`). Posterior update:
   `lambda = (alpha + k) / (beta + T)`.

7. Store separately for sell and drop:
   ```python
   result[key] = {
       "sell": fit_for(rates_sell),
       "drop": fit_for(rates_drop),
   }
   ```

### 4.2 — Fallback chain + default prior

```python
# In prior.py, top of file:

# Per-hour rates. Conservative — expects maybe 1 sale every 4 days.
# alpha: pseudo-count of events observed. beta: pseudo-hours of exposure.
# Small alpha means the prior evaporates quickly after real data arrives.
DEFAULT_PRIOR = {
    "sell": GammaParams(alpha=0.25, beta=600.0),  # 0.01 sales/day (1 per ~4 days)
    "drop": GammaParams(alpha=0.1,  beta=600.0),  # 0.004 drops/day (rarer)
}
```

When a `(item_type, tier)` key has < 20 intervals total → drop tier → fit on `(item_type,)` alone.  
When `(item_type,)` still has < 20 → fit one global `("global",)` prior.  
When `("global",)` still has < 20 → or `fit_prior()` returns `None` → **use `DEFAULT_PRIOR`**.

```python
def resolve_prior(exposures, all_events_flip, flip_meta):
    """Try fallback chain, return (key, prior_dict). Last resort: DEFAULT_PRIOR."""
    # Try (item_type, tier)
    key = (flip_meta.item_type, flip_meta.refresh_tier)
    rates = collect_rates(all_events_flip, key)
    if len(rates) >= 20 and (prior := _fit_gamma(rates)):
        return key, prior

    # Try (item_type,)
    key = (flip_meta.item_type,)
    rates = collect_rates(all_events_flip, key)
    if len(rates) >= 20 and (prior := _fit_gamma(rates)):
        return key, prior

    # Try global
    key = ("global",)
    rates = collect_rates(all_events_flip, key)
    if len(rates) >= 20 and (prior := _fit_gamma(rates)):
        return key, prior

    # Give up — use hardcoded conservative default
    logger.info("resolve_prior: insufficient data (<20 intervals) — using DEFAULT_PRIOR")
    return ("default",), DEFAULT_PRIOR
```

**Why `alpha=0.25`?** It means after seeing 1 real sale, the posterior is already
dominated by data: `(0.25+1)/(600+T_exposure)`. The default prior contributes ~20%
after 1 observed sale, <1% after 5 sales. It's a warm-start, not a prior that
fights real observations.

### 4.3 — Self-check

```python
def _demo():
    """Verify Gamma fit gives sensible numbers."""
    from pypoe.analysis.prior import fit_prior
    # synthetic: 2 sales in 100 hours of exposure
    rates = [0.02] * 10  # 10 intervals each with 0.02 rate
    params = _fit_gamma(rates)  # internal helper
    assert params.alpha > 0 and params.beta > 0
    # mean should be close to 0.02
    assert 0.01 < params.alpha / params.beta < 0.03
    print("prior._demo OK")
```

---

## Phase 5 — Posterior, corrections, and CIF

### 5.1 — `item_posterior()` 

**File:** `app/pypoe/analysis/survival.py`

```python
def item_posterior(
    prior: GammaParams,
    k: int,                    # this item's own event count
    t_exposure_hours: float,   # this item's own exposure
) -> tuple[float, float]:
    """Returns (lambda_posterior, variance)."""
    lam = (prior.alpha + k) / (prior.beta + t_exposure_hours)
    var = (prior.alpha + k) / (prior.beta + t_exposure_hours) ** 2
    return lam, var
```

**Property:** `t_exposure=0` → `lam = prior.alpha / prior.beta` (pure market prior).  
Large `t_exposure` → `lam ≈ k/t` (empirical). No special-case code needed — the
formula handles `k=0, t=0` by construction.

**Poisson fallback:** if `prior.is_poisson == True`, `lam = prior.lambda` for all items
(no shrinkage, no `k/T` blend). In practice this happens only for item types with 
near-zero-variance rates. Return `lam` with a warning logged.

### 5.2 — Queue position correction

```python
def my_queue_position(
    flip_id: str,
    cheapest_price: float,
    snapshots: list[dict],    # all snapshots for this flip, 7-day window
) -> int:
```

**Algorithm:**

1. From the most recent snapshot, find all entries with `amount == cheapest_price`.
   Let these be the active sellers at our price.

2. For each active seller, find their `first_seen_ms` = the earliest `fetched_ms` across
   ALL snapshots where `(seller, amount)` pair appears with `amount == cheapest_price`.

3. Count how many of these sellers have `first_seen_ms < our_first_listed_ms`,
   where `our_first_listed_ms` = now (since we haven't listed yet — we'd queue behind
   everyone already there).

4. Return that count. If 3 sellers are already at cheapest price, `queue_pos = 3`,
   `lambda_sell_corrected = lambda_sell / (1 + 3) = lambda_sell / 4`.

**Edge case:** if `first_seen_ms` is unreliable due to sparse snapshots (L7), log a
warning and mark confidence as `"low"` (handled in Phase 6).

### 5.3 — Downward pressure correction

```python
def downward_pressure_ratio(
    flip_id: str,
    cheapest_price: float,
    events: list[IntervalEvent],   # this flip's events
    avg_historical_downward_flow: float,  # from prior group
) -> float:
```

For the most recent interval: count how many offers appeared at `amount < cheapest_price`
(new listings below our price). Normalize by the 7-day average of the same metric for
this `(item_type, tier)` group.

```python
def compute_downward_flow(snapshots, cheapest_price):
    """Count new offers below cheapest_price in most recent interval."""
    prev = snapshots[-2]
    curr = snapshots[-1]
    prev_sellers = set(s for s, a in prev["offers"] if a < cheapest_price)
    curr_sellers = set(s for s, a in curr["offers"] if a < cheapest_price)
    return len(curr_sellers - prev_sellers)

flow = compute_downward_flow(...)
ratio = flow / max(1, avg_historical_downward_flow_for_tier)
lambda_drop_corrected = lambda_drop * ratio
```

### 5.4 — CIF computation

```python
@dataclass
class HorizonResult:
    p_sell: float
    p_drop: float
    p_stagnation: float
    confidence: str         # "high" or "low"

def compute_cif(
    events: list[IntervalEvent],
    lam_sell_corrected: float,     # after queue position correction
    lam_drop_corrected: float,     # after downward pressure correction
    horizons_days: list[int],      # [1, 3, 7]
    now_ms: int,
    last_snapshot_ms: int,
) -> dict[int, HorizonResult]:
```

**Historical pass** (steps 1..k, where interval k is the most recent completed interval):

```python
S = 1.0  # survival at t_0
cif_sell = 0.0
cif_drop = 0.0

for event in events:
    dt = event.delta_t_hours / 24  # convert to days
    total_rate = lam_sell_corrected + lam_drop_corrected
    # survival decrement for this interval
    interval_survival = math.exp(-total_rate * dt)
    # CIF increment
    frac = lam_sell_corrected / total_rate if total_rate > 0 else 0.0
    cif_sell += frac * (1 - interval_survival) * S
    frac_drop = lam_drop_corrected / total_rate if total_rate > 0 else 0.0
    cif_drop += frac_drop * (1 - interval_survival) * S
    S *= interval_survival
```

After historical pass, `S_history = S`, `cif_sell_history = cif_sell`, `cif_drop_history = cif_drop`.

**Forward projections** (one virtual interval of length T from "now"):

Use final lambdas (after EWMA confidence decay, see Phase 6):

```python
for T_days in horizons_days:
    total_rate = lam_sell_final + lam_drop_final
    S_T = math.exp(-total_rate * T_days)
    frac = lam_sell_final / total_rate if total_rate > 0 else 0.0
    P_sell = cif_sell_history + frac * (1 - S_T) * S_history
    P_drop = cif_drop_history + (lam_drop_final/total_rate if total_rate>0 else 0) * (1 - S_T) * S_history
    P_stagnation = 1.0 - P_sell - P_drop
    
    # confidence flag
    last_dt_days = events[-1].delta_t_hours / 24 if events else 999
    conf = "high" if T_days >= 2 * last_dt_days else "low"
    
    result[T_days] = HorizonResult(
        p_sell=round(P_sell, 4),
        p_drop=round(P_drop, 4),
        p_stagnation=round(max(0, P_stagnation), 4),
        confidence=conf,
    )
```

**Edge cases:**
- `total_rate == 0` → `P_sell = 0`, `P_drop = 0`, `P_stagnation = 1.0` (nothing ever happens)
- No events (new item) → `S_history = 1.0`, pure forward projection from prior
- `P_stagnation < 0` due to rounding → clamp to 0.0

### 5.5 — EWMA confidence decay (staleness)

```python
TAU_DECAY_HOURS = 6.0

def ewma_lambda(
    lam_item: float,
    lam_prior: float,
    last_snapshot_ms: int,
    now_ms: int,
) -> float:
    delta_hours = (now_ms - last_snapshot_ms) / 3600000
    weight = math.exp(-delta_hours / TAU_DECAY_HOURS)
    return weight * lam_item + (1 - weight) * lam_prior
```

Apply to both `lam_sell_corrected` and `lam_drop_corrected` before forward projections.
The stallest the last observation, the more we revert to market prior.

---

## Phase 6 — Public entry point

### 6.1 — `analyze_flip()`

**File:** `app/pypoe/analysis/__init__.py`

```python
def analyze_flip(
    flip_id: str,
    flip_name: str,           # e.g. "royal plate 29"
    flip_fast: bool,          # fast=true/false → refresh_tier
) -> dict[int, dict] | None:
    """Returns {1: {p_sell, p_drop, p_stagnation, conf}, 3: {...}, 7: {...}} or None if insufficient data."""
```

**Flow:**

1. Load all snapshots for this flip from local `listings.db` (last 7 days)
2. If < 2 snapshot moments → return None (insufficient data)
3. Call `classify_events()` → `list[IntervalEvent]`
4. Extract `item_type` from `flip_name` (lowercase, strip quality suffix → map to GROUPS base name)
5. Load all other flips of same `(item_type, refresh_tier)` to pool events
6. Call `fit_prior()` for relevant group keys
7. Resolve prior via fallback chain
8. Call `item_posterior()` for this flip
9. Compute `my_queue_position()` and `downward_pressure_ratio()`
10. Apply corrections to lambdas
11. Apply EWMA decay
12. Call `compute_cif()` for [1, 3, 7]
13. Return results dict

### 6.2 — BFF endpoint

**File:** `app/pypoe/flipper/api.py`

```python
# GET /api/analysis?flip_id=<uuid>
def _handle_analysis(self):
    params = parse_qs(urlparse(self.path).query)
    flip_id = params.get("flip_id", [None])[0]
    if not flip_id:
        self._reply_json(400, {"error": "missing flip_id"})
        return
    
    # find flip in cache
    flip = _flip_cache.get(flip_id)
    if not flip:
        self._reply_json(404, {"error": "flip not found"})
        return
    
    from pypoe.analysis import analyze_flip
    result = analyze_flip(flip["id"], flip["name"], flip["fast"])
    if result is None:
        self._reply_json(200, {"status": "insufficient_data"})
    else:
        self._reply_json(200, result)
```

**Response when sufficient data:**
```json
{
  "1": {"p_sell": 0.0234, "p_drop": 0.0156, "p_stagnation": 0.9610, "confidence": "low"},
  "3": {"p_sell": 0.0678, "p_drop": 0.0452, "p_stagnation": 0.8870, "confidence": "high"},
  "7": {"p_sell": 0.1456, "p_drop": 0.0971, "p_stagnation": 0.7573, "confidence": "high"}
}
```

---

## Phase 7 — UI integration (SPA)

Minimal: add a `P(sell)` pill to each flip row in the SPA table. Click expands to
show all 3 horizons with confidence flags.

**Data flow:** SPA → `GET /flipper/api.php?...` → BFF → `GET /api/analysis?flip_id=...`
(local) → analyze_flip().

Load lazily: only fetch analysis when user clicks a flip or expands a row. Don't
compute for all 144+ flips at once.

---

## Phase 8 — Tests

### 8.1 — `app/tests/test_analysis.py`

Minimal assert-based test (no framework):

```python
def _demo():
    """End-to-end: synthetic snapshots → P(sell≤7d) sanity check."""
    import tempfile, time
    from pathlib import Path
    
    # Set up temp DB with synthetic data
    # 10 snapshots over 7 days, 2 sellers disappear, 1 comes back
    # Verify: P(sell) > 0, P(drop) > 0, probabilities sum to 1
    # Verify: no data → returns None
    # Verify: 1 snapshot → returns None
    
    print("test_analysis._demo OK")
```

Run: `PYTHONPATH=app .venv/bin/python3 app/tests/test_analysis.py`

---

## Phase 9 — Calibration constants (tunable)

| Constant | Default | Where | Tune when |
|----------|---------|-------|-----------|
| `DEFAULT_PRIOR.sell` | `α=0.25, β=600` (0.01/d) | `prior.py` fallback chain | Results seem too optimistic/pessimistic before data accumulates |
| `DEFAULT_PRIOR.drop` | `α=0.1, β=600` (0.004/d) | `prior.py` fallback chain | Pricedrops seem over/underestimated early on |
| `epsilon_rel` | `1e-4` | `prior.py` guard 2 | Prior fits produce implausible alphas |
| `tau_decay` | `6h` | `survival.py` EWMA | Market-state correlation measured from data |
| Confidence threshold | `2×` last Δt | `survival.py` compute_cif | Too many "low" flags in practice |
| Min intervals for tier | `20` | `engine.py` fallback chain | Tier-level priors too noisy |
| 48h window | `48h` | `engine.py` seller reappearance | Market speed changes |

---

## Implementation order

1. Phase 1 (gatherer API) — 3 small changes, test with curl
2. Phase 2 (local mirror) — model after history.py, verify sync loop works
3. Phase 3 (event classification) — core logic, test with synthetic data
4. Phase 4 (Gamma prior) — pure math, test with synthetic rates
5. Phase 5 (posterior + CIF) — wire together with phases 3+4
6. Phase 6 (entry point + BFF) — integrate with API
7. Phase 7 (UI) — minimal pill, lazy load

---

# Post-implementation audit — known issues (2026-08-08)

Audited the shipped code (`app/pypoe/analysis/`) against the algorithm. Found
three issues plus a cold-start correction. Issues 1, 2, and 4 are **fixed**;
issue 3 is **deferred** (see its status). Kept here as a decision log.

## 1. `cheapest` scanned from all 7 days, not just the latest snapshot

**Location:** `__init__.py:101`

```python
cheapest = min(r["amount"] for r in rows)   # rows = all 7-day snapshots
```

If the cheapest was 3div 6 days ago but is 5div today, `min()` returns 3. That
stale value feeds both structural corrections:

- `my_queue_position(rows, 3)` → counts sellers at 3div in the *latest* snapshot
  → 0. The correct queue position is at today's 5div, where sellers may be
  ahead of you → λ_sell not divided → **P(sell) overestimated**.
- `downward_pressure_ratio(rows, 3)` → looks for new offers *below* 3div → none.
  Real new competition below today's 5div is invisible → **λ_drop suppressed**.

**Fix:** compute cheapest from the latest snapshot moment only:

```python
latest_ms = max(r["fetched_ms"] for r in rows)
cheapest = min(r["amount"] for r in rows if r["fetched_ms"] == latest_ms)
```

## 2. Downward-pressure ratio is time-blind

**Location:** `survival.py:72-85` (`downward_pressure_ratio`) + `_downward_flow_per_interval`

```python
recent = flows[-1]                    # e.g. 12 new cheap sellers in a 12h gap
mean_flow = sum(flows) / len(flows)   # e.g. 0.5 per ~2-min interval
return recent / mean_flow             # 12/0.5 = 24 → λ_drop × 24
```

`flows` are *per-snapshot* counts of newly-visible cheap sellers, not per-hour
rates. When intervals differ in length, a long interval naturally accumulates
more new entries → the ratio inflates (and short intervals deflate it).

**When it hurts:** slow flips (30-min cadence), missed syncs, Pi outages, and
the cold-start first interval all produce a long last gap → a one-cycle spike
that inflates λ_drop → `P(drop)` up, `P(sell)` down. Roughly-equal fast flips
(2-5 min) are near-1 and fine. Next cycle self-corrects (the long gap becomes
part of the historical mean).

**Fix:** normalize both sides by interval length → "new sellers per hour":

```python
# _downward_flow_per_interval returns (count, delta_hours) per interval
recent = flows[-1][0] / flows[-1][1]
mean_flow = sum(c / dt for c, dt in flows) / len(flows)
```

## 3. Item-level posterior uses full 7-day exposure, not a recent window

**Location:** `__init__.py:96` → `engine.exposure(events)` (7-day events)

Original algorithm step 5: item observations should come from a *recent*
window (last 48-72h), "to capture current market state without over-averaging
into the past." Shipped code passes the full 7-day `k`/`T_exposure`.

**Why it matters:** old sales keep inflating λ even when nothing happened
recently. The EWMA decay (`survival.ewma_lambda`) only discounts the staleness
of the *last snapshot*, not the *age of the events themselves* — a fresh
snapshot from 2 min ago gives full weight to 5-day-old event counts.

**Fix options (not decided):**
- (a) Filter events to `last 48-72h` by `now_ms` before `exposure()`
- (b) Time-decay k (exponential discount on older events)

**Status:** deferred — flagged in the algorithm's L3/L5 family of known biases;
low urgency given the market is slow. Revisit after real data accumulates.

## 4. Cold-start prior: inflated rate + zero-event cliff

**Location:** `engine.py collect_rates` + `prior.py fit_prior/_prior_from`

Two related cold-start bugs, both fixed 2026-08-08:

**4a. Sparse events inflated the pooled rate.** `collect_rates` averaged
`k_i/Δt_i` over *positive-event intervals only*, skipping the many zero-event
intervals. For a rare-event process this is wrong: 1 event in one 2h interval
yielded rate 0.5/h ≈ 12 sales/day. Zero intervals must be in the denominator
for the mean to recover the true rate. **Fixed:** every interval with `Δt > 0`
now contributes `k/Δt` (0.0 when nothing happened) → pooled mean is the true
events-per-hour rate.

**4b. Zero-event group → zero prior.** A group crossing the 20-interval
threshold with zero events fell through `_prior_from([])` → `Prior(mean=0.0)`
→ P(sell)=0 for every flip in the group — a cliff, not a cold start. **Fixed:**
`fit_prior` floors a zero-rate category at `DEFAULT_PRIOR` (conservative floor
instead of 0).

No redeploy of the gatherer needed — this is app-side analysis only. The
recrystallization is automatic: everything is recomputed from raw snapshots on
every poll (prior pool re-fits every 10 min), so newly-accumulated data
self-corrects the numbers without migration.

---

# Next up — prior vs data weight indicator (not implemented)

Requested 2026-08-08, deferred to next session.

**Goal:** surface how much of each P(sell)/P(drop) estimate comes from the
market prior vs. the item's own observed data, so the user can judge how much
a number is "real signal" vs "borrowed market average."

**Exact math (verified):** for a Gamma prior with parameters `(α, β)`, the
item posterior decomposes cleanly as a weighted blend:

```
λ_item = (α + k) / (β + T)
       = w_prior · (α/β)   +   w_data · (k/T)
where  w_prior = β / (β + T)        w_data = T / (β + T)
```

So the **data weight = T / (β + T)** — the item's exposure hours over its
exposure plus the prior's pseudo-exposure. Pure-Poisson prior (`prior.poisson`)
uses no item data → data weight = 0. No-item-data (T=0) → data weight = 0
(pure prior). The EWMA decay toward the prior (stale snapshot) additionally
reduces effective data weight by `exp(-Δt/τ)`.

**Where to surface it:**
- `survival.HorizonResult` — add a `data_weight` field (0..1, per horizon, or
  a single number per flip).
- `api.py /api/analysis` — include it in each horizon payload.
- SPA — show as a small marker on the pill (e.g. `≈` or a dot) or in the
  tooltip ("64% data / 36% prior").

**Planned shape (verify before implementing):** data weight for sell and drop
are computed separately (different priors); decide whether to report one
aggregate or both. `item_posterior` must also return the components or the
weight must be derived from the same inputs in `analyze_flip`.
