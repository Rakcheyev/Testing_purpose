import os
import pandas as pd
import requests
from typing import List, Dict, Any

# --- Excel/CSV Parsing ---
def parse_excel(file_path: str) -> pd.DataFrame:
    """Parse Excel file and return DataFrame."""
    return pd.read_excel(file_path)

def parse_csv(file_path: str) -> pd.DataFrame:
    """Parse CSV file and return DataFrame."""
    return pd.read_csv(file_path)

# --- API Parsing ---
def fetch_api(url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> Any:
    """Fetch data from API and return JSON."""
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# --- Validation ---
def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
    """Validate DataFrame for required columns and return result."""
    missing = [col for col in required_columns if col not in df.columns]
    return {
        "valid": len(missing) == 0,
        "missing_columns": missing,
        "columns": list(df.columns)
    }

# --- Example Usage ---
if __name__ == "__main__":
    # Example: Parse and validate Excel
    excel_path = "example.xlsx"
    required_cols = ["id", "name", "value"]
    if os.path.exists(excel_path):
        df = parse_excel(excel_path)
        result = validate_dataframe(df, required_cols)
        print(f"Excel validation: {result}")

    # Example: Parse and validate CSV
    csv_path = "example.csv"
    if os.path.exists(csv_path):
        df = parse_csv(csv_path)
        result = validate_dataframe(df, required_cols)
        print(f"CSV validation: {result}")

    # Example: Fetch and validate API
    api_url = "https://api.example.com/data"
    try:
        data = fetch_api(api_url)
        # If API returns tabular data, convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
            result = validate_dataframe(df, required_cols)
            print(f"API validation: {result}")
    except Exception as e:
        print(f"API fetch error: {e}")
