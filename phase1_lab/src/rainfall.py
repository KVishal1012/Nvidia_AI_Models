# Rainfall threshold and simple flood prediction logic
"""
rainfall.py

Simple rainfall-based flood risk classification for the Chennai Flood MVP.

Input:
- data/raw/chennai_rainfall.csv

Output:
- data/processed/rainfall_risk.csv

This is a beginner-friendly rule-based method.
No machine learning is used.
"""

import pandas as pd

from config import (
    RAINFALL_FILE,
    PROCESSED_DIR,
    RAINFALL_HIGH_RISK_MM_24H,
    RAINFALL_MEDIUM_RISK_MM_24H,
)


RAINFALL_RISK_FILE = PROCESSED_DIR / "rainfall_risk.csv"


def classify_rainfall_risk(rainfall_mm: float) -> str:
    """
    Classify flood risk based on 24-hour rainfall.

    Thresholds come from config.py:
    - High risk: rainfall >= RAINFALL_HIGH_RISK_MM_24H
    - Medium risk: rainfall >= RAINFALL_MEDIUM_RISK_MM_24H
    - Low risk: below medium threshold
    """
    if rainfall_mm >= RAINFALL_HIGH_RISK_MM_24H:
        return "high"
    elif rainfall_mm >= RAINFALL_MEDIUM_RISK_MM_24H:
        return "medium"
    else:
        return "low"


def add_risk_score(risk_level: str) -> int:
    """
    Convert text risk level into a simple numeric score.
    """
    scores = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    return scores.get(risk_level, 0)


def process_rainfall():
    """
    Read rainfall CSV, classify risk, and save processed output.
    """
    print(f"Reading rainfall data: {RAINFALL_FILE}")

    if not RAINFALL_FILE.exists():
        raise FileNotFoundError(f"Rainfall file not found: {RAINFALL_FILE}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    rainfall = pd.read_csv(RAINFALL_FILE)

    required_columns = {"date", "rainfall_mm_24h"}

    missing_columns = required_columns - set(rainfall.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    rainfall["risk_level"] = rainfall["rainfall_mm_24h"].apply(classify_rainfall_risk)
    rainfall["risk_score"] = rainfall["risk_level"].apply(add_risk_score)

    rainfall.to_csv(RAINFALL_RISK_FILE, index=False)

    print(f"Saved rainfall risk output: {RAINFALL_RISK_FILE}")
    print("\nRisk summary:")
    print(rainfall["risk_level"].value_counts())

    return rainfall


def main():
    process_rainfall()


if __name__ == "__main__":
    main()