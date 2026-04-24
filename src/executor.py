import os
import sys
import json
import subprocess
import pandas as pd
from datetime import datetime

# mapping of common security keywords to Kubescape control ids
KEYWORD_TO_CONTROLS = {
    "authentication": ["C-0007", "C-0062"],
    "encryption": ["C-0066", "C-0087"],
    "access control": ["C-0035", "C-0036", "C-0084"],
    "rbac": ["C-0035", "C-0036"],
    "secret": ["C-0014", "C-0015"],
    "privilege": ["C-0055", "C-0057"],
    "network": ["C-0021", "C-0043"],
    "image": ["C-0016", "C-0017", "C-0078"],
    "resource": ["C-0009", "C-0010"],
    "logging": ["C-0024", "C-0048"],
    "container": ["C-0002", "C-0006"],
    "pod": ["C-0009", "C-0016"],
}


# read text files from Task-2 and return their contents
def load_diff_files(txt1_path: str, txt2_path: str) -> tuple:
    if not os.path.exists(txt1_path):
        raise FileNotFoundError(f"File not found: {txt1_path}")
    if not os.path.exists(txt2_path):
        raise FileNotFoundError(f"File not found: {txt2_path}")

    with open(txt1_path, "r", encoding="utf-8") as f:
        content1 = f.read()
    with open(txt2_path, "r", encoding="utf-8") as f:
        content2 = f.read()

    return content1, content2


# check if the diff files contain actual differences
def has_differences(content1: str, content2: str) -> bool:
    no_diff_phrases = [
        "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES",
        "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS",
        "NO DIFFERENCES FOUND",
    ]
    # both files must contain a no-difference phrase to return False
    content1_no_diff = any(phrase in content1 for phrase in no_diff_phrases)
    content2_no_diff = any(phrase in content2 for phrase in no_diff_phrases)
    return not (content1_no_diff and content2_no_diff)


# map diffs to Kubescape controls using keyword matching
def map_differences_to_controls(content1: str, content2: str, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "kubescape_controls.txt")

    # check if there are no differences
    if not has_differences(content1, content2):
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("NO DIFFERENCES FOUND\n")
        return out_path

    # combine both files for keyword search
    combined = (content1 + " " + content2).lower()

    # find matching controls based on keywords
    matched_controls = set()
    for keyword, controls in KEYWORD_TO_CONTROLS.items():
        if keyword in combined:
            for control in controls:
                matched_controls.add(control)

    with open(out_path, "w", encoding="utf-8") as f:
        if matched_controls:
            for control in sorted(matched_controls):
                f.write(control + "\n")
        else:
            # default to broad set of controls if no keywords matched
            f.write("C-0002\nC-0007\nC-0014\nC-0035\nC-0055\n")

    return out_path


# run Kubescape from command line based on controls file content
def run_kubescape(controls_txt_path: str, yamls_dir: str = "inputs/YAMLfiles", output_dir: str = "outputs") -> pd.DataFrame:
    os.makedirs(output_dir, exist_ok=True)

    with open(controls_txt_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # build results output path
    results_json = os.path.join(output_dir, "kubescape_results.json")

    if content == "NO DIFFERENCES FOUND":
        # run with all controls
        cmd = [
            "kubescape", "scan", yamls_dir,
            "--format", "json",
            "--output", results_json,
        ]
    else:
        # run with only matched controls
        controls = [line.strip() for line in content.splitlines() if line.strip()]
        controls_str = ",".join(controls)
        cmd = [
            "kubescape", "scan", "control", controls_str, yamls_dir,
            "--format", "json",
            "--output", results_json,
        ]

    print(f"Running Kubescape command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=False, timeout=300)
    except subprocess.TimeoutExpired:
        print("Kubescape scan timed out.")
    except FileNotFoundError:
        print("Kubescape not found. Make sure it is installed and in your PATH.")

    # parse JSON results into dataframe
    df = parse_kubescape_results(results_json)
    return df


# parse Kubescape JSON output into a pandas dataframe
def parse_kubescape_results(results_json_path: str) -> pd.DataFrame:
    rows = []

    if not os.path.exists(results_json_path):
        print(f"Results file not found: {results_json_path}")
        return pd.DataFrame(columns=["FilePath", "Severity", "Control name", "Failed resources", "All Resources", "Compliance score"])

    with open(results_json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("Could not parse Kubescape JSON output.")
            return pd.DataFrame(columns=["FilePath", "Severity", "Control name", "Failed resources", "All Resources", "Compliance score"])

    # extract results from JSON structure
    results = data.get("results", [])
    for result in results:
        control_name = result.get("name", "Unknown")
        severity = result.get("severity", {})
        if isinstance(severity, dict):
            severity_val = severity.get("severity", "Unknown")
        else:
            severity_val = str(severity)

        # Get resource counts
        all_resources = result.get("resourceCounters", {}).get("allResources", 0)
        failed_resources = result.get("resourceCounters", {}).get("failedResources", 0)

        # calculate compliance score
        if all_resources > 0:
            compliance_score = round(((all_resources - failed_resources) / all_resources) * 100, 2)
        else:
            compliance_score = 0.0

        # get file paths from failed resources
        raw_resources = result.get("rawResources", {})
        file_paths = []
        for status, resources in raw_resources.items():
            if isinstance(resources, list):
                for resource in resources:
                    source = resource.get("source", {})
                    filepath = source.get("relativePath", source.get("path", "Unknown"))
                    if filepath not in file_paths:
                        file_paths.append(filepath)

        if file_paths:
            for fp in file_paths:
                rows.append({
                    "FilePath": fp,
                    "Severity": severity_val,
                    "Control name": control_name,
                    "Failed resources": failed_resources,
                    "All Resources": all_resources,
                    "Compliance score": compliance_score,
                })
        else:
            rows.append({
                "FilePath": "N/A",
                "Severity": severity_val,
                "Control name": control_name,
                "Failed resources": failed_resources,
                "All Resources": all_resources,
                "Compliance score": compliance_score,
            })

    return pd.DataFrame(rows, columns=["FilePath", "Severity", "Control name", "Failed resources", "All Resources", "Compliance score"])


# save dataframe to CSV file
def save_results_to_csv(df: pd.DataFrame, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"kubescape_results_{timestamp}.csv")
    df.to_csv(out_path, index=False)
    print(f"CSV saved to: {out_path}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python executor.py <txt1> <txt2>")
        sys.exit(1)
    content1, content2 = load_diff_files(sys.argv[1], sys.argv[2])
    controls_path = map_differences_to_controls(content1, content2)
    df = run_kubescape(controls_path)
    save_results_to_csv(df)