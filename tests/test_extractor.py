import pytest
import os
import yaml
import sys

# add src directory to path to import extractor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extractor import (
    load_document,
    build_zero_shot_prompt,
    build_few_shot_prompt,
    build_chain_of_thought_prompt,
    parse_yaml_output,
    save_kdes_to_yaml,
    dump_llm_outputs,
)


# test that load_document raises errors on invalid inputs
def test_load_document(tmp_path):
    # raise FileNotFoundError for missing file
    with pytest.raises(FileNotFoundError):
        load_document("inputs/nonexistent.pdf")

    # raise ValueError for empty filepath
    with pytest.raises(ValueError):
        load_document("")

    # raise ValueError for non-PDF by creating text file
    fake_txt = tmp_path / "fake.txt"
    fake_txt.write_text("not a pdf")
    with pytest.raises(ValueError):
        load_document(str(fake_txt))


# test that zero-shot prompt returns non-empty string containing instructions
def test_build_zero_shot_prompt():
    sample_text = "Users must use multi-factor authentication."
    result = build_zero_shot_prompt(sample_text)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "YAML" in result
    assert sample_text[:50] in result


# test that few-shot prompt returns string with examples
def test_build_few_shot_prompt():
    sample_text = "All data must be encrypted at rest."
    result = build_few_shot_prompt(sample_text)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Example" in result
    assert "YAML" in result


# test that chain-of-thought prompt returns string with step instructions
def test_build_chain_of_thought_prompt():
    sample_text = "Access control must follow least privilege."
    result = build_chain_of_thought_prompt(sample_text)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Step 1" in result
    assert "Step 5" in result


# test that save_kdes_to_yaml creates valid YAML file
def test_save_kdes_to_yaml(tmp_path):
    sample_kde = {
        "element1": {
            "name": "User Authentication",
            "requirements": ["Use MFA", "Expire sessions after 30 mins"]
        }
    }
    # use tmp_path to clean up test files
    out_path = save_kdes_to_yaml(sample_kde, "inputs/cis-r1.pdf", output_dir=str(tmp_path))
    assert os.path.exists(out_path)

    # verify file contains valid YAML
    with open(out_path, "r") as f:
        loaded = yaml.safe_load(f)
    assert "element1" in loaded
    assert loaded["element1"]["name"] == "User Authentication"


# test that dump_llm_outputs creates text file
def test_dump_llm_outputs(tmp_path):
    sample_results = [
        {
            "llm_name": "google/gemma-3-1b-it",
            "prompt": "Sample prompt text",
            "prompt_type": "zero_shot",
            "llm_output": "element1:\n  name: Test\n  requirements:\n    - req1"
        }
    ]
    out_path = dump_llm_outputs(sample_results, output_dir=str(tmp_path))
    assert os.path.exists(out_path)

    # verify file contains expected sections
    with open(out_path, "r") as f:
        content = f.read()
    assert "*LLM Name*" in content
    assert "*Prompt Used*" in content
    assert "*Prompt Type*" in content
    assert "*LLM Output*" in content
    assert "google/gemma-3-1b-it" in content