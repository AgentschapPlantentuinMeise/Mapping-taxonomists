import numpy as np
import pandas as pd
import matplotlib.pyplot as plt # version 3.5.2
import fiona
import geopandas as gpd
import pickle
from itertools import groupby


def freq_countries(df):
    # get list of countries with authors
    countries = list(df["inst_country_code"])
    # remove None values + alphabetical
    countries = sorted([i for i in countries if i is not None])
    
    # count how many of each group (country)
    freqs = [len(list(group)) for key, group in groupby(countries)]
    
    # link counts to country codes
    freqs_dict = {}
    for i, country in enumerate(sorted(set(countries))):
        freqs_dict[country] = freqs[i]

    return freqs_dict


# get worldmap 
def plot_country_freqs(freqs, map_path, europe=False, dpi='figure'):
    worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    worldmap = worldmap.to_crs("ESRI:54009") 

    # convert 3-letter codes to 2-letter codes used for frequencies
    country_codes = pd.read_csv("../../data/external/countries_codes_and_coordinates.csv")
    country_codes = country_codes.applymap(lambda x: x.replace(' "', ""))
    country_codes = country_codes.applymap(lambda x: x.replace('"', ""))
    
    worldmap = worldmap.rename(columns={"iso_a3":"Alpha-3 code"})
    worldmap = pd.merge(worldmap, country_codes[["Alpha-2 code", "Alpha-3 code"]], 
                        on="Alpha-3 code", how="left")
    # fix problem with France
    worldmap.at[43,"Alpha-2 code"] = "FR"

    # add frequencies to worldmap
    worldmap["freq"] = worldmap["Alpha-2 code"].map(freqs)
    worldmap["freq"].fillna(0, inplace=True)
            
    # plot frequencies
    if not europe:
        fig, ax = plt.subplots(1,1)
        worldmap.plot(column='freq', ax=ax, legend=True)
        plt.savefig(map_path+".png", dpi=dpi)
    
    if europe:
        fig, ax = plt.subplots(1, 1)
        # limit scope of map to europe
        minx, miny, maxx, maxy = [-1500000, 4000000, 3500000, 8500000]
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        
        # limit data to europe
        europemap = worldmap.loc[worldmap["continent"] == "Europe"]
        europemap.plot(column='freq', ax=ax, legend=True)
        plt.savefig(map_path+"_europe.png", dpi=dpi)


authors = pd.read_pickle("../../data/interim/single_authors_of_european_taxonomic_articles.pkl")

countries_freq = freq_countries(authors)
plot_country_freqs(countries_freq, "../../reports/figures/map_authors_of_european_articles")

eu_authors = pd.read_pickle("../../data/interim/european_taxonomic_authors_no_duplicates.pkl")
countries_freq = freq_countries(eu_authors)
plot_country_freqs(countries_freq, "../../reports/figures/map_european_authors", europe=True)

eujot_freq = freq_countries(eu_authors[eu_authors["inst_display_name"]=="European journal of taxonomy"])
plot_country_freqs(eujot_freq, "../../reports/figures/map_eujot", europe=True)

print("Authors' institutions plotted onto world maps. Results in reports/figures.")
