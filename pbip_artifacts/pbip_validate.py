import os
from pbip_extract import extract_pbip_structure
from pbip_export import save_tmdl, save_json, save_yaml
from pbip_compare import compare_with_standards
from pbip_report import generate_report

if __name__ == "__main__":
    pbip_path = "example.pbip"
    standards_path = "../../external/standards_mcp.json"
    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Extract structure
    structure = extract_pbip_structure(pbip_path)

    # 2. Save in TMDL, JSON, YAML
    save_tmdl(structure, os.path.join(reports_dir, "pbip_structure.tmdl"))
    save_json(structure, os.path.join(reports_dir, "pbip_structure.json"))
    save_yaml(structure, os.path.join(reports_dir, "pbip_structure.yaml"))

    # 3. Compare with standards
    result = compare_with_standards(structure, standards_path)

    # 4. Generate report
    generate_report(result, os.path.join(reports_dir, "pbip_validation_report.json"))
    print("PBIP validation workflow complete (placeholders)")
