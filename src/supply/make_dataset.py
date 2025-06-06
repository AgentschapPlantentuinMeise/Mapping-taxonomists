import sys
import os
import glob
from datetime import datetime

def log(msg):
    """Print a timestamped log message."""
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")

def run_script(path):
    """Run a script via exec() and handle errors."""
    try:
        log(f"Running {path}...")
        with open(path, "r") as f:
            code = f.read()
        exec(code, globals())
        log(f"{path} completed successfully.")
    except Exception as e:
        log(f"ERROR while running {path}: {e}")
        sys.exit(1)

# Step 1: Define backbone path
backbone_dir = os.path.join("..", "..", "data", "external", "backbone")
backbone_file = os.path.join(backbone_dir, "Taxon.tsv")

# Step 2: Ensure directories exist
if not os.path.exists(backbone_file):
    os.makedirs(backbone_dir, exist_ok=True)
    log("ERROR: GBIF taxonomic backbone is missing.")
    print("Please download it and place it in data/external/backbone/")
    sys.exit(1)

for directory in [
    "../../data/raw/articles",
    "../../data/interim/keyword-filtered_articles",
    "../../data/processed"
]:
    os.makedirs(directory, exist_ok=True)

# Step 3: Clean article directory
log("Cleaning raw articles directory...")
for f in glob.glob("../../data/raw/articles/*"):
    try:
        os.remove(f)
    except Exception as e:
        log(f"WARNING: Could not delete {f}: {e}")

# Step 4: Run scripts sequentially with logging and error handling
run_script("list_journals.py")
run_script("get_articles.py")
run_script("parse_taxonomy.py")
run_script("get_authors.py")
run_script("disambiguate.py")

log("make_dataset.py completed successfully.")