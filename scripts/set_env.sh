#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

deactivate || echo "No venv setup"
python3 -m venv .venv
echo 'pip install -r requirements.txt' >> .venv/bin/activate
echo "export PYTHONPATH=$PROJECT_DIR" >> .venv/bin/activate
source .venv/bin/activate
