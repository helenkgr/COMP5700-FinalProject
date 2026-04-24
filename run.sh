#!/bin/bash

# activate virtual environment
source comp5700-venv/Scripts/activate

# check that two PDF files were provided
if [ "$#" -ne 2 ]; then
    echo "Usage: bash run.sh <pdf1> <pdf2>"
    exit 1
fi

PDF1=$1
PDF2=$2

# run the full pipeline
echo "Running extractor on $PDF1 and $PDF2..."
python src/extractor.py "$PDF1" "$PDF2"

# get the generated YAML file names
BASE1=$(basename "$PDF1" .pdf)
BASE2=$(basename "$PDF2" .pdf)
YAML1="outputs/${BASE1}-kdes.yaml"
YAML2="outputs/${BASE2}-kdes.yaml"

echo "Running comparator on $YAML1 and $YAML2..."
python src/comparator.py "$YAML1" "$YAML2"

# get the generated diff file names
DIFF1="outputs/name_diff_${BASE1}-kdes_vs_${BASE2}-kdes.txt"
DIFF2="outputs/req_diff_${BASE1}-kdes_vs_${BASE2}-kdes.txt"

echo "Running executor on $DIFF1 and $DIFF2..."
python src/executor.py "$DIFF1" "$DIFF2"

echo "Pipeline complete! Check the outputs/ folder."