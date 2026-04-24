import fitz
import yaml
import os
import re
from transformers import pipeline
import torch
from datetime import datetime


# load and validate PDF file; return all text as string
def load_document(filepath: str) -> str:
    if not filepath:
        raise ValueError("Filepath cannot be empty.")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if not filepath.lower().endswith(".pdf"):
        raise ValueError(f"File must be a PDF: {filepath}")

    doc = fitz.open(filepath)
    if doc.page_count == 0:
        raise ValueError(f"PDF has no pages: {filepath}")

    # loop through all pages and extract text
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    if not text.strip():
        raise ValueError(f"PDF appears to be empty or unreadable: {filepath}")

    return text


# zero-shot prompt
def build_zero_shot_prompt(document_text: str) -> str:
    truncated = document_text[:3000]
    prompt = f"""You are a security requirements analyst.

Read the following security requirements document and identify all Key Data Elements (KDEs).
For each KDE, provide its name and list the specific requirements associated with it.

Respond ONLY in the following YAML format and nothing else:
element1:
  name: <element name>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <element name>
  requirements:
    - <requirement 1>

Document:
{truncated}

YAML Output:"""
    return prompt


# few-shot prompt 
def build_few_shot_prompt(document_text: str) -> str:
    truncated = document_text[:3000]
    prompt = f"""You are a security requirements analyst.

Read the following security requirements document and identify all Key Data Elements (KDEs).
For each KDE, provide its name and list the specific requirements associated with it.

Here are two examples of the expected output format:

Example 1:
element1:
  name: User Authentication
  requirements:
    - All users must authenticate using multi-factor authentication
    - Passwords must be at least 12 characters long
    - Sessions must expire after 30 minutes of inactivity

Example 2:
element1:
  name: Data Encryption
  requirements:
    - All data at rest must be encrypted using AES-256
    - All data in transit must use TLS 1.2 or higher
element2:
  name: Access Control
  requirements:
    - Role-based access control must be enforced
    - Least privilege principle must be applied to all accounts

Now extract KDEs from this document in the same format:

Document:
{truncated}

YAML Output:"""
    return prompt


# chain-of-thought prompt
def build_chain_of_thought_prompt(document_text: str) -> str:
    truncated = document_text[:3000]
    prompt = f"""You are a security requirements analyst.

Follow these steps to extract Key Data Elements (KDEs) from the document below:

Step 1: Read the entire document carefully.
Step 2: Identify distinct security topics or data categories mentioned.
Step 3: For each topic, list the specific requirements or rules associated with it.
Step 4: Label each topic as a Key Data Element (KDE).
Step 5: Format your findings in YAML as shown below.

Output format:
element1:
  name: <element name>
  requirements:
    - <requirement 1>
    - <requirement 2>
element2:
  name: <element name>
  requirements:
    - <requirement 1>

Document:
{truncated}

Now follow Steps 1-5 and produce the YAML output:"""
    return prompt


# load the Gemma-3-1B model pipeline on CPU
def load_llm():
    pipe = pipeline(
        "text-generation",
        model="google/gemma-3-1b-it",
        device="cpu",
        torch_dtype=torch.bfloat16,
    )
    return pipe


# parse YAML from raw LLM output
def parse_yaml_output(raw_text: str) -> dict:
    cleaned = re.sub(r"```yaml|```", "", raw_text).strip()
    try:
        parsed = yaml.safe_load(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass
    # fallback if YAML parsing fails
    return {"element1": {"name": "unparsed_output", "requirements": [cleaned]}}


# run the LLM on a prompt and return parsed KDE dictionary and raw output
def extract_kdes(prompt: str, pipe) -> dict:
    messages = [
        [
            {
                "role": "system",
                "content": [{"type": "text", "text": "You are a helpful security requirements analyst. Always respond in valid YAML format only."}],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
        ]
    ]

    output = pipe(messages, max_new_tokens=512)
    raw_text = output[0][0]["generated_text"][-1]["content"]
    kde_dict = parse_yaml_output(raw_text)
    return kde_dict, raw_text


# save KDE dictionary to YAML file
def save_kdes_to_yaml(kde_dict: dict, pdf_filepath: str, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(pdf_filepath))[0]
    out_path = os.path.join(output_dir, f"{base_name}-kdes.yaml")

    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(kde_dict, f, default_flow_style=False, allow_unicode=True)

    return out_path


# collect LLM run results and put them in text file
def dump_llm_outputs(results: list, output_dir: str = "outputs") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"llm_outputs_{timestamp}.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        for entry in results:
            f.write(f"*LLM Name*\n{entry['llm_name']}\n\n")
            f.write(f"*Prompt Used*\n{entry['prompt']}\n\n")
            f.write(f"*Prompt Type*\n{entry['prompt_type']}\n\n")
            f.write(f"*LLM Output*\n{entry['llm_output']}\n\n")

    return out_path


# full pipeline (load docs, build prompts, run LLM, save all outputs)
def run_extractor(pdf1_path: str, pdf2_path: str):
    print("Loading documents...")
    text1 = load_document(pdf1_path)
    text2 = load_document(pdf2_path)

    print("Loading LLM (may take a few minutes)")
    pipe = load_llm()

    # define all three prompt types to run
    prompt_builders = [
        ("zero_shot", build_zero_shot_prompt),
        ("few_shot", build_few_shot_prompt),
        ("chain_of_thought", build_chain_of_thought_prompt),
    ]

    results = []

    # run each prompt type on each document
    for doc_path, doc_text in [(pdf1_path, text1), (pdf2_path, text2)]:
        for prompt_type, builder in prompt_builders:
            print(f"Running {prompt_type} prompt on {os.path.basename(doc_path)}...")
            prompt = builder(doc_text)
            kde_dict, raw_output = extract_kdes(prompt, pipe)
            save_kdes_to_yaml(kde_dict, doc_path)

            results.append({
                "llm_name": "google/gemma-3-1b-it",
                "prompt": prompt,
                "prompt_type": prompt_type,
                "llm_output": raw_output,
            })

    dump_llm_outputs(results)
    print("Extractor complete. Check outputs/ folder.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python extractor.py <pdf1> <pdf2>")
        sys.exit(1)
    run_extractor(sys.argv[1], sys.argv[2])