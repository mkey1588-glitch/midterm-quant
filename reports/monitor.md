# Observation dashboard as of the 2026-11-05 close

Generated 2026-11-06T05:30:25+00:00. Each value is dated by the observation it describes; 'age' is days from that observation to 2026-11-05.

| Group | Code | Indicator | Value | Observation date | Age (d) | Status | Read | Context | Rule |
|---|---|---|---|---|---|---|---|---|---|
| Macro and policy | M1 | Economic policy uncertainty (30-day average) | 288 | 2026-11-04 | 1 | OK | **NEUTRAL** | z -0.49 vs 3 years | z > +1.5 STRESS; z < -0.5 CALM |
| Macro and policy | M2 | 10-year Treasury yield (FRED DGS10) | 4.90% | 2026-11-04 | 1 | OK | **NEUTRAL** | +27bp in 3 months | > 5.0% or +50bp in 63 days STRESS |
| Macro and policy | M3 | 10-year term premium (Kim-Wright) | 0.93% | 2026-10-29 | 7 | OK | **NEUTRAL** | 3-month change z +0.23 | z > +1.5 STRESS |
| Macro and policy | M4 | 2-year yield minus effective fed funds | +70bp | 2026-11-04 | 1 | OK | **HIGHER RATES PRICED** | effective fed funds 3.88% | > +25bp HIGHER RATES PRICED; < -50bp CUTS PRICED |
| Macro and policy | M5 | 10-year breakeven inflation | 2.26% | 2026-11-04 | 1 | OK | **NEUTRAL** | +4bp in 3 months | > 2.6% STRESS |
| Macro and policy | M6 | 10-year real yield (TIPS) | 2.64% | 2026-11-04 | 1 | OK | **HEADWIND** | +23bp in 3 months | > 2.5% and rising: gold HEADWIND |
| Macro and policy | M7 | Broad trade-weighted dollar | 121.7 | 2026-10-30 | 6 | OK | **STRONG USD** | +1.8% vs 200-day | above SMA200 STRONG USD |
| Macro and policy | M8 | 4-week minus 3-month bill yield | -18bp | 2026-11-04 | 1 | OK | **NEUTRAL** | 1-month vs 3-month bills | > +15bp X-DATE STRESS |
| Macro and policy | M9 | Fed net liquidity (same-Wednesday basis) | $5,730bn | 2026-10-28 | 8 | OK | **DRAINING** | -35bn over 13 weeks; TGA $1,016bn | 13-week change > 0 EXPANDING, < 0 DRAINING |
| Macro and policy | M10 | Credit risk-appetite proxy: HYG vs IEF | -2.15z | 2026-11-05 | 0 | OK | **STRESS** | high-yield ETF vs Treasuries | z < -1.5 STRESS |
| Macro and policy | M11 | High-yield option-adjusted spread (ICE BofA) | 332bp | 2026-11-04 | 1 | OK | **CALM** | +62bp in 3 months | >= 5.0pp or +1.0pp in 63 days STRESS; >= 4.0pp WATCH |
| Macro and policy | M12 | Fed funds futures: implied policy path | +38bp by Jun 2027 | 2026-11-04 | 1 | OK | **HIKES PRICED** | effective 3.88%; Dec-26 4.00%, Feb-27 4.08%, Apr-27 4.18%, Jun-27 4.26% | Jun-27 implied minus effective > +25bp HIKES PRICED; < -25bp CUTS PRICED |
| U.S. equities | E-a | S&P 500 trend | 7,354 | 2026-11-05 | 0 | OK | **RISK-ON** | +0.4% vs 200-day; -5.9% from 1-year high | below SMA200 RISK-OFF |
| U.S. equities | E-b | VIX term structure | 28.2 | 2026-11-05 | 0 | OK | **STRESS** | VIX/VIX3M 1.10 | > 1.0 STRESS; < 0.9 CALM |
| U.S. equities | E-c | Breadth: equal-weight vs cap-weight | +3.9% | 2026-11-05 | 0 | OK | **BROADENING** | equal- minus cap-weight, 63 days | > 0 BROADENING |
| U.S. equities | E-d | Small caps vs large caps | -4.9% | 2026-11-05 | 0 | OK | **NARROW** | small minus large, 63 days | > 0 BROADENING |
| U.S. equities | E-e | Semiconductor relative strength: SMH vs SPY | -18.2% | 2026-11-05 | 0 | OK | **SEMIS LAGGING** | semiconductors minus market, 63 days | < -5% SEMIS LAGGING |
| U.S. equities | E-f | Policy-sensitive sector baskets vs SPY | leader: health care | 2026-11-05 | 0 | OK | **INFO** | defence -13%, health care +17%, solar -11%, regional banks +0%, energy +13% | informational |
| U.S. equities | E-g | Midterm seasonal window and election clock | window day 35 | 2026-11-05 | 0 | OK | **IN WINDOW** | trading day 2 after election day 03 Nov 2026; window opened 01 Oct 2026 | 1 Oct midterm year - 31 Dec pre-election year IN WINDOW |
| Crypto | C-a | Bitcoin Mayer multiple | 1.10 | 2026-11-04 | 1 | STALE | **UPTREND** | BTC $80,405 (UTC bar 04 Nov), -24% from 1-year high | < 0.8 DEEP VALUE; > 2.4 EUPHORIC; else above/below 1 |
| Crypto | C-b | Bitcoin 30-day realised volatility | 32% | 2026-11-04 | 1 | STALE | **NEUTRAL** | annualised | > 70% STRESS |
| Crypto | C-c | ETH/BTC ratio | 0.0301 | 2026-11-04 | 1 | STALE | **BTC DOMINANCE** | +2% in 90 days | > +10% ALT-SEASON |
| Crypto | C-d | Crypto equity vs bitcoin: COIN vs BTC | -20.9% | 2026-11-04 | 1 | STALE | **CRYPTO EQUITY LAGS** | Coinbase minus bitcoin, 63 days | < -10% CRYPTO EQUITY LAGS |
| Crypto | C-e | Stablecoin supply: level and 30-day growth | $295bn | 2026-11-05 | 0 | OK | **OUTFLOW** | 30 days -4.3% (-13bn) | 30-day growth > 0 INFLOW |
| Crypto | C-f | Halving-cycle clock | ACCUMULATION | - | - | OK | **INFO** | 527 days to the estimated halving | phase by days since halving (in-sample boundaries) |
| Energy | N-a | Brent minus WTI (front-month futures) | $7.8 | 2026-11-05 | 0 | OK | **WIDE** | Brent $98.3, WTI $90.5; Brent +18% in 3 months | > $6 WIDE |
| Energy | N-b | Oil-fund roll proxy: USO vs USL | +6.2% | 2026-11-05 | 0 | OK | **FRONT OUTPERFORMING** | front-month fund minus 12-month strip, 63 days | > 0 FRONT OUTPERFORMING |
| Energy | N-f | WTI futures curve: 1st vs 12th contract | +$15.41 | 2026-11-05 | 0 | OK | **BACKWARDATION** | CLZ26 $90.52 vs CLX27 $75.11 (+17.0%) | > 0 BACKWARDATION; < 0 CONTANGO |
| Energy | N-c | U.S. retail gasoline price | $4.15 | 2026-11-02 | 3 | OK | **AFFORDABILITY PRESSURE** | higher than 87% of the past 2 years | > $4.00 or > 70th percentile AFFORDABILITY PRESSURE |
| Energy | N-d | Oil shock detector (USO 20-day return z) | -0.43 | 2026-11-05 | 0 | OK | **NORMAL** | vs a year of 20-day returns | > +2 SPIKE; < -2 CRASH |
| Energy | N-e | Clean vs fossil energy equities | -19.6% | 2026-11-05 | 0 | OK | **FOSSIL LEADS** | clean minus fossil, 63 days | > 0 CLEAN LEADS |
| Precious metals | P-a | Gold trend | $4,114 | 2026-11-05 | 0 | OK | **DOWNTREND** | -23% from high; -8.7% vs 200-day | below SMA200 DOWNTREND |
| Precious metals | P-b | Gold/silver ratio | 78.8 | 2026-11-05 | 0 | OK | **NEUTRAL** | z +0.05 vs 2 years | z > +1 SILVER CHEAP; z < -1 SILVER RICH |
| Precious metals | P-c | Gold/oil price ratio (input-cost proxy) | 45.4 | 2026-11-05 | 0 | OK | **COST HEADWIND** | -15% vs 200-day | above SMA200 COST TAILWIND |
| Precious metals | P-d | Miners vs bullion: GDX vs GLD | +1.2% | 2026-11-05 | 0 | OK | **CONFIRMING** | miners minus bullion, 63 days | > 0 CONFIRMING |
| Precious metals | P-e | Platinum/gold ratio | 0.371 | 2026-11-05 | 0 | OK | **PGM WEAK** | z -1.33 vs 1 year | z < -1 PGM WEAK |
