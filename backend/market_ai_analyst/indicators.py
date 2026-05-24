"""CryptoGhost - Indicadores técnicos avançados."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
except ImportError:
    ta = None


@dataclass
class TechnicalIndicatorSet:
    rsi: float
    macd: float
    macd_signal: float
    macd_hist: float
    ema_12: float
    ema_26: float
    sma_20: float
    sma_50: float
    vwap: float
    bb_upper: float
    bb_lower: float
    bb_mid: float
    atr: float
    obv: float
    fib_382: float
    fib_618: float
    support: float
    resistance: float
    volume_ratio: float
    momentum: float


class TechnicalIndicators:
    """Calcula indicadores técnicos usando pandas-ta e numpy."""

    @staticmethod
    def compute(df: pd.DataFrame) -> TechnicalIndicatorSet:
        df = df.copy()
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)
        volume = df["volume"].astype(float)

        if ta is not None and len(df) >= 30:
            df.ta.rsi(length=14, append=True)
            df.ta.macd(append=True)
            df.ta.ema(length=12, append=True)
            df.ta.ema(length=26, append=True)
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.vwap(append=True)
            df.ta.bbands(length=20, append=True)
            df.ta.atr(length=14, append=True)
            df.ta.obv(append=True)

            last = df.iloc[-1]
            rsi = float(last.get("RSI_14", 50))
            macd = float(last.get("MACD_12_26_9", 0))
            macd_signal = float(last.get("MACDs_12_26_9", 0))
            macd_hist = float(last.get("MACDh_12_26_9", 0))
            ema_12 = float(last.get("EMA_12", close.iloc[-1]))
            ema_26 = float(last.get("EMA_26", close.iloc[-1]))
            sma_20 = float(last.get("SMA_20", close.iloc[-1]))
            sma_50 = float(last.get("SMA_50", close.iloc[-1]))
            vwap = float(last.get("VWAP_D", close.iloc[-1]))
            bb_upper = float(last.get("BBU_20_2.0", close.iloc[-1] * 1.02))
            bb_lower = float(last.get("BBL_20_2.0", close.iloc[-1] * 0.98))
            bb_mid = float(last.get("BBM_20_2.0", close.iloc[-1]))
            atr = float(last.get("ATRr_14", close.iloc[-1] * 0.01))
            obv = float(last.get("OBV", volume.sum()))
        else:
            rsi = TechnicalIndicators._rsi(close)
            ema_12 = float(close.ewm(span=12).mean().iloc[-1])
            ema_26 = float(close.ewm(span=26).mean().iloc[-1])
            macd = ema_12 - ema_26
            macd_signal = float((close.ewm(span=12).mean() - close.ewm(span=26).mean()).ewm(span=9).mean().iloc[-1])
            macd_hist = macd - macd_signal
            sma_20 = float(close.rolling(min(20, len(close))).mean().iloc[-1])
            sma_50 = float(close.rolling(min(50, len(close))).mean().iloc[-1])
            vwap = float((close * volume).sum() / max(volume.sum(), 1))
            std = close.rolling(min(20, len(close))).std().iloc[-1] or close.iloc[-1] * 0.01
            bb_mid = sma_20
            bb_upper = sma_20 + 2 * std
            bb_lower = sma_20 - 2 * std
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr = float(tr.rolling(min(14, len(tr))).mean().iloc[-1])
            obv = float((np.sign(close.diff()) * volume).fillna(0).cumsum().iloc[-1])

        swing_high = float(high.tail(50).max())
        swing_low = float(low.tail(50).min())
        diff = swing_high - swing_low
        fib_382 = swing_high - diff * 0.382
        fib_618 = swing_high - diff * 0.618
        support = float(low.tail(20).min())
        resistance = float(high.tail(20).max())
        vol_avg = float(volume.tail(20).mean()) or 1
        volume_ratio = float(volume.iloc[-1] / vol_avg)
        momentum = float((close.iloc[-1] / close.iloc[-min(10, len(close))] - 1) * 100)

        return TechnicalIndicatorSet(
            rsi=rsi, macd=macd, macd_signal=macd_signal, macd_hist=macd_hist,
            ema_12=ema_12, ema_26=ema_26, sma_20=sma_20, sma_50=sma_50,
            vwap=vwap, bb_upper=bb_upper, bb_lower=bb_lower, bb_mid=bb_mid,
            atr=atr, obv=obv, fib_382=fib_382, fib_618=fib_618,
            support=support, resistance=resistance, volume_ratio=volume_ratio, momentum=momentum,
        )

    @staticmethod
    def _rsi(close: pd.Series, period: int = 14) -> float:
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
        rs = gain / loss.replace(0, 1e-10)
        return float(100 - (100 / (1 + rs.iloc[-1]))) if len(close) >= period else 50.0

    @staticmethod
    def to_dict(indicators: TechnicalIndicatorSet) -> dict:
        return {
            "rsi": round(indicators.rsi, 2),
            "macd": round(indicators.macd, 4),
            "macd_signal": round(indicators.macd_signal, 4),
            "ema_12": round(indicators.ema_12, 2),
            "ema_26": round(indicators.ema_26, 2),
            "sma_20": round(indicators.sma_20, 2),
            "sma_50": round(indicators.sma_50, 2),
            "vwap": round(indicators.vwap, 2),
            "bb_upper": round(indicators.bb_upper, 2),
            "bb_lower": round(indicators.bb_lower, 2),
            "atr": round(indicators.atr, 4),
            "obv": round(indicators.obv, 2),
            "fib_382": round(indicators.fib_382, 2),
            "fib_618": round(indicators.fib_618, 2),
            "support": round(indicators.support, 2),
            "resistance": round(indicators.resistance, 2),
            "volume_ratio": round(indicators.volume_ratio, 2),
            "momentum": round(indicators.momentum, 2),
        }
