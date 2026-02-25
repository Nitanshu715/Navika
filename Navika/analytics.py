import numpy as np

def detect_anomalies(transactions):
    if len(transactions) < 5:
        return []

    amounts = [tx["amount"] for tx in transactions]
    mean = np.mean(amounts)
    std = np.std(amounts)

    anomalies = [
        tx for tx in transactions
        if abs(tx["amount"] - mean) > 2 * std
    ]

    return anomalies