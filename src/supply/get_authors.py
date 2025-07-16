import pandas as pd
from pathlib import Path
import prep_authors

# === Path setup ===
this_dir = Path(__file__).resolve().parent
root_dir = this_dir.parents[1]

# Input files
processed_dir = root_dir / "data" / "processed"
interim_dir = root_dir / "data" / "interim"

articles_path = processed_dir / "taxonomic_articles_with_subjects.pkl"
output_all_authors = interim_dir / "all_authors_of_taxonomic_articles.pkl"
output_single_authors = interim_dir / "single_authors_of_taxonomic_articles.pkl"
output_country_authors = interim_dir / "country_authors_with_all_taxonomic_articles.pkl"
output_country_single_authors = interim_dir / "country_taxonomic_authors_no_duplicates.pkl"
output_country_single_authors_tsv = processed_dir / "country_taxonomic_authors_no_duplicates.tsv"

# === Load articles ===
print(f"[INFO] Loading articles from: {articles_path}", flush=True)
articles = pd.read_pickle(articles_path)

# === Extract authors ===
print(f"[INFO] Extracting authors...", flush=True)
authors = prep_authors.get_authors(articles)
single_authors = prep_authors.get_single_authors(authors)

# Save full and single-author datasets
authors.to_pickle(output_all_authors)
single_authors.to_pickle(output_single_authors)
print(f"[INFO] Saved all authors to: {output_all_authors}", flush=True)
print(f"[INFO] Saved single authors to: {output_single_authors}", flush=True)

# === Country-filtered authors ===
print(f"[INFO] Filtering authors by country...", flush=True)
country_authors = prep_authors.get_country_authors(authors)
single_country_authors = prep_authors.get_single_authors(country_authors)

country_authors.to_pickle(output_country_authors)
single_country_authors.to_pickle(output_country_single_authors)
single_country_authors.to_csv(output_country_single_authors_tsv, sep="\t", index=False)

print(f"[INFO] Country-specific authors written to: {output_country_single_authors_tsv}", flush=True)
