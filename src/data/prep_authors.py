import pandas as pd


# get authorship information from raw dataframe WITH all other data
def get_authors(df_input): # input: articles after get_dict_info
    # create empty dataframe with all authorship attributes
    df = pd.DataFrame()
    authors_list = []

    # find an example row to infer column names from
    i = 0
    example_row = None
    while example_row is None:
        row = df_input.iloc[i]
        # needs to have an available source with all expected fields
        if len(row["authorships"]) != 0:
            if len(row["authorships"][0]["institutions"]) != 0:
                example_row = row
                length_inst = len(row["authorships"][0]["institutions"][0])
        else:
            i += 1

    for article in df_input.itertuples():
        authors = pd.DataFrame(article.authorships)

        if len(authors) != 0:
            # disassemble author info
            for author in authors.itertuples():
                new_info = [article.id,] + list(author)[1:] + \
                           list(author.author.values())

                # add institution info
                if len(author.institutions) != 0:
                    new_info += list(author.institutions[0].values()) 
                else:
                    # no institution, no info
                    new_info += [None,] * length_inst
                
                if "countries" in str(author):
                    new_info.append(author.countries)
                else:
                    new_info += [None,]
                authors_list.append(new_info) 

    new_df = pd.DataFrame(authors_list, 
                          columns = ["article_id",] + list(example_row["authorships"][0].keys()) + \
                                    ["author_"+x for x in example_row["authorships"][0]["author"]] + \
                                    ["inst_"+x for x in example_row["authorships"][0]["institutions"][0]] + \
                                    ["countries_list",])
    df = pd.concat([df, new_df])
    
    return pd.merge(df, df_input, left_on="article_id", right_on="id")


# keep most recent publication per author
def get_single_authors(df_input): # input: authors with doubles
    keep = []
    
    for author in set(df_input["author_id"]):
        # get all rows that match author
        publications = df_input[df_input["author_id"]==author]
        # get most recent one
        most_recent = publications["publication_date"].max()

        # get species_subject from all their publications
        subjects = []
        for subjects_list in publications["species_subject"]:
            subjects.extend(subjects_list)

        keep_row = publications[publications["publication_date"]==most_recent].values.tolist()
        if keep_row:
            keep_row[0][-1] = subjects
            keep += keep_row
    
    keep_df = pd.DataFrame(keep, columns = df_input.columns)
    # drop duplicates because some articles may have been found twice through different queries 
    # and some authors have published multiple relevant articles on the same day
    return keep_df.drop_duplicates(subset=["author_id"], ignore_index=True)


with open("included_countries.txt", "r") as file:
    countries = [line[:-1] for line in file]

# filter a list of authors for authors who are asscociated with at least one institution from one of the chosen countries
def get_country_authors(df_input): # input: authors
    keep = []              
                
    for author in df_input.itertuples():
        # check every affiliated institute
        if author.inst_country_code in countries:
            keep.append(author)
    
    return pd.DataFrame(keep)#.drop(columns="Index") # drop old index
