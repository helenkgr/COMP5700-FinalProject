# COMP5700 Final Project

## Team Members
- Helen Grogan - hkg0017@auburn.edu

## LLM Used
This project uses **google/gemma-3-1b-it** for Key Data Element (KDE) extraction in Task 1.

## Project Structure
- `src/extractor.py` - Task 1: extracts KDEs from PDF security requirements documents
- `src/comparator.py` - Task 2: compares KDE YAML files for differences
- `src/executor.py` - Task 3: maps differences to Kubescape controls and runs scans
- `tests/` - test cases for all three tasks
- `inputs/` - input PDF files and YAML files for scanning
- `outputs/` - generated YAML, TEXT, and CSV output files

## Setup and Installation

### Prerequisites
- Python 3.10+
- Kubescape installed and available in PATH

### Install dependencies
```bash
python -m venv comp5700-venv
comp5700-venv\Scripts\activate
pip install -r requirements.txt
```

### Run the project
```bash
bash run.sh inputs/cis-r1.pdf inputs/cis-r2.pdf
```

## Running Tests
```bash
pytest tests/ -v
```