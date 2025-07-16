import pandas as pd
import numpy as np
import re
from pathlib import Path

# === Setup paths ===
this_dir = Path(__file__).resolve().parent
root_dir = this_dir.parents[1]
interim_dir = root_dir / "data" / "interim"
processed_dir = root_dir / "data" / "processed"
external_dir = root_dir / "data" / "external" / "backbone"

# === Load author data ===
input_authors = interim_dir / "country_taxonomic_authors_no_duplicates.pkl"
print(f"[INFO] Loading author data from: {input_authors}")
authors = pd.read_pickle(input_authors)
print(f"[INFO] Number of authors before disambiguation: {len(authors)}")

# === Preprocess author names ===
authors = authors[["author_id", "author_display_name", "author_orcid",
                   "inst_id", "inst_display_name", "species_subject"]]
authors = authors.set_index("author_id")

truncated_names = []
stripped_names = []

for author in authors.itertuples():
    first_initial = author.author_display_name[0]
    last_name = author.author_display_name.split(" ")[-1]
    truncated_names.append(f"{first_initial} {last_name}")
    stripped_name = re.sub(r'[ .\u002D\u2010\u2012\u2013\u2014\u2015\u2043\uFE63\uFF0D]', '', author.author_display_name)
    stripped_names.append(stripped_name)

authors["truncatedName"] = truncated_names
authors["strippedName"] = stripped_names

# === Load GBIF backbone ===
backbone_path = external_dir / "Taxon.tsv"
print(f"[INFO] Loading GBIF backbone from: {backbone_path}")
backbone = pd.read_csv(backbone_path, sep="\t", 
                       dtype={'scientificNameAuthorship': 'str',
                              'infraspecificEpithet': 'str',
                              'canonicalName': 'str',
                              'genericName': 'str',
                              'specificEpithet': 'str',
                              'namePublishedIn': 'str',
                              'taxonomicStatus': 'str',
                              'taxonRank': 'str',
                              'taxonRemarks': 'str',
                              'kingdom': 'str',
                              'phylum': 'str',
                              'family': 'str',
                              'genus': 'str'},
                       on_bad_lines='skip')

backbone = backbone[backbone["taxonomicStatus"] != "doubtful"]
backbone = backbone[["canonicalName", "kingdom", "order", "family"]].dropna(subset=["canonicalName"]).drop_duplicates()

# === Index species to order and kingdom ===
seen_species = {row.canonicalName: row.order for row in backbone.itertuples() if isinstance(row.order, str)}
species_to_kingdom = {row.canonicalName: row.kingdom for row in backbone.itertuples() if isinstance(row.kingdom, str)}

# === Map orders and kingdoms to authors ===
authors["order"] = [[] for _ in range(len(authors))]
authors["kingdom"] = [[] for _ in range(len(authors))]

for i, author in authors.iterrows():
    for species in author["species_subject"]:
        if species in seen_species:
            if seen_species[species] not in author["order"]:
                authors.at[i, "order"].append(seen_species[species])
        if species in species_to_kingdom:
            if species_to_kingdom[species] not in author["kingdom"]:
                authors.at[i, "kingdom"].append(species_to_kingdom[species])

# === Disambiguation logic ===
def match(a, b):
    if a.order == [] or b.order == []:
        return a.inst_id == b.inst_id and a.strippedName == b.strippedName
    else:
        return a.inst_id == b.inst_id and bool(set(a.order).intersection(set(b.order)))

def cluster(matches):
    clusters = []
    for match in matches:
        overlapping = [i for i, group in enumerate(clusters) if set(match).intersection(group)]
        if not overlapping:
            clusters.append(match)
        elif len(overlapping) == 1:
            clusters[overlapping[0]].extend(match)
        else:
            supergroup = []
            for i in sorted(overlapping, reverse=True):
                supergroup.extend(clusters.pop(i))
            supergroup.extend(match)
            clusters.append(supergroup)
    return [set(group) for group in clusters]

duplicates = authors[authors.duplicated(subset=["truncatedName"], keep=False)]
true_people = []

for name in set(duplicates["truncatedName"]):
    same_names = duplicates[duplicates["truncatedName"] == name]
    matches = []
    for person_a in same_names.itertuples():
        aliases = [person_a.Index]
        for person_b in same_names.itertuples():
            if person_a.Index != person_b.Index and match(person_a, person_b):
                aliases.append(person_b.Index)
        matches.append(aliases)
    true_people.extend(cluster(matches))

true_authors = authors[~authors.duplicated(subset="truncatedName", keep=False)].reset_index()
merged_people = []
m = 1

def collect_values(df, person_ids, column):
    if not person_ids: return None
    values = []
    for pid in person_ids:
        val = df.loc[pid, column]
        if val is None: continue
        if column in ["order", "species_subject", "kingdom"]:
            values.extend(val)
        else:
            values.append(val)
    values = set(values)
    return list(values)[0] if len(values) == 1 else list(values)

for person in true_people:
    row = [person]
    for col in true_authors.columns[1:]:
        row.append(collect_values(authors, person, col))
    merged_people.append(authors.loc[list(person)].reset_index())
    merged_people[-1]["groupNr"] = m
    m += 1
    true_authors.loc[len(true_authors)] = row

# === Save results ===
merged_df = pd.concat(merged_people, ignore_index=True)
merged_df.to_csv(interim_dir / "merged_people_truncated.csv", index=False)

true_authors.to_pickle(processed_dir / "authors_disambiguated_truncated.pkl")
true_authors.to_csv(processed_dir / "authors_disambiguated_truncated.tsv", sep="\t", index=False)

print(f"[INFO] Number of authors after disambiguation: {len(true_authors)}")
