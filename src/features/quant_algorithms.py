import numpy as np
import pandas as pd
from typing import List, Dict, Union

def calculate_sma(data: List[float], window: int) -> List[float]:
    if len(data) < window:
        return [np.nan] * len(data)
    
    series = pd.Series(data)
    sma = series.rolling(window=window).mean()
    return sma.tolist()

def calculate_ema(data: List[float], window: int) -> List[float]:
    if len(data) < window:
        return [np.nan] * len(data)
    
    series = pd.Series(data)
    ema = series.ewm(span=window, adjust=False).mean()
    return ema.tolist()

def calculate_rsi(data: List[float], window: int = 14) -> List[float]:
    if len(data) < window:
        return [np.nan] * len(data)
        
    series = pd.Series(data)
    delta = series.diff()
    
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)

    roll_up1 = up.ewm(span=window, adjust=False).mean()
    roll_down1 = down.ewm(span=window, adjust=False).mean()

    rs = roll_up1 / roll_down1
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.tolist()

def calculate_macd(data: List[float], slow: int = 26, fast: int = 12, signal: int = 9) -> Dict[str, List[float]]:
    if len(data) < slow:
        nan_list = [np.nan] * len(data)
        return {"macd": nan_list, "signal": nan_list, "hist": nan_list}
        
    series = pd.Series(data)

    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()

    macd = exp1 - exp2

    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    
    return {
        "macd": macd.tolist(),
        "signal": signal_line.tolist(),
        "hist": hist.tolist()
    }

def calculate_bollinger_bands(data: List[float], window: int = 20, num_std: float = 2.0) -> Dict[str, List[float]]:
    if len(data) < window:
        nan_list = [np.nan] * len(data)
        return {"upper": nan_list, "mid": nan_list, "lower": nan_list}
        
    series = pd.Series(data)
    
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    return {
        "upper": upper_band.tolist(),
        "mid": sma.tolist(),
        "lower": lower_band.tolist()
    }

def simulate_recent_gamelog(base_value: float, games: int = 30, volatility: float = 0.15) -> List[float]:
    log = [base_value]

    for _ in range(games - 1):
        scale = abs(base_value * volatility)
        shock = np.random.normal(0, scale) if scale > 0 else 0

        current = log[-1]
        reversion = (base_value - current) * 0.2

        next_val = max(0.1, current + shock + reversion)
        log.append(next_val)

    return log

def extract_quant_features(gamelog: List[float]) -> Dict[str, float]:
    rsi_list = calculate_rsi(gamelog, window=14)
    macd_dict = calculate_macd(gamelog)
    bb_dict = calculate_bollinger_bands(gamelog, window=20)
    sma_list = calculate_sma(gamelog, window=10)

    latest_rsi = rsi_list[-1] if not np.isnan(rsi_list[-1]) else 50.0 
    latest_macd_hist = macd_dict['hist'][-1] if not np.isnan(macd_dict['hist'][-1]) else 0.0

    latest_val = gamelog[-1]
    bb_upper = bb_dict['upper'][-1]
    bb_lower = bb_dict['lower'][-1]
    
    bb_position = 0.5
    if not np.isnan(bb_upper) and not np.isnan(bb_lower) and (bb_upper - bb_lower) > 0:
        bb_position = (latest_val - bb_lower) / (bb_upper - bb_lower)
        
    return {
        "rsi": latest_rsi,
        "macd_hist": latest_macd_hist,
        "bb_position": bb_position,
        "recent_trend": (latest_val / sma_list[-1]) if not np.isnan(sma_list[-1]) and sma_list[-1] > 0 else 1.0
    }

def predict_future_performance(base_value: float, quant_features: Dict[str, float]) -> float:
    modifier = 1.0

    rsi = quant_features.get('rsi', 50.0)
    if rsi > 70:
        modifier *= 0.95
    elif rsi < 30:
        modifier *= 1.05

    macd_hist = quant_features.get('macd_hist', 0.0)
    if macd_hist > 0:
        modifier *= 1.02
    elif macd_hist < 0:
        modifier *= 0.98

    bb_pos = quant_features.get('bb_position', 0.5)
    if bb_pos > 1.0:
        modifier *= 1.03
    elif bb_pos < 0.0:
        modifier *= 0.97
        
    return base_value * modifier
