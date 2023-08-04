import pandas as pd

# David's gender data from WikiData
gender_names = pd.read_csv("../../data/external/given-names-by-prevalence-in-WD-15000.openrefine.tsv", sep="\t")

# normalize men and women by library size
gender_names["count_male_norm"] = gender_names["count_male"] / sum(gender_names["count_male"])
gender_names["count_female_norm"] = gender_names["count_female"] / sum(gender_names["count_female"])
gender_names["count_other_norm"] = gender_names["count_other"] / sum(gender_names["count_other"])
gender_names["count_undefined_norm"] = gender_names["count_undefined"] / sum(gender_names["count_undefined"])

prevalent_gender_norm = []
confidence_norm = []

for name in gender_names.itertuples():
    if name.count_male_norm > name.count_female_norm:
        prevalent_gender_norm.append("male")
        confidence_norm.append(name.count_male_norm / (name.count_male_norm+name.count_female_norm))
        
    elif name.count_male_norm == name.count_female_norm:
        prevalent_gender_norm.append("inconclusive")
        confidence_norm.append(0.5)
        
    else:
        prevalent_gender_norm.append("female")
        confidence_norm.append(name.count_female_norm / (name.count_male_norm+name.count_female_norm))

gender_names["prevalent_gender_norm"] = prevalent_gender_norm
gender_names["confidence_norm"] = confidence_norm

authors = pd.read_pickle("../../data/interim/european_authors_with_all_taxonomic_articles.pkl")

def first_name_date(authors):
    year_authors = authors[["author_id", "author_display_name",
                            "publication_year"]].drop_duplicates().reset_index(drop=True)  
    first_names_list = []

    for author in year_authors.itertuples():
        if author.author_display_name:
            # first name of each author is the first word of their display name (before space)
            first_name = author.author_display_name.split()[0]
            first_names_list.append(first_name)
        else:
            first_names_list.append(None)

    year_authors["firstName"] = first_names_list
    return year_authors

first_names = first_name_date(authors)


def infer_gender(first_names, gender_names=gender_names, confidence=0.9):
    gender_names = gender_names[gender_names["nameLang"]=="mul"] # easier not to have doubles (for now)
    genders_list = []
    
    for author in first_names.itertuples():
        # record progress
        name_row = gender_names[gender_names["nameLabel"]==author.firstName]

        if name_row["prevalent_gender_norm"].values == "female" and name_row["confidence_norm"].values > confidence:
            genders_list.append(name_row["prevalent_gender"].values[0])
        elif name_row["prevalent_gender_norm"].values == "male" and name_row["confidence_norm"].values > confidence:
            genders_list.append(name_row["prevalent_gender"].values[0])
        else:
            genders_list.append("inconclusive")

    first_names["gender"] = genders_list
    return first_names

first_names = infer_gender(first_names)
first_names.to_csv("../../data/processed/gender_per_author.tsv", sep="\t")
print("Genders inferred. Results in data/processed/gender_per_author.tsv.")
