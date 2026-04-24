import pytest
import os
import pandas as pd
import sys

# add src directory to path to import executor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from executor import (
    load_diff_files,
    has_differences,
    map_differences_to_controls,
    save_results_to_csv,
)


# helper to create temporary text file for testing
def create_temp_txt(tmp_path, filename, content):
    filepath = tmp_path / filename
    filepath.write_text(content)
    return str(filepath)


# test load_diff_files raises errors on invalid inputs
def test_load_diff_files(tmp_path):
    # raise FileNotFoundError for missing files
    with pytest.raises(FileNotFoundError):
        load_diff_files("outputs/nonexistent1.txt", "outputs/nonexistent2.txt")

    # load valid text files successfully
    f1 = create_temp_txt(tmp_path, "diff1.txt", "User Authentication only in cis-r1-kdes")
    f2 = create_temp_txt(tmp_path, "diff2.txt", "Data Encryption only in cis-r2-kdes")
    c1, c2 = load_diff_files(f1, f2)
    assert "User Authentication" in c1
    assert "Data Encryption" in c2


# test has_differences identifies no-difference cases
def test_has_differences(tmp_path):
    # both files say no diffs
    no_diff1 = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
    no_diff2 = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"
    assert has_differences(no_diff1, no_diff2) == False

    # at least one file has diffs
    diff1 = "User Authentication only in cis-r1-kdes"
    diff2 = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"
    assert has_differences(diff1, diff2) == True


# test map_differences_to_controls writes correct output
def test_map_differences_to_controls(tmp_path):
    # when no diffs, write NO DIFFERENCES FOUND
    no_diff = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
    out_path = map_differences_to_controls(no_diff, no_diff, output_dir=str(tmp_path))
    assert os.path.exists(out_path)
    with open(out_path, "r") as f:
        content = f.read()
    assert "NO DIFFERENCES FOUND" in content

    # when diffs with keywords, write control IDs
    diff1 = "authentication access control encryption"
    diff2 = "rbac secret privilege"
    out_path2 = map_differences_to_controls(diff1, diff2, output_dir=str(tmp_path))
    with open(out_path2, "r") as f:
        content2 = f.read()
    assert "C-" in content2


# test save_results_to_csv creates valid CSV file
def test_save_results_to_csv(tmp_path):
    # create sample dataframe
    sample_df = pd.DataFrame([
        {
            "FilePath": "inputs/YAMLfiles/repos/argo-cd/deploy.yaml",
            "Severity": "High",
            "Control name": "Anonymous access enabled",
            "Failed resources": 3,
            "All Resources": 10,
            "Compliance score": 70.0,
        }
    ])

    out_path = save_results_to_csv(sample_df, output_dir=str(tmp_path))
    assert os.path.exists(out_path)

    # verify CSV has correct headers
    loaded = pd.read_csv(out_path)
    assert "FilePath" in loaded.columns
    assert "Severity" in loaded.columns
    assert "Control name" in loaded.columns
    assert "Failed resources" in loaded.columns
    assert "All Resources" in loaded.columns
    assert "Compliance score" in loaded.columns