import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgb
import geopandas as gpd
from mpl_toolkits.axes_grid1 import make_axes_locatable
from pathlib import Path
from scipy.stats import pearsonr

# Define paths
this_dir = Path(__file__).resolve().parent
root_dir = this_dir.parents[1]
interim_dir = root_dir / "data" / "interim"
external_dir = root_dir / "data" / "external"
reports_dir = root_dir / "reports" / "figures"

# Define color maps
newcmp = LinearSegmentedColormap.from_list("TETTRIs", [to_rgb('#78d3ac'), to_rgb('#05041d')], N=10)
alt_cmp = LinearSegmentedColormap.from_list("CB_Safe_YellowPurple", ["#fef0d9", "#fdcc8a", "#fc8d59", "#d7301f"], N=10)

def freq_countries(df):
    countries = df["inst_country_code"].dropna()
    return countries.value_counts().to_dict()

def plot_country_freqs(freqs, map_path, europe=False, dpi=300, relative=False, panel_label=None):
    shapefile_path = external_dir / "naturalearth" / "ne_110m_admin_0_countries.shp"
    #print(f"[DEBUG] Loading shapefile from: {shapefile_path}")
    worldmap = gpd.read_file(shapefile_path)

    if worldmap.crs is None:
        print("[DEBUG] CRS is missing. Setting it to EPSG:4326")
        worldmap.set_crs(epsg=4326, inplace=True)

    worldmap = worldmap.to_crs("ESRI:54009")

    # Load country codes and population estimates
    country_data_path = external_dir / "country_codes_and_population.tsv"
    if not country_data_path.exists():
        raise FileNotFoundError(f"[ERROR] Could not find country data at: {country_data_path}")
    country_data = pd.read_csv(country_data_path, sep="\t")

    required_cols = {"Alpha-2 code", "Alpha-3 code", "pop_est"}
    missing_cols = required_cols - set(country_data.columns)
    if missing_cols:
        raise ValueError(f"[ERROR] Missing columns in population file: {missing_cols}")

    if "ISO_A3" in worldmap.columns:
        worldmap.rename(columns={"ISO_A3": "Alpha-3 code"}, inplace=True)
    else:
        raise KeyError("Expected column 'ISO_A3' not found in shapefile.")
    worldmap = pd.merge(worldmap, country_data[["Alpha-2 code", "Alpha-3 code", "pop_est"]],
                        on="Alpha-3 code", how="left")

    worldmap["freq"] = worldmap["Alpha-2 code"].map(freqs)
    #worldmap["freq"].fillna(0, inplace=True)
    worldmap["freq"] = worldmap["freq"].fillna(0)
    worldmap.replace(0, np.nan, inplace=True)
    

    if relative:
        worldmap = worldmap.rename(columns={"freq": "absolute_freq"})
        worldmap["freq"] = (worldmap["absolute_freq"] / worldmap["pop_est"]) * 100

    fig, ax = plt.subplots(1, 1)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    ax.set_xticks([])
    ax.set_yticks([])
    if panel_label:
        ax.text(
            0.005, 0.97, panel_label, transform=ax.transAxes,
            fontsize=32, fontweight='normal', va='top', ha='left'
        )

    if europe:
        minx, miny, maxx, maxy = [-1500000, 4000000, 4300000, 8500000]
        ax.set_xlim(minx, maxx)
        ax.set_ylim(miny, maxy)
        ax.set_frame_on(False)

    #cmap = alt_cmp if not relative else newcmp
    #cmap = plt.cm.viridis
    
    cmap_absolute = LinearSegmentedColormap.from_list("CB_Blues", [
        "#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"
    ], N=10)
    
    cmap_relative = LinearSegmentedColormap.from_list("CB_Purples", [
        "#fcfbfd", "#efedf5", "#dadaeb", "#bcbddc", "#9e9ac8", "#807dba", "#6a51a3", "#54278f"
    ], N=10)
    
    cmap = cmap_relative if relative else cmap_absolute

    label = "number of taxonomists" if not relative else "percentage of population"
    
    worldmap.plot(
        column='freq',
        ax=ax,
        legend=True,
        missing_kwds={"color": "lightgrey"},
        legend_kwds={"label": label},
        cax=cax,
        cmap=cmap,
        edgecolor="black"
    )
    
    ax.set_frame_on(False)
    cax.set_ylabel(label, fontsize=16)
    cax.tick_params(labelsize=14)
    #ax.set_xlabel(label, fontsize=14, labelpad=12)
    
    plt.tight_layout()
    output_file = str(map_path) + ".jpg"
    plt.savefig(output_file, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[DEBUG] Map saved to: {output_file}")

def save_freq_data(freqs_dict, output_path):
    freq_df = pd.DataFrame(list(freqs_dict.items()), columns=['Country Code', 'Frequency'])
    freq_df.to_csv(output_path, index=False)
    print(f"Underlying data saved to {output_path}")

# Load and process author data
authors_path = interim_dir / "single_authors_of_taxonomic_articles.pkl"
print(f"[DEBUG] Trying to load: {authors_path}")
if not authors_path.exists():
    print(f"Error: File not found at {authors_path}")
    exit()

authors = pd.read_pickle(authors_path)
countries_freq = freq_countries(authors)
save_freq_data(countries_freq, reports_dir / "countries_freq_all.csv")
plot_country_freqs(countries_freq, reports_dir / "map_authors")

eu_authors_path = interim_dir / "country_taxonomic_authors_no_duplicates.pkl"
eu_authors = pd.read_pickle(eu_authors_path)
countries_freq = freq_countries(eu_authors)
save_freq_data(countries_freq, reports_dir / "countries_freq_europe.csv")
#plot_country_freqs(countries_freq, reports_dir / "map_authors_europe", europe=True)
#plot_country_freqs(countries_freq, reports_dir / "map_authors_europe_relative", europe=True, relative=True)
plot_country_freqs(countries_freq, reports_dir / "map_authors_europe", europe=True, panel_label="A")
plot_country_freqs(countries_freq, reports_dir / "map_authors_europe_relative", europe=True, relative=True, panel_label="B")



eujot_freq = freq_countries(eu_authors[eu_authors["source_issn_l"] == "2118-9773"])
save_freq_data(eujot_freq, reports_dir / "countries_freq_eujot.csv")
plot_country_freqs(eujot_freq, reports_dir / "map_eujot", europe=True)
plot_country_freqs(eujot_freq, reports_dir / "map_eujot_relative", europe=True, relative=True)

print("Authors' institutions plotted onto world maps. Results in reports/figures.")


def calculate_population_correlation(freqs_dict, population_file):
    # Load population data
    colnames = ["id", "Country", "Alpha-2 code", "Alpha-3 code", "pop_est"]
    population_df = pd.read_csv(population_file, sep="\t", skiprows=1, names=colnames)

    # Clean population data
    population_df["Alpha-2 code"] = population_df["Alpha-2 code"].str.strip()
    population_df["pop_est"] = pd.to_numeric(population_df["pop_est"], errors="coerce")
    population_df = population_df.dropna(subset=["Alpha-2 code", "pop_est"])

    # Convert frequency dictionary to DataFrame
    freq_df = pd.DataFrame(list(freqs_dict.items()), columns=["Alpha-2 code", "freq"])
    freq_df["Alpha-2 code"] = freq_df["Alpha-2 code"].str.strip()

    # Merge on Alpha-2 ISO code
    merged = pd.merge(freq_df, population_df[["Alpha-2 code", "pop_est"]], on="Alpha-2 code", how="inner")

    # Drop any remaining NaNs
    merged = merged.dropna(subset=["freq", "pop_est"])

    # Report match stats
    total_freq_countries = len(freq_df)
    matched_countries = len(merged)
    unmatched_countries = total_freq_countries - matched_countries
    unmatched_codes = set(freq_df["Alpha-2 code"]) - set(merged["Alpha-2 code"])

    print(f"[INFO] Total countries in frequency data: {total_freq_countries}")
    print(f"[INFO] Countries matched with population data: {matched_countries}")
    print(f"[INFO] Countries without population data: {unmatched_countries}")
    if unmatched_codes:
        print("[WARNING] Unmatched country codes:")
        for code in sorted(unmatched_codes):
            print(f"  - {code}")

    # Compute correlation
    corr_coef, p_value = pearsonr(merged["freq"], merged["pop_est"])
    print(f"[RESULT] Pearson correlation coefficient: {corr_coef:.4f} (p = {p_value:.4g})")

    return corr_coef, p_value, merged

def plot_population_vs_frequency(freqs_dict, population_file):
    # Load population data
    colnames = ["id", "Country", "Alpha-2 code", "Alpha-3 code", "pop_est"]
    population_df = pd.read_csv(population_file, sep="\t", skiprows=1, names=colnames)
    population_df["Alpha-2 code"] = population_df["Alpha-2 code"].str.strip()
    population_df["pop_est"] = pd.to_numeric(population_df["pop_est"], errors="coerce")
    population_df = population_df.dropna(subset=["Alpha-2 code", "pop_est"])

    # Frequency data
    freq_df = pd.DataFrame(list(freqs_dict.items()), columns=["Alpha-2 code", "freq"])
    freq_df["Alpha-2 code"] = freq_df["Alpha-2 code"].str.strip()

    # Merge
    merged = pd.merge(freq_df, population_df[["Alpha-2 code", "pop_est"]], on="Alpha-2 code", how="inner")
    merged = merged.dropna(subset=["freq", "pop_est"])

    # Correlation
    corr_coef, p_value = pearsonr(merged["freq"], merged["pop_est"])

    # Plot
    plt.figure(figsize=(8, 6))
    plt.scatter(merged["pop_est"], merged["freq"], alpha=0.7)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Population (log scale)", fontsize=12)
    plt.ylabel("Taxonomist Frequency (log scale)", fontsize=12)
    plt.title(
        f"Population vs. Taxonomist Frequency\nPearson r = {corr_coef:.2f}, p = {p_value:.2g}",
        fontsize=14
    )
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()

    # Optional: Save the plot
    plot_path = reports_dir / "plot_population_vs_frequency.png"
    plt.savefig(plot_path, dpi=300)
    plt.close()

population_file_path = external_dir / "country_codes_and_population.tsv"
calculate_population_correlation(countries_freq, population_file_path)
plot_population_vs_frequency(countries_freq, external_dir / "country_codes_and_population.tsv")