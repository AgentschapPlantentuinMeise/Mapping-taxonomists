import numpy as np
import pandas as pd
import matplotlib.pyplot as plt # version 3.5.2
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap, to_rgb
import fiona
import geopandas as gpd
import pickle
from itertools import groupby
from mpl_toolkits.axes_grid1 import make_axes_locatable


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

# Alternative color scheme for the relative map (yellow to dark red)
#alt_cmp = LinearSegmentedColormap.from_list("WarmGradient", ["#ffe6b3", "#ff9933", "#cc3300"], N=10)


newcmp = LinearSegmentedColormap.from_list("TETTRIs", [to_rgb('#78d3ac'), to_rgb('#05041d')], N=10)
# Color-blind-safe color scheme for the relative map (yellow to purple)
alt_cmp = LinearSegmentedColormap.from_list("CB_Safe_YellowPurple", ["#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f"], N=10)
# Color-blind-safe color scheme for the relative map (blue to orange)
#alt_cmp = LinearSegmentedColormap.from_list("CB_Safe_BlueOrange", ["#f0f9e8", "#bae4bc", "#7bccc4", "#2b8cbe", "#084081"], N=10)


def plot_europe_combined_country_freqs(freqs, map_path, dpi=1200):
    # Load and process world map
    worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    worldmap = worldmap.to_crs("ESRI:54009")  # Mollweide projection

    # Convert 3-letter codes to 2-letter codes used for frequencies
    country_codes = pd.read_csv("../../data/external/country_codes.tsv", sep="\t")
    worldmap = worldmap.rename(columns={"iso_a3": "Alpha-3 code"})

    # Fix specific country codes in worldmap
    worldmap.at[43, "Alpha-3 code"] = "FRA"
    worldmap.at[21, "Alpha-3 code"] = "NOR"
    worldmap.at[174, "Alpha-3 code"] = "XKX"
    
    # Merge country codes and frequency data
    worldmap = pd.merge(worldmap, country_codes[["Alpha-2 code", "Alpha-3 code"]],
                        on="Alpha-3 code", how="left")
    worldmap["freq"] = worldmap["Alpha-2 code"].map(freqs).fillna(0)
    worldmap.replace(0, np.nan, inplace=True)
    
    # Set up the figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))  # Adjust size as needed
    
    # Remove box (spines) around each map
    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_visible(False)

    # Plot the absolute frequency map of Europe
    divider1 = make_axes_locatable(ax1)
    cax1 = divider1.append_axes("right", size="5%", pad=0.1)
    
    minx, miny, maxx, maxy = [-1500000, 4000000, 4300000, 8500000]
    ax1.set_xlim(minx, maxx)
    ax1.set_ylim(miny, maxy)
    
    ax1.set_xticks([])
    ax1.set_yticks([])
    worldmap.plot(column='freq', ax=ax1, legend=True, cax=cax1,
                  missing_kwds={"color": "lightgrey"},
                  cmap=newcmp,
                  edgecolor="black",  # Add black borders to the countries
                  linewidth=0.5,      # Set line width for borders
                  legend_kwds={"label": "Number of Taxonomists"})  # Set legend font size here
    
    # Adjust font size of colorbar ticks
    plt.setp(cax1.yaxis.get_ticklabels(), fontsize=14)
    cax1.set_ylabel("Number of Taxonomists", fontsize=16, labelpad=10)  # Increase label font size here
    
    # Add 'A' label to the first plot
    ax1.text(0.06, 0.97, 'A', transform=ax1.transAxes, fontsize=36, fontweight='normal', va='top', ha='right')

    # Plot the relative frequency map of Europe with a color-blind-safe color scheme
    worldmap["relative_freq"] = worldmap["freq"] / worldmap["pop_est"] * 100
    
    divider2 = make_axes_locatable(ax2)
    cax2 = divider2.append_axes("right", size="5%", pad=0.1)
    
    ax2.set_xlim(minx, maxx)
    ax2.set_ylim(miny, maxy)
    
    ax2.set_xticks([])
    ax2.set_yticks([])
    worldmap.plot(column='relative_freq', ax=ax2, legend=True, cax=cax2,
                  missing_kwds={"color": "lightgrey"},
                  cmap=alt_cmp,  # Use the color-blind-safe blue-to-orange colormap
                  edgecolor="black",  # Add black borders to the countries
                  linewidth=0.5,      # Set line width for borders
                  legend_kwds={"label": "Percentage of Population"})
    
    # Adjust font size of colorbar ticks
    plt.setp(cax1.yaxis.get_ticklabels(), fontsize=14)
    cax2.set_ylabel("Percentage of Population", fontsize=16, labelpad=10)  # Increase label font size here
    
    # Add 'B' label to the second plot
    ax2.text(0.06, 0.97, 'B', transform=ax2.transAxes, fontsize=36, fontweight='normal', va='top', ha='right')

    plt.tight_layout()  # Adjust layout
    plt.savefig(map_path + "_europe_combined.jpg", dpi=dpi, bbox_inches="tight")
    plt.show()  # Show plot if running interactively

# get worldmap 
def plot_country_freqs(freqs, map_path, europe=False, dpi=1200, relative=False):
    worldmap = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
    worldmap = worldmap.to_crs("ESRI:54009") # Mollweide projection

    # convert 3-letter codes to 2-letter codes used for frequencies
    country_codes = pd.read_csv("../../data/external/country_codes.tsv", sep="\t")
    
    worldmap = worldmap.rename(columns={"iso_a3":"Alpha-3 code"})
    # fixing country codes in worldmap
    worldmap.at[43,"Alpha-3 code"] = "FRA"
    worldmap.at[21,"Alpha-3 code"] = "NOR"
    worldmap.at[174,"Alpha-3 code"] = "XKX"
    
    worldmap = pd.merge(worldmap, country_codes[["Alpha-2 code", "Alpha-3 code"]], 
                        on="Alpha-3 code", how="left")

    # add frequencies to worldmap
    worldmap["freq"] = worldmap["Alpha-2 code"].map(freqs)
    worldmap["freq"].fillna(0, inplace=True)
    worldmap.replace(0, np.nan, inplace=True)
    
    if relative:
        worldmap = worldmap.rename(columns={"freq":"absolute_freq"})
        # map percentage of country's population that are taxonomists
        worldmap["freq"] = worldmap["absolute_freq"]/worldmap["pop_est"]*100
            
    # plot frequencies
    if not europe:
        fig, ax = plt.subplots(1,1)

        ax.set_xticks([])
        ax.set_yticks([])
        
        divider = make_axes_locatable(ax) # make legend same size as plot
        cax = divider.append_axes("right", size="5%", pad=0.1)
        
        worldmap.plot(column='freq', ax=ax, legend=True,
                      missing_kwds={"color":"lightgrey"},
                      cax=cax,
                      cmap = newcmp)
        plt.savefig(map_path+".jpg", dpi=dpi)
    
    if europe:
        fig, ax = plt.subplots(1, 1)
        
        divider = make_axes_locatable(ax) # make legend same size as plot
        cax = divider.append_axes("right", size="5%", pad=0.1)
        
        # limit scope of map to europe
        minx, miny, maxx, maxy = [-1500000, 4000000, 4300000, 8500000]
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)

        ax.set_xticks([])
        ax.set_yticks([])

        plt.xticks([])
        plt.yticks([])
        
        if not relative:
            worldmap.plot(column='freq', ax=ax, legend=True,
                          missing_kwds={"color":"lightgrey"},
                          legend_kwds={"label":"number of taxonomists"},
                          cax=cax,
                          cmap = alt_cmp)
        else:
            worldmap.plot(column='freq', ax=ax, legend=True,
                          missing_kwds={"color":"lightgrey"}, 
                          legend_kwds={"label":"percentage of population"},
                          cax=cax,
                          cmap = newcmp)

        plt.tight_layout()  # Adjust padding
        plt.savefig(map_path+"_europe.jpg", dpi=dpi, bbox_inches="tight")
        
def save_freq_data(freqs_dict, output_path):
    """
    Saves the country frequency data to a CSV file.
    
    Parameters:
    freqs_dict (dict): Dictionary with country codes and frequency counts.
    output_path (str): Path where the CSV file will be saved.
    """
    freq_df = pd.DataFrame(list(freqs_dict.items()), columns=['Country Code', 'Frequency'])
    freq_df.to_csv(output_path, index=False)
    print(f"Underlying data saved to {output_path}")


authors = pd.read_pickle("../../data/interim/single_authors_of_taxonomic_articles.pkl")

countries_freq = freq_countries(authors)
save_freq_data(countries_freq, "../../reports/figures/countries_freq_all.csv")
plot_country_freqs(countries_freq, "../../reports/figures/map_authors")

eu_authors = pd.read_pickle("../../data/interim/country_taxonomic_authors_no_duplicates.pkl")
countries_freq = freq_countries(eu_authors)
save_freq_data(countries_freq, "../../reports/figures/countries_freq_europe.csv")
plot_country_freqs(countries_freq, "../../reports/figures/map_authors_europe", europe=True)
plot_country_freqs(countries_freq, "../../reports/figures/map_authors_europe_relative", europe=True,
                   relative=True) 

eujot_freq = freq_countries(eu_authors[eu_authors["source_issn_l"]=="2118-9773"])
save_freq_data(eujot_freq, "../../reports/figures/countries_freq_eujot.csv")
plot_country_freqs(eujot_freq, "../../reports/figures/map_eujot", europe=True)
plot_country_freqs(eujot_freq, "../../reports/figures/map_eujot_relative", europe=True, relative=True)

print("Authors' institutions plotted onto world maps. Results in reports/figures.")

countries_freq = freq_countries(eu_authors)
plot_europe_combined_country_freqs(countries_freq, "../../reports/figures/map_authors_europe_combined")
