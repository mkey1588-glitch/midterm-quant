# Observation dashboard (2026-11-06)

| Group | Code | Indicator | Value | Context | Read | Rule |
|---|---|---|---|---|---|---|
| Macro/Policy | M1 | Economic Policy Uncertainty (30d avg) | 294 | 3y z -0.43 | **NEUTRAL** | STRESS if 3y z > +1.5 |
| Macro/Policy | M2 | 10Y Treasury yield | 4.91% | 3m +21bp | **NEUTRAL** | STRESS if > 5.0% or +50bp/3m |
| Macro/Policy | M3 | 10Y term premium (Kim-Wright) | 0.91% | 3m chg z -0.05 | **NEUTRAL** | STRESS if 3m change z > +1.5 (fiscal/Fed-independence premium) |
| Macro/Policy | M4 | 2Y yield minus fed funds (implied path) | +71bp | FF 3.88% | **HIKES PRICED** | > +25bp = hikes priced; < -50bp = cuts priced |
| Macro/Policy | M5 | 10Y breakeven inflation | 2.30% | 3m +7bp | **NEUTRAL** | STRESS if > 2.6% (oil pass-through de-anchoring) |
| Macro/Policy | M6 | 10Y real yield (TIPS) | 2.62% | 3m +19bp | **HEADWIND** | Gold headwind if > 2.5% and rising |
| Macro/Policy | M7 | Broad trade-weighted dollar | 121.7 | vs 200d +1.8% | **STRONG USD** | Weak-USD regime if below 200d SMA |
| Macro/Policy | M8 | Bill curve: 4-week minus 3-month T-bill | -13bp | 1M vs 3M bills | **NEUTRAL** | Debt-limit X-date stress if > +15bp |
| Macro/Policy | M9 | Fed net liquidity (WALCL - TGA - RRP) | $5.75tn | 13w -80bn; TGA $1.00tn | **DRAIN** | Risk-on if 13w change > 0; TGA drawdown = pre-X-date injection |
| Macro/Policy | M10 | Credit: HYG/IEF 20d change | -2.15z | HY vs Treasuries | **STRESS** | STRESS if z < -1.5 |
| US Equities | E-a | S&P 500 trend / drawdown | 7,354 | vs 200d +0.4%, DD -5.9% | **RISK-ON** | Risk-off if below 200d SMA |
| US Equities | E-b | VIX and VIX/VIX3M | 28.1 | VIX/VIX3M 1.10 | **STRESS** | STRESS if ratio > 1.0 (inverted) |
| US Equities | E-c | Breadth: RSP vs SPY (63d) | +3.9% | equal- vs cap-weight | **BROADENING** | Broadening if > 0 |
| US Equities | E-d | Small caps: IWM vs SPY (63d) | -4.9% | small vs large | **NARROW** | Broadening if > 0 |
| US Equities | E-e | AI-infrastructure risk: SMH vs SPY (63d) | -18.2% | semis vs market | **DERATING** | Regulation-risk repricing if < -5% |
| US Equities | E-f | Policy baskets vs SPY (63d) | lead: health | defence -68%, health +17%, solar -11%, reg. banks +0%, energy +13% | **INFO** | Largest movers flag where policy is being priced |
| US Equities | E-g | Midterm-cycle clock | day 3 | since 2026-11-03 | **SWEET SPOT** | Seasonal sweet spot: Oct midterm yr -> Dec pre-election yr |
| Crypto | C-a | BTC Mayer multiple (price / 200d SMA) | 1.03 | BTC $75,738, DD -29% | **UPTREND** | < 0.8 historically deep value; > 2.4 euphoric |
| Crypto | C-b | BTC 30d realized vol | 38% | annualised | **NEUTRAL** | STRESS if > 70% |
| Crypto | C-c | ETH/BTC (90d change) | 0.0294 | 90d -0% | **BTC DOMINANCE** | Alt-season if > +10% and rising |
| Crypto | C-d | US regulatory sentiment: COIN vs BTC (63d) | -27.7% | Coinbase vs bitcoin | **REG HEADWIND** | Negative = US-specific regulatory discount widening |
| Crypto | C-e | Stablecoin supply (30d growth) | $295bn | 30d -4.0% | **OUTFLOW** | Liquidity inflow if > 0 |
| Crypto | C-f | Halving-cycle phase | ACCUMULATION | 526 days to est. halving | **INFO** | Next halving ~Apr 2028 (estimate) |
| Energy | N-a | Brent / WTI and spread | $98.4 / $90.5 | spread $7.9, Brent 3m +18% | **WAR PREMIUM** | War premium if Brent-WTI > $6 |
| Energy | N-b | Curve proxy: USO vs USL (63d) | +6.3% | front vs 12m strip | **BACKWARDATION** | Backwardation tightening if > 0 |
| Energy | N-c | US retail gasoline | $4.15 | 2y pct 87% | **POLITICAL PAIN** | Political pain if > $4.00 or top-30% of 2y |
| Energy | N-d | Oil 20d return z-score (USO) | -0.43 | vs 1y of 20d returns | **NORMAL** | Spike if > +2, crash if < -2 |
| Energy | N-e | Clean vs fossil: ICLN vs XLE (63d) | -19.7% | clean minus fossil | **FOSSIL LEADS** | Policy/rates rotation signal |
| Precious Metals | P-a | Gold price / drawdown | $4,094 | DD from ATH -23%, vs 200d -9.1% | **DOWNTREND** | Below 200d SMA = trend broken |
| Precious Metals | P-b | Gold/silver ratio | 79.1 | 2y z +0.07 | **NEUTRAL** | Silver cheap if 2y z > +1 |
| Precious Metals | P-c | Gold/oil ratio (miner margin proxy) | 45.2 | vs 200d -15% | **MARGINS SQUEEZED** | Miners favoured if above 200d SMA |
| Precious Metals | P-d | Miners vs bullion: GDX vs GLD (63d) | +1.2% | miners minus bullion | **CONFIRMING** | Confirms gold upleg if > 0 |
| Precious Metals | P-e | Platinum/gold ratio | 0.371 | 1y z -1.33 | **PGM WEAK** | Industrial-metal stress if 1y z < -1 |
