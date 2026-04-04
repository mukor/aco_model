# ACO Model Roadmap

Game economic model for Animal Company mobile conversion.

## Phase 1: Retention Foundation (Complete)

- [x] Cohort-based retention simulation
- [x] Configurable retention curve (anchor-point interpolation: D1/D7/D30/D90 targets)
- [x] Daily install ingestion from data file
- [x] DAU calculation across stacked cohorts
- [x] Per-cohort tracking via SimResult (cohort matrix, individual cohort access)
- [x] CLI output with Rich tables
- [x] CSV export
- [x] Test suite (49 tests)

## Phase 2: Visualization & Exploration (Complete)

- [x] Jupyter notebook for interactive exploration (`notebooks/01_retention.ipynb`)
  - [x] Retention curve with interactive sliders (D1/D7/D30/D90)
  - [x] DAU simulation linked to sliders
  - [x] 365-day extended projection with actual vs projected shading
  - [x] D1 sensitivity analysis
  - [x] Cohort heatmap
- [x] Add matplotlib + jupyter as project dependencies
- [x] Monetization notebook (`notebooks/02_monetization.ipynb`)
  - [x] Revenue estimation with interactive sliders (% payers, ARPPU)
  - [x] ARPDAU, lifetime revenue per payer, cohort revenue
  - [x] Sensitivity analysis, combined DAU + revenue view
- [x] Shared state file (`output/state.json`) for cross-notebook communication
- [x] Hide Code toggle button, Save/Reset to Defaults buttons
- [ ] Notebook templates for common analyses

## Phase 3: Currency & Economy (In Progress)

> **Reference:** `animalco_economy.md` in brain-rag vault — currency definitions,
> taps/sinks, Battle Pass design, Key Card merging tiers.
> VR baseline data in `2026-03-25.md` daily note (pricing, LTV, ARPPU from Spatial).

### Answered questions
- [x] Key Card merge cost currency: **Nuts** (typo in notes corrected)
- [x] Battle Pass price: **5 Coins ($5)**
- [x] Instance runs per day: **3**
- [x] Key Card consumed per run: **yes, 1 per instance**
- [x] Battle Pass season length: **60 days**
- [x] Mobile pricing: **start with VR baseline** ($7 outfits, $15-$20 characters), tunable

### Still pending (waiting on Sienna / Stainless)
- [x] Specific Scrap/Nuts earn rates per instance tier (using placeholders)
- [ ] Additional Nut sinks beyond Key Cards
- [x] Item catalog and cost ranges
- [ ] Buff/upgrade tiers and Scrap costs

### Implementation
- [x] Currency models (Pydantic): InstanceTier, KeyCardTier, BattlePassParams, EconomyParams
- [x] Source/sink definitions per currency (Nuts, Scrap, Coins flows)
- [x] Per-instance currency flow: value-in vs value-out by tier
- [x] Key Card progression model (merge tree: bronze → vibranium, escalating Nut costs)
- [x] Battle Pass model: cost, season length, completion rate, breakeven analysis
- [x] Wallet balance tracking over time (per `2026-02-11_GameGou_call.md` recommendations)
- [x] Economy balance: cumulative Nuts/Scrap in system + avg per player
- [x] Notebook: `03_economy.ipynb` — 5 interactive sections with sliders
- [x] CLI: `aco economy` command with instance economics + keycard progression tables
- [x] Economy params in shared state file
- [x] Test suite: 23 economy tests (114 total)
- [ ] VR baseline comparison: model current VR metrics as a benchmark target
- [ ] Economy balance validation (inflation alerts when currencies accumulate too fast)

### Notebook Restructure (03_economy.ipynb)

New section order and changes:

#### Section 1: Resource Values & Exchange Rates (existing, extend)
- [x] Exchange rate table, resource value inputs, keycard cost grid, instance loot grid
- [x] Add **seeded currency inputs** — starting wallet for new players (coins, nuts, scrap given on install)
- [x] Add **XP** as an output in the Instance Loot table (XP earned per run, by tier)

> **Q: Seeded currency** — what currencies does a new player start with? Just coins? Nuts too? Approximate amounts?
>
The players should start with a a bit of everything. Let's create settable mounts of coins, nuts, and scrap. Let's start with default values of 5 coins, 1000 nuts, and 1000 scrap. I also would like these starting values be wired up to the 'Reset to Defaults' and 'Save to Defaults'. 

> **Q: XP per instance** — is XP earned per run a fixed amount by tier, or does it vary by quests/kills? For the model, should we use a flat avg XP per tier?
>
XP is earned two ways. Most of the XP is earned thought completing quests (think Fortnite).  These quests are broken up into daily, weekly, and battlepass season quests. The second ways is the runs themselves (kill mobs, achieving the goals of the instance). The instance based XP is going to scale up based on the instance tier (mobs are more difficult, intances have more challenging goals.)

With that said, we need an easy way to model they XP. Let's initially set an avg XP yield for each intance based on tier. The should be settable amounts that are wire up to our 'Reset to Defaults' to  'Save to Defults' 

#### Section 2: Wallet Balances (move up from section 3, rework)
- [x] Move to just below Resource Values & Exchange Rates (now "Player Wallet Progression")
- [x] Change subtitle to "Average player wallet balances after install"
- [x] X-axis = **player day** (days since install), not simulation day
- [x] One graph per currency (coins, nuts, scrap, XP) showing avg wallet balance over player days
- [x] Non-payer and BP holder variants shown side-by-side
- [x] Factor in seeded currency as the starting balance
- [x] Tier-up markers shown as vertical lines

> **Q: Wallet balance per player day** — should this model a single "average" player progressing through tiers over time? Or should it average across all active cohorts? The difference: a single-player view shows the progression journey, while the cohort-average flattens it because different players are at different tiers.
>
This model should be a single avg player progression through the tiers over time. We will then apply this to players in each cohort. Another thing that we have to take in account is the meta gets rest for each battlepass season. Currency balances are maintained, however XP and level goes back to 0. Let's assume the players don't hord key cards and they use them effencently to get to the next tier. They might have a few key cards left over after a season, but they aren't hording them.

> **Q: Tier progression pace** — for the single-player wallet model, how do we decide when a player moves up to the next instance tier? Options:
> a) As soon as they can afford the next keycard merge, they do it (greediest path)
> b) They run X instances at current tier before moving up (e.g., 10 runs per tier)
> c) Settable number of runs per tier
> Which approach? This determines how quickly nuts get spent on merges vs accumulating in the wallet.
>
Lets go with a) for now.

> **Q: Spending pattern for coins/scrap** — for the wallet balance model, should we assume the player spends coins on store items at some rate, or just model the earning side? Same for scrap — do they buff every run (current model) or some fraction of runs?
>
I think we assume that players that buy the battle pass are payers. Players who don't spend money on the battlepass are non-payers. So if we are talking about non-payers let's model the earning side.  Keep in mind we should balance things so non-payers can do the common and un-common tier instance, but after that they should stall a bit and really need to get the battle pass to get into the higher tiers.

**NOTE** There can be up to 4 players who enter an instance. They only need 1 keycard for the group. This might complicate things a bit from a modeling perspective. We can file this away to integrate later or tackle it now. My gut says to approach this later after we have QAed the model. In any case it should have a place on the roadmap.

#### Section 3: Total Economy Balance (rename from Currency Flows, move down)
- [x] Rename section to "Total Economy Balance"
- [x] Subtitle: "Total amount of currency in the system"
- [x] X-axis = **simulation day** (not player day)
- [x] Daily earned vs spent graph for each currency (coins, nuts, scrap)
- [x] Daily net balance graph for each currency
- [x] Summary text: total earned, total spent, current balance over full simulation

#### Section 4: Key Card Progression (rework)
- [x] Focus on: after how many instance runs can a player afford each keycard tier?
- [x] Show runs-to-afford and days-to-afford (based on runs/day setting)
- [x] Factor in nuts earned per run vs merge cost (uses player progression sim)

#### Section 5: Battle Pass Economics (extend)
- [x] BP cost (coins) — already settable
- [x] BP reward payouts (coins, nuts, scrap, keycards) — already settable
- [x] Add **total XP required to complete** the BP as settable input
- [x] Add **gear/weapons reward value** to BP payouts (item count × avg value)
- [x] Add **BP season days** as settable input (independent from sim_days)
- [x] Calculate **average payout per XP point** (total rewards / total XP)
- [x] Calculate **additional Value Out per instance run** for BP holders (BP reward rate × XP per run)
- [x] Spender profile analysis: low/medium/high runs/day completion times
- [x] XP earned in season vs required (delta)
- [x] Net payout to player (coins returned = coins spent)

> **Q: XP to complete BP** — do you have a target number? Or should we derive it from (season_days × runs_per_day × avg_xp_per_run × some_completion_factor)?
>
Let's make this a settable value for the entire battlepass and assume award thresholds are evently spaced. Let's also make a setable value for they number of days in the battlepass (start with 90 days as a placeholder).

Some of the things I want this section to analyze.
- compare the XP output of all the instance runs (assuming the player does it effienciently) during the battlepass season with the requried XP to complete the battlepass and show the delta.
- how long does it take avg player to complete the battle pass. ideally I would like the completion based on spender profiles (high, medium, low).
- This section should show the payout total and net payout of the battlepass. Keep in mind the player should get back all the coins (in the form of coin rewards) they spent to purchase the battlepass.

> **Q: BP gear rewards** — should gear value be a single USD total (like nuts/scrap), or broken into item counts × avg item value?
>
Let's start with breaking the rewards up into nuts/scrap/coins and gear with an average item value.

> **Q: Spender profiles for BP completion** — you mentioned high/medium/low. How should we define these? Some options:
> a) By runs per day: high=5+, medium=3, low=1-2
> b) By coin spend: high spenders buy keycards/bundles, low only buy BP
> c) Settable profiles with runs/day + coin budget
> Which dimensions matter most for the BP completion analysis?
>
b) I thinking by purchase spend ($). That said coin spend is a good proxy.

> **Q: BP season days vs sim days** — you said start with 90 days for BP season. Currently sim_days is also 90. Should the BP season always equal the sim length, or should they be independent? (e.g., sim 180 days showing players going through 2 BP seasons)
>
They should be independent. Maybe we should extend the sim length to 180 days (two seasons)

## Phase 3.1: Event Spec

Create an event specification for aco_economy telemetry. Output: `~/dev/aco_model/event_spec/event_spec.md`

An event spec defines all in-game events tracked to measure the Animal Company economy. Events are pushed to a data collector → ETL → data warehouse.

### Common Event Fields
Every event includes:
- `user_id` — unique player identifier
- `timestamp` — UTC datetime
- `platform` — ios / android / quest
- `event_type` — one of the types below
- `payload` — event-type-specific data (JSON)

### Event Types

#### `session`
Triggered on game login / logout.
- `session_id`, `action` (start/end), `duration_seconds` (on end)

#### `instance`
Triggered on instance start / complete.
- `instance_id`, `action` (start/complete), `tier` (common→legendary)
- `keycard_tier` (bronze→vibranium), `keycard_consumed` (bool)
- On complete: `nuts_earned`, `scrap_earned`, `coins_earned`, `xp_earned`
- On complete: `gear_drops` (list of {item_id, item_type, rarity, value_usd})
- On complete: `keycard_dropped` (bool), `buffs_used` (list of {buff_id, scrap_cost})

#### `store_purchase`
Triggered on IAP purchase.
- `transaction_id`, `item_id`, `item_type` (bundle/skin/coins/battle_pass)
- `price_usd`, `coins_spent` (if bought with in-game coins), `quantity`

#### `battle_pass`
Triggered on BP level up (XP threshold reached).
- `bp_season_id`, `level_reached`, `xp_total`
- `reward_type` (coins/nuts/scrap/keycard/gear), `reward_amount`, `reward_value_usd`

#### `buff`
Triggered when player applies a buff.
- `buff_id`, `item_id` (weapon/gear buffed), `buff_tier`
- `scrap_cost`, `buff_duration`, `buff_effect`

#### `merge`
Triggered when player merges keycards.
- `source_tier`, `target_tier`, `cards_consumed`, `nuts_cost`

> **Q: Are there other event types to consider?** Some possibilities:
> - `quest_complete` — if quests are separate from instances (your XP answer mentions daily/weekly/season quests — should these be their own events?)
> - `trade` — if players can trade items/currency
> - `loot_crate_open` — if crates are opened separately from instance completion
> - `login_reward` — daily login bonuses
> - `keycard_purchase` — buying keycards from the store (separate from merge)
>
quest_complete is good.
loot_create_open is good.
maybe we need a mob kill too.

> **Q: Should the event spec also define aggregate/derived metrics** (e.g., ARPDAU, LTV, funnel conversion rates) or just the raw events?
>
note now.

> **Q: Is there a preferred schema format?** (e.g., JSON Schema, protobuf-style, or just the markdown table format above?)
>
JSON

### Implementation (Complete)
- [x] Create `event_spec/` directory in project root
- [x] Write `event_spec/event_spec.md` with full event definitions
- [x] Include example JSON payloads for each event type
- [x] 9 event types: session, instance, store_purchase, battle_pass, buff, merge, quest_complete, loot_crate_open, mob_kill


## Phase 4: Session Modeling

- [ ] Session frequency per retention day
- [ ] Session duration curves
- [ ] Engagement depth (actions per session)
- [ ] Energy/stamina system modeling

## Phase 5: Advanced Monetization

> Basic monetization (% payers, ARPPU, ARPDAU, lifetime rev per payer) done in Phase 2.

- [ ] Player segmentation (non-payer, minnow, dolphin, whale)
- [ ] IAP conversion rates per segment
- [ ] Ad revenue modeling (rewarded, interstitial)
- [ ] LTV modeling by segment
- [ ] IAP catalog modeling (bundles, skins, Battle Pass — from VR pricing data in `2026-03-25.md`)

## Phase 6: Sensitivity Analysis

- [ ] Parameter sweep framework
- [ ] Monte Carlo simulation support
- [ ] Key metric dashboards (DAU, revenue, LTV, payback)
- [ ] Scenario comparison (optimistic/base/pessimistic)

## Phase 7: Interfaces

- [ ] Curses TUI for terminal dashboards
- [ ] FastAPI web interface for sharing results
- [ ] Interactive parameter controls
- [ ] Slack interface to spit out stats

## Phase 4.5: New user funnel
After first beta...
Simulate changes in the funnel falloff graph to show effect on D1 retention.

## Future Considerations

- **Group instance runs** — up to 4 players per instance, 1 keycard for the group. Drops effective keycard cost to 25% in a full group. Needs matchmaking assumptions.
- A/B test outcome modeling
- UA cost modeling and ROI/payback periods
- LiveOps event impact simulation
- Competitive benchmarking data ingestion
