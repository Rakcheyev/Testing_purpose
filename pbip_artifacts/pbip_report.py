import json
from typing import Dict, Any

def generate_report(result: Dict[str, Any], out_path: str):
    """Save validation report as JSON."""
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
