import numpy as np
import pandas as pd
from typing import List, Dict, Union

def calculate_sma(data: List[float], window: int) -> List[float]:
    """
    Simple Moving Average (SMA).
    Averages the past 'window' periods.
    """
    if len(data) < window:
        return [np.nan] * len(data)
    
    series = pd.Series(data)
    sma = series.rolling(window=window).mean()
    return sma.tolist()

def calculate_ema(data: List[float], window: int) -> List[float]:
    """
    Exponential Moving Average (EMA).
    Gives more weight to recent data points.
    """
    if len(data) < window:
        return [np.nan] * len(data)
    
    series = pd.Series(data)
    ema = series.ewm(span=window, adjust=False).mean()
    return ema.tolist()

def calculate_rsi(data: List[float], window: int = 14) -> List[float]:
    """
    Relative Strength Index (RSI).
    Measures the speed and change of movements.
    Values > 70 generally indicate "Overbought" (overperforming/due to regress).
    Values < 30 generally indicate "Oversold" (underperforming/due to bounce back).
    """
    if len(data) < window:
        return [np.nan] * len(data)
        
    series = pd.Series(data)
    delta = series.diff()
    
    # Make two series: one for lower closes and one for higher closes
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Calculate the EWMA (Exponential Weighted Moving Average)
    roll_up1 = up.ewm(span=window, adjust=False).mean()
    roll_down1 = down.ewm(span=window, adjust=False).mean()
    
    # Calculate the RSI based on EWMA
    rs = roll_up1 / roll_down1
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.tolist()

def calculate_macd(data: List[float], slow: int = 26, fast: int = 12, signal: int = 9) -> Dict[str, List[float]]:
    """
    Moving Average Convergence Divergence (MACD).
    Shows the relationship between two moving averages of a series.
    Returns the MACD line, Signal line, and the Histogram (difference).
    """
    if len(data) < slow:
        nan_list = [np.nan] * len(data)
        return {"macd": nan_list, "signal": nan_list, "hist": nan_list}
        
    series = pd.Series(data)
    
    # Get the 12-day EMA and the 26-day EMA
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    
    # Calculate MACD
    macd = exp1 - exp2
    
    # Calculate Signal and Histogram
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    
    return {
        "macd": macd.tolist(),
        "signal": signal_line.tolist(),
        "hist": hist.tolist()
    }

def calculate_bollinger_bands(data: List[float], window: int = 20, num_std: float = 2.0) -> Dict[str, List[float]]:
    """
    Bollinger Bands.
    A set of trendlines plotted two standard deviations (positively and negatively) 
    away from a simple moving average (SMA) of a series.
    """
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
    """
    Simulates a time-series of game-by-game performances around a base average.
    Uses random walk with mean reversion to make it realistic.
    """
    # Start at base
    log = [base_value]
    
    for _ in range(games - 1):
        # Random shock
        scale = abs(base_value * volatility)
        shock = np.random.normal(0, scale) if scale > 0 else 0
        
        # Mean reversion (pulls back to base average)
        current = log[-1]
        reversion = (base_value - current) * 0.2
        
        next_val = max(0.1, current + shock + reversion) # Floor at 0.1
        log.append(next_val)
        
    return log

def extract_quant_features(gamelog: List[float]) -> Dict[str, float]:
    """
    Runs all indicators on a series and extracts the latest value as a feature dictionary.
    """
    if len(gamelog) < 26:
        # Not enough data for MACD, pad or mock if necessary in real usage
        pass
        
    rsi_list = calculate_rsi(gamelog, window=14)
    macd_dict = calculate_macd(gamelog)
    bb_dict = calculate_bollinger_bands(gamelog, window=20)
    sma_list = calculate_sma(gamelog, window=10)
    
    # Get the most recent valid values
    latest_rsi = rsi_list[-1] if not np.isnan(rsi_list[-1]) else 50.0 
    latest_macd_hist = macd_dict['hist'][-1] if not np.isnan(macd_dict['hist'][-1]) else 0.0
    
    # Bollinger Band Position (0 = at lower band, 1 = at upper band)
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
    """
    A Predictor algorithm.
    Takes the base estimated value and modifies it based on quant indicators.
    """
    modifier = 1.0
    
    # 1. RSI Logic (Mean Reversion)
    # If RSI > 70 (Overbought), player is likely overperforming and will regress downwards
    # If RSI < 30 (Oversold), player is likely underperforming and will regress upwards (buy low)
    rsi = quant_features.get('rsi', 50.0)
    if rsi > 70:
        modifier *= 0.95 # 5% penalty for unsustainable hot streak
    elif rsi < 30:
        modifier *= 1.05 # 5% bonus for positive regression
        
    # 2. MACD Logic (Momentum)
    # Positive histogram means accelerating upward momentum
    macd_hist = quant_features.get('macd_hist', 0.0)
    if macd_hist > 0:
        modifier *= 1.02 # Small momentum bonus
    elif macd_hist < 0:
        modifier *= 0.98 # Small momentum penalty
        
    # 3. Bollinger Band Breakout
    # Values heavily outside bands imply trend shifts
    bb_pos = quant_features.get('bb_position', 0.5)
    if bb_pos > 1.0: # Breakout above upper band
        modifier *= 1.03
    elif bb_pos < 0.0: # Breakdown below lower band
        modifier *= 0.97
        
    return base_value * modifier
