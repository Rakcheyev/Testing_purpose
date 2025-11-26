import json
import yaml
from typing import Dict, Any

def save_tmdl(structure: Dict[str, Any], out_path: str):
    """Save structure in TMDL format. Placeholder."""
    # TODO: Реалізувати експорт у TMDL
    with open(out_path, "w") as f:
        f.write("# TMDL export placeholder\n")
        f.write(str(structure))

def save_json(structure: Dict[str, Any], out_path: str):
    with open(out_path, "w") as f:
        json.dump(structure, f, indent=2)

def save_yaml(structure: Dict[str, Any], out_path: str):
    with open(out_path, "w") as f:
        yaml.dump(structure, f)
