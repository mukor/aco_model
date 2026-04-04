# Animal Company Event Specification

Taxonomy of in-game telemetry events for the Animal Company economy.

## Overview

Events flow through this pipeline:

```
Game Client → Event Collector → ETL Pipeline → Data Warehouse
```

Every player action that affects the economy or is useful for analytics generates an event.
Events are buffered client-side and batched to the collector to minimize network overhead.

All events share a common envelope (user_id, timestamp, platform, event_type, session_id)
and include an event-type-specific `payload` object.

## Common Fields

Every event has these fields at the top level:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | yes | Unique player identifier (UUID) |
| `timestamp` | string (ISO 8601) | yes | UTC datetime when the event occurred on the client |
| `platform` | enum | yes | One of: `ios`, `android`, `quest` |
| `event_type` | string | yes | One of the event types defined below |
| `session_id` | string | yes | Current session ID (UUID) |
| `payload` | object | yes | Event-type-specific data |

### Envelope Example

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-01T14:32:15Z",
  "platform": "ios",
  "event_type": "instance",
  "session_id": "a7f3b2c1-9d8e-4f6a-b5c3-1e2d3f4a5b6c",
  "payload": { /* event-specific */ }
}
```

---

## Event Types

### 1. `session`

Triggered when a player logs in or out of the game.

**Fires on:** game start, game end/timeout.

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | enum | yes | `start` or `end` |
| `duration_seconds` | integer | on end | Session length in seconds |
| `device_model` | string | yes | Device model (e.g. "iPhone14,3") |
| `os_version` | string | yes | OS version (e.g. "17.4.1") |
| `app_version` | string | yes | Game client version (e.g. "1.2.3") |

**Example (session end):**

```json
{
  "action": "end",
  "duration_seconds": 1847,
  "device_model": "iPhone14,3",
  "os_version": "17.4.1",
  "app_version": "1.2.3"
}
```

---

### 2. `instance`

Triggered when a player starts or completes an instance run.

**Fires on:** instance entry (start), instance completion/failure (complete).

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instance_id` | string | yes | Unique ID for this instance run |
| `action` | enum | yes | `start` or `complete` |
| `tier` | enum | yes | `common`, `uncommon`, `rare`, `epic`, `legendary` |
| `keycard_tier` | enum | yes | `bronze`, `silver`, `gold`, `mithril`, `vibranium` |
| `keycard_consumed` | boolean | yes | Whether the keycard was used (group leader) |
| `group_size` | integer (1-4) | yes | Number of players in the instance |
| `nuts_earned` | number | on complete | Nuts awarded on completion |
| `scrap_earned` | number | on complete | Scrap awarded on completion |
| `coins_earned` | number | on complete | Coins awarded on completion |
| `xp_earned` | number | on complete | XP awarded on completion |
| `gear_drops` | array | on complete | List of gear items dropped |
| `keycard_dropped` | boolean | on complete | Whether a keycard was returned |
| `buffs_used` | array | on complete | List of buffs consumed during the run |
| `duration_seconds` | integer | on complete | Run duration |
| `success` | boolean | on complete | Whether the instance was completed successfully |

**`gear_drops[]` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | string | Catalog ID of the item |
| `item_type` | enum | `weapon`, `outfit`, `skin`, `accessory` |
| `rarity` | enum | `common`, `uncommon`, `rare`, `epic`, `legendary` |
| `value_usd` | number | Approximate USD value |

**`buffs_used[]` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `buff_id` | string | Catalog ID of the buff |
| `scrap_cost` | number | Scrap spent on this buff |

**Example (instance complete):**

```json
{
  "instance_id": "inst_8b3c2a1f",
  "action": "complete",
  "tier": "rare",
  "keycard_tier": "gold",
  "keycard_consumed": true,
  "group_size": 3,
  "nuts_earned": 100,
  "scrap_earned": 175,
  "coins_earned": 2.0,
  "xp_earned": 120,
  "gear_drops": [
    {"item_id": "weapon_rifle_v3", "item_type": "weapon", "rarity": "rare", "value_usd": 0.75}
  ],
  "keycard_dropped": false,
  "buffs_used": [
    {"buff_id": "buff_dmg_tier1", "scrap_cost": 50}
  ],
  "duration_seconds": 480,
  "success": true
}
```

---

### 3. `store_purchase`

Triggered on any IAP transaction (real money or in-game coins).

**Fires on:** successful purchase confirmation.

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transaction_id` | string | yes | Platform transaction ID |
| `item_id` | string | yes | Catalog ID of the purchased item |
| `item_type` | enum | yes | `bundle`, `skin`, `coins`, `battle_pass`, `keycard` |
| `price_usd` | number | yes | USD price paid (0 if bought with coins) |
| `coins_spent` | number | yes | In-game coins spent (0 if bought with real money) |
| `quantity` | integer | yes | Number of items purchased |
| `store` | enum | yes | `apple`, `google`, `meta` |

**Example (IAP bundle):**

```json
{
  "transaction_id": "GPA.1234-5678-9012-34567",
  "item_id": "bundle_starter_pack",
  "item_type": "bundle",
  "price_usd": 9.99,
  "coins_spent": 0,
  "quantity": 1,
  "store": "google"
}
```

**Example (coin purchase of skin):**

```json
{
  "transaction_id": "internal_a1b2c3d4",
  "item_id": "skin_panda_warrior",
  "item_type": "skin",
  "price_usd": 0,
  "coins_spent": 15,
  "quantity": 1,
  "store": "apple"
}
```

---

### 4. `battle_pass`

Triggered when a player crosses an XP threshold and levels up in the Battle Pass.

**Fires on:** BP level-up (reward unlock).

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bp_season_id` | string | yes | Identifier for the BP season |
| `level_reached` | integer | yes | Level number achieved |
| `xp_total` | number | yes | Player's cumulative XP this season |
| `xp_for_level` | number | yes | XP threshold for this level |
| `reward_type` | enum | yes | `coins`, `nuts`, `scrap`, `keycard`, `gear` |
| `reward_amount` | number | yes | Quantity of the reward |
| `reward_item_id` | string | if gear | Catalog ID (for gear rewards) |
| `reward_value_usd` | number | yes | Estimated USD value of the reward |

**Example:**

```json
{
  "bp_season_id": "s2026_q2",
  "level_reached": 15,
  "xp_total": 7500,
  "xp_for_level": 7500,
  "reward_type": "gear",
  "reward_amount": 1,
  "reward_item_id": "weapon_sniper_epic",
  "reward_value_usd": 3.00
}
```

---

### 5. `buff`

Triggered when a player applies a buff to a weapon or piece of gear.

**Fires on:** buff application (scrap spend confirmed).

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `buff_id` | string | yes | Catalog ID of the buff |
| `item_id` | string | yes | Catalog ID of the weapon/gear being buffed |
| `buff_tier` | enum | yes | `common`, `uncommon`, `rare`, `epic`, `legendary` |
| `scrap_cost` | number | yes | Scrap spent |
| `buff_effect` | string | yes | Human-readable effect (e.g. "damage +15%") |

**Example:**

```json
{
  "buff_id": "buff_reload_t2",
  "item_id": "weapon_rifle_v3",
  "buff_tier": "uncommon",
  "scrap_cost": 75,
  "buff_effect": "reload_speed +20%"
}
```

---

### 6. `merge`

Triggered when a player merges lower-tier keycards into a higher tier.

**Fires on:** successful keycard merge.

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_tier` | enum | yes | Keycard tier being consumed (e.g. `bronze`) |
| `target_tier` | enum | yes | Keycard tier being created (e.g. `silver`) |
| `cards_consumed` | integer | yes | Number of source-tier cards used |
| `nuts_cost` | number | yes | Nuts spent on the merge |

**Example:**

```json
{
  "source_tier": "silver",
  "target_tier": "gold",
  "cards_consumed": 4,
  "nuts_cost": 200
}
```

---

### 7. `quest_complete`

Triggered when a player completes a quest. Quests are a major XP source.

**Fires on:** quest objective met.

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quest_id` | string | yes | Catalog ID of the quest |
| `quest_type` | enum | yes | `daily`, `weekly`, `season` |
| `xp_earned` | number | yes | XP awarded |
| `rewards` | array | yes | List of additional rewards |

**`rewards[]` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | enum | `coins`, `nuts`, `scrap`, `keycard`, `gear` |
| `amount` | number | Quantity of the reward |

**Example:**

```json
{
  "quest_id": "daily_kill_50_mobs",
  "quest_type": "daily",
  "xp_earned": 200,
  "rewards": [
    {"type": "nuts", "amount": 100},
    {"type": "scrap", "amount": 50}
  ]
}
```

---

### 8. `loot_crate_open`

Triggered when a player opens a loot crate. Crates come from instances, BP, or store purchases.

**Fires on:** crate open animation start (reward resolved).

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `crate_id` | string | yes | Unique ID of the crate instance |
| `crate_tier` | enum | yes | `common`, `uncommon`, `rare`, `epic`, `legendary` |
| `source` | enum | yes | `instance`, `battle_pass`, `store`, `login_reward` |
| `contents` | array | yes | List of items received |

**`contents[]` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `item_type` | enum | `coins`, `nuts`, `scrap`, `keycard`, `gear` |
| `item_id` | string | Catalog ID (empty for fungible currencies) |
| `quantity` | number | Number of items or currency amount |
| `value_usd` | number | Estimated USD value |

**Example:**

```json
{
  "crate_id": "crate_7x9y2z",
  "crate_tier": "epic",
  "source": "instance",
  "contents": [
    {"item_type": "nuts", "item_id": "", "quantity": 150, "value_usd": 1.50},
    {"item_type": "gear", "item_id": "outfit_ninja_epic", "quantity": 1, "value_usd": 2.00}
  ]
}
```

---

### 9. `mob_kill`

Triggered when a player kills a mob during an instance.

**Fires on:** mob death (credit assigned to this player).

**Payload schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instance_id` | string | yes | ID of the instance this kill happened in |
| `mob_id` | string | yes | Unique instance ID of this mob |
| `mob_type` | string | yes | Catalog type (e.g. "grunt", "boss_alpha") |
| `mob_tier` | enum | yes | `common`, `uncommon`, `rare`, `epic`, `legendary` |
| `xp_earned` | number | yes | XP awarded for the kill |
| `drops` | array | yes | Items/currency dropped |

**`drops[]` item schema:**

| Field | Type | Description |
|-------|------|-------------|
| `item_type` | enum | `nuts`, `scrap`, `coins`, `gear` |
| `quantity` | number | Quantity dropped |

**Example:**

```json
{
  "instance_id": "inst_8b3c2a1f",
  "mob_id": "mob_9x2k4l",
  "mob_type": "grunt",
  "mob_tier": "rare",
  "xp_earned": 15,
  "drops": [
    {"item_type": "scrap", "quantity": 5}
  ]
}
```

---

## Implementation Notes

### Event Buffering & Delivery
- Buffer events client-side; batch upload every 30 seconds or on session end
- Retry failed batches with exponential backoff
- Persist buffer to disk to survive app crashes

### Timestamping
- Always use client-side UTC timestamps for `timestamp`
- Server should record `received_at` separately to detect clock skew

### Schema Versioning
- Include `event_version` in the envelope when schema changes are introduced
- Initial version: `v1`

### Privacy & PII
- `user_id` should be a stable anonymous UUID, not tied to PII
- Do not log email, real names, or payment details in events

### Data Warehouse Partitioning
- Partition by `event_type` and `date(timestamp)` for efficient querying

### Testing
- All events should pass JSON Schema validation before leaving the client
- Staging environment with live event debugging
