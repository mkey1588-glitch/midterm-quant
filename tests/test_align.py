import pandas as pd
import pytest

from midterm_quant.data import align


def _ohlc(s: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s, "volume": 1.0})


def test_inception_and_no_backfill_inside_history():
    cal = pd.bdate_range("2024-01-01", periods=10)
    raw = _ohlc(pd.Series([10.0, 11.0, 15.0], index=[cal[3], cal[4], cal[8]]))
    df, inc = align.align(raw, cal, ffill_limit=5)
    assert inc == cal[3]
    assert (df.loc[: cal[2], "close"] == 10.0).all()           # pre-inception placeholder
    assert (df.loc[cal[5]: cal[7], "close"] == 11.0).all()     # forward-filled, never 15
    assert df.loc[cal[8], "close"] == 15.0
    assert (df.loc[cal[5]: cal[7], "volume"] == 0.0).all()


def test_fred_publication_lag(monkeypatch):
    obs = pd.Series([1.0, 2.0, 3.0], index=pd.to_datetime(["2024-01-03", "2024-01-10", "2024-01-17"]))  # Wednesdays
    monkeypatch.setattr(align, "fetch_fred", lambda sid: obs)
    frame = align._fred_frame("fred:WALCL")  # 2 business-day lag -> usable Friday
    assert list(frame.index) == list(pd.to_datetime(["2024-01-05", "2024-01-12", "2024-01-19"]))
    cal = pd.bdate_range("2024-01-02", "2024-01-19")
    df, _ = align.align(frame, cal, ffill_limit=None)
    assert df.loc["2024-01-11", "close"] == 1.0  # Thursday still sees last week's print
    assert df.loc["2024-01-12", "close"] == 2.0


def test_unknown_calendar():
    with pytest.raises(ValueError):
        align.make_calendar("lunar", pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01"))
