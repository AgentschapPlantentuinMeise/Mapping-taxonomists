from pathlib import Path
import subprocess
import sys
from datetime import datetime
import os
import glob
import pandas as pd
import json
import argparse
#sys.stdout.reconfigure(line_buffering=True)


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, required=True)
args = parser.parse_args()

with open(args.config, "r", encoding="utf-8") as f:
    config = json.load(f)

# Set root directory
root_dir = Path(config.get("root_dir", Path(__file__).resolve().parents[1]))

required_keys = ["root_dir"]
missing = [key for key in required_keys if key not in config]
if missing:
    raise ValueError(f"Missing required config keys: {missing}")
    
if not hasattr(pd, "DataFrame"):
    raise ImportError("pandas is not correctly loaded — check for naming conflicts (e.g., pandas.py).")

def log(msg):
    """Print a timestamped log message."""
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")

log(f"Loaded config from: {args.config}")

def run_script(script_relative_path):
    """Run a script using subprocess with proper error handling."""
    script_path = Path(__file__).resolve().parent / script_relative_path
    if not script_path.exists():
        log(f"ERROR: Cannot find script at {script_path}")
        sys.exit(1)

    try:
        log(f"Running {script_relative_path}...")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True  # Will raise CalledProcessError on failure
        )
        log(f"{script_relative_path} completed successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        log(f"ERROR while running {script_relative_path}:")
        print(e.stderr)
        sys.exit(e.returncode)

# Step 1: Define backbone path
backbone_file = Path("data") / "external" / "backbone" / "Taxon.tsv"

# Step 2: Ensure directories exist
if not backbone_file.exists():
    backbone_file.parent.mkdir(parents=True, exist_ok=True)
    log("ERROR: GBIF taxonomic backbone is missing.")
    print("Please download it and place it in data/external/backbone/")
    sys.exit(1)

for rel_dir in [
    "data/raw/articles",
    "data/interim/keyword-filtered_articles",
    "data/processed"
]:
    Path(rel_dir).mkdir(parents=True, exist_ok=True)

# Step 3: Clean article directory
log("Cleaning raw articles directory...")
for f in Path("data/raw/articles").glob("*"):
    try:
        f.unlink()
    except Exception as e:
        log(f"WARNING: Could not delete {f}: {e}")

# Step 4: Run scripts in order
run_script("list_journals.py")
run_script("get_articles.py")
run_script("parse_taxonomy.py")
run_script("get_authors.py")
run_script("disambiguate.py")

log("Pipeline completed successfully.")
