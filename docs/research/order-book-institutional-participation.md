<!--
Source: Claude Docs "Tracking Institutional Participation with Order-Book Data"
        https://claude.ai/artifact/7wkRXk4N19Mrd73Do3aoDv (rev 7, 2026-10-17). Imported 2026-11-01 as Markdown.
Canonical copy is this file. Its proposal was adopted in spec v8 (Section 11.6, Momentum Quality).
-->

# Tracking Institutional Participation with Order-Book Data

Oct 17, 2026 · @Rahil Khan

## Summary

The current spec does not track order-count and order-size signals explicitly. The data needed for a good approximation already comes through the broker feed the spec uses, so expensive order-level data is not required for this.

## What broker depth data already shows

Indian broker APIs provide market depth (Level 2) with both the **total quantity** and the **number of orders** at each of the top price levels. Dividing quantity by orders gives the **average order size** on each side.

| Side | Quantity (shares) | Orders | Average order size (shares) |
| --- | --- | --- | --- |
| Bids (buyers) | 50,000 | 8 | \~6,250 |
| Asks (sellers) | 48,000 | 210 | \~230 |

A few large buy orders against many small sell orders suggests large participants accumulating while small sellers supply shares. The reverse pattern suggests large holders distributing to retail buyers.

The spec's current `get_order_book_imbalance` tool measures quantity imbalance only. It does not compute order counts, average order size, or how these change over time.

## Limitations

The signal is **suggestive, not proof**. It becomes reliable only when it persists across many snapshots and days and is confirmed by other evidence.

- **Orders are not buyers.** The feed is anonymous: one institution may appear as many orders, and several small traders may post large ones.
- **Institutions hide their size.** Their algorithms split large orders into many small ones, so they can look like retail flow.
- **Disclosed quantity.** NSE allows orders that show less than their real quantity, so the visible book can understate large interest.
- **Only waiting orders are visible.** Depth shows resting orders in the top few levels, not executed trades; much institutional buying executes immediately and never appears in the book.
- **Large visible orders can be fake.** Orders placed to impress and then cancelled are the spoofing pattern.
- **Snapshots miss activity in between.** Broker feeds refresh periodically, so short-lived orders can go unseen.

## How the system could track it

The Market Data Gateway would record depth snapshots for held and watchlisted stocks. A deterministic job would compute these indicators:

| Indicator | What it measures | Why it matters |
| --- | --- | --- |
| Average order size | Quantity per order on each side, against the stock's own normal range | Absolute sizes differ hugely between a large bank and a small-cap |
| Order concentration | Quantity per order on bids vs. asks | Few large buyers vs. many small sellers, or the reverse |
| Persistence | Whether large orders stay and get filled, or keep vanishing without trades | Vanishing orders are a possible spoofing sign |
| Large-trade estimates | Unusually large trades inferred from volume changes between snapshots, and whether they hit the ask or the bid | Buyer- vs. seller-initiated pressure |
| Daily summaries | All of the above aggregated per stock per day | Patterns over days and weeks, not minutes |

These indicators are then **cross-checked** against signals that identify institutions more directly:

- Rising delivery percentage
- Bulk and block deals with disclosed buyers and sellers
- FII and DII positioning in participant-wise open interest
- Monthly mutual fund holdings
- Quarterly shareholding changes

When the order-book pattern and the disclosed data agree, the evidence of institutional accumulation or distribution is fairly strong.

## Would full order-level data add much?

Somewhat, but not enough to justify it yet. Order-level data shows every order's arrival and cancellation, so slicing and spoofing are clearer. It is still anonymous, so it cannot show who is buying.

The snapshot approach captures much of the value at a fraction of the cost. Paper-trading results will show whether a deeper feed is worth paying for later.

## Proposed next step: a Momentum Quality module

Add a **Momentum Quality** module to the spec. It would combine the order-book participation indicators above with delivery, deal, participant open interest, and shareholding signals. Its score would classify each price move as one of four types:

- Likely accumulation
- Likely distribution
- Short covering
- Speculative churn
