from wordcloud import WordCloud, STOPWORDS
import pandas as pd
import matplotlib.pyplot as plt
import re
from pathlib import Path

# ── PATH SETUP ───────────────────────────────────────────────────

# Resolve root directory (assumes script is in src/visualization/)
this_file = Path(__file__).resolve()
root_dir = this_file.parents[2]  # Go up to the project root

# Define data and report directories
data_path = root_dir / "data" / "processed" / "taxonomic_articles_with_subjects.pkl"
output_dir = root_dir / "reports" / "figures"
output_dir.mkdir(parents=True, exist_ok=True)

# ── STOPWORDS SETUP ──────────────────────────────────────────────

additional_stopwords = [
    "one", "two", "three", "four", "five", "et", "sp", "taxonomy",
    "taxonomic", "taxon", "checklist", "nov", "new", "species", "novel",
    "genus", "genera"
] + list("abcdefghijklmnopqrstuvwxyz1234567890")

stopwords = STOPWORDS.copy()
stopwords.update(additional_stopwords)

# ── HELPER FUNCTIONS ─────────────────────────────────────────────

def clean_word(word):
    return re.sub(r"[^\w\s]", "", word).lower()

def wordcloud_abstracts(df, name):
    abstract_words = df["abstract_inverted_index"]
    abstract_words = list(filter(None, abstract_words))
    num_articles = len(abstract_words)

    frequencies = {}
    for pub in abstract_words:
        for word, indices in pub.items():
            word = clean_word(word)
            if word in frequencies:
                frequencies[word] += len(indices)
            elif word.lower() not in stopwords:
                frequencies[word] = len(indices)

    wordcloud = WordCloud(
        stopwords=stopwords,
        background_color="white",
        width=2000,
        height=1000,
        colormap="viridis",
        max_words=500,
        normalize_plurals=True,
    ).fit_words(frequencies)

    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")

    # Save as PNG and TIFF
    png_path = output_dir / "FigS2.png"
    tiff_path = output_dir / "FigS2.tif"
    plt.savefig(png_path, format="png", dpi=600, bbox_inches="tight")
    plt.savefig(tiff_path, format="tiff", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    plt.show()

    # Output summary
    print(f"Figure S2: A word cloud to visualise the most common words occurring in title and abstract of the {num_articles} articles found. This gives a visual representation of the subjects of the articles and a qualitative check that we have predominantly filtered for taxonomic articles.")
    print(f"Additional stopwords used: {', '.join(sorted(additional_stopwords))}")
    print(f"Word cloud saved as:\nPNG: {png_path}\nTIFF: {tiff_path}")

# ── RUN SCRIPT ───────────────────────────────────────────────────

articles = pd.read_pickle(data_path)
wordcloud_abstracts(articles, "european_taxonomic_articles")
