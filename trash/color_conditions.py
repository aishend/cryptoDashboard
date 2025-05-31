def rsi_color(rsi_value):
    if rsi_value < 30:
        return "green"
    elif rsi_value > 70:
        return "red"
    else:
        return "gray"

def macd_color(macd_value):
    if macd_value > 0:
        return "green"
    elif macd_value < 0:
        return "red"
    else:
        return "gray"

def macd_hist_color(hist_value, epsilon=0.01):
    if hist_value > epsilon:
        return "green"
    elif hist_value < -epsilon:
        return "red"
    else:
        return "gray"

def k_signal_color(k_signal_value, threshold=25):
    if k_signal_value < threshold:
        return "green"
    elif k_signal_value > threshold + 10:
        return "red"
    else:
        return "gray"

def macd_zero_lag_color(prev_macd, prev_signal, curr_macd, curr_signal):
    if prev_macd > prev_signal and curr_macd < curr_signal:
         return "red"
    elif prev_macd < prev_signal and curr_macd > curr_signal:
         return "green"
    else:
         return "green" if curr_macd > curr_signal else "red"
