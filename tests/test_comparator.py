import pytest
import os
import yaml
import sys

# add src directory to path to import comparator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from comparator import (
    load_yaml_file,
    compare_kde_names,
    compare_kde_requirements,
)


# helper function to create temporary YAML file for testing
def create_temp_yaml(tmp_path, filename, data):
    filepath = tmp_path / filename
    with open(filepath, "w") as f:
        yaml.dump(data, f)
    return str(filepath)


# test load_yaml_file raises errors on invalid inputs
def test_load_yaml_file(tmp_path):
    # raise FileNotFoundError for missing file
    with pytest.raises(FileNotFoundError):
        load_yaml_file("outputs/nonexistent.yaml")

    # raise ValueError for non-YAML file
    with pytest.raises(ValueError):
        load_yaml_file("inputs/cis-r1.pdf")

    # raise ValueError for empty filepath
    with pytest.raises(ValueError):
        load_yaml_file("")

    # load valid YAML file successfully
    sample = {"element1": {"name": "Test", "requirements": ["req1"]}}
    valid_path = create_temp_yaml(tmp_path, "test.yaml", sample)
    result = load_yaml_file(valid_path)
    assert result == sample


# test compare_kde_names correctly identifies name differences
def test_compare_kde_names(tmp_path):
    # create YAML files with different KDE names
    data1 = {
        "element1": {"name": "User Authentication", "requirements": ["Use MFA"]},
        "element2": {"name": "Data Encryption", "requirements": ["Use AES-256"]},
    }
    data2 = {
        "element1": {"name": "User Authentication", "requirements": ["Use MFA"]},
        "element2": {"name": "Access Control", "requirements": ["Use RBAC"]},
    }

    yaml1 = create_temp_yaml(tmp_path, "cis-r1-kdes.yaml", data1)
    yaml2 = create_temp_yaml(tmp_path, "cis-r2-kdes.yaml", data2)

    out_path = compare_kde_names(yaml1, yaml2, output_dir=str(tmp_path))
    assert os.path.exists(out_path)

    with open(out_path, "r") as f:
        content = f.read()

    # data encryption only in file1; access control only in file2
    assert "Data Encryption" in content or "Access Control" in content
    assert "NO DIFFERENCES" not in content


# test that compare_kde_requirements correctly identifies requirement differences
def test_compare_kde_requirements(tmp_path):
    # create YAML files with same KDE names but diff requirements
    data1 = {
        "element1": {"name": "User Authentication", "requirements": ["Use MFA", "Expire after 30 mins"]},
    }
    data2 = {
        "element1": {"name": "User Authentication", "requirements": ["Use MFA"]},
    }

    yaml1 = create_temp_yaml(tmp_path, "cis-r1-kdes.yaml", data1)
    yaml2 = create_temp_yaml(tmp_path, "cis-r2-kdes.yaml", data2)

    out_path = compare_kde_requirements(yaml1, yaml2, output_dir=str(tmp_path))
    assert os.path.exists(out_path)

    with open(out_path, "r") as f:
        content = f.read()

    # expire after 30 mins only in file1
    assert "Expire after 30 mins" in content
    assert "NO DIFFERENCES" not in content