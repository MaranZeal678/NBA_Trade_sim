# NBA Trade Simulator

This project simulates NBA trade deadline decisions. It tries to value players, classify teams as buyers or sellers, build trade packages, and reject trades that fail simplified CBA salary matching rules.

## Main Flow

`run_simulation.py` loads live NBA data when `nba_api` works. If that import or fetch fails, it uses the included mock league so the simulator can still run locally.

The engine then:

1. Assigns each team a strategy from its win percentage.
2. Values every player with a stats and age based formula.
3. Randomly samples buyer and seller pairs.
4. Builds a salary matching package from the buyer.
5. Adds a draft pick if the value gap is large enough.
6. Checks CBA legality.
7. Keeps trades where both teams have positive utility.

## Player Value Math

The value model starts with an efficiency estimate.

```text
marginal_efficiency = max(efficiency - replacement_level, 0)
base_value = marginal_efficiency * dollars_per_efficiency_point
```

It then creates a fake 30 game performance log around that base number. The quant indicators are calculated from that log:

- SMA and EMA smooth recent games.
- RSI checks if a player is probably running too hot or too cold.
- MACD checks short term momentum against longer trend.
- Bollinger Bands check whether the latest value is outside the normal range.

The final value is adjusted by the quant signals and age.

```text
value = quant_adjusted_base * age_multiplier + 2,000,000
```

Young players get a larger multiplier. Older players get a discount. Values are capped between 2 million and 65 million.

## Team Strategy

Teams are assigned simple modes:

```text
win_pct > 0.45  -> BUYER
win_pct < 0.35  -> SELLER
otherwise       -> HOLD
```

## Trade Utility

Buyer utility favors current player value.

```text
buyer_utility = (value_in - value_out) * 1.5
              + (future_value_in - future_value_out) * 0.2
```

Seller utility favors picks and salary savings.

```text
seller_utility = (future_value_in - future_value_out) * 1.5
               - salary_change * 0.1
```

A trade is only returned if both utilities are positive.

## Salary Matching

The CBA check is simplified:

- Second apron teams cannot aggregate multiple outgoing players.
- Second apron teams cannot take back more salary than they send.
- First apron and tax teams use a 110 percent plus 100k limit.
- Other teams use a 125 percent plus 250k limit.
- Future first round picks cannot be consecutive.

## Running

```bash
python run_simulation.py
```

The fallback mock data path only needs the local Python source plus the numeric packages used by the value model.
