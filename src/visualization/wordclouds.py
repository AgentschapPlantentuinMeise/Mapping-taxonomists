from wordcloud import WordCloud, STOPWORDS
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import re
import os

# Additional stopwords
additional_stopwords = ["one", "two", "three", "four", "five", "et", "sp", "taxonomy", "taxonomic", "taxon", "checklist", "nov", "new", "species", "novel", "genus", "genera"] + list("abcdefghijklmnopqrstuvwxyz1234567890")

# Combine additional stopwords with the default set
stopwords = STOPWORDS.copy()
stopwords.update(additional_stopwords)

# Ensure output directory exists
output_dir = "../../reports/figures/"
os.makedirs(output_dir, exist_ok=True)

# Helper function to clean words
def clean_word(word):
    return re.sub(r"[^\w\s]", "", word).lower()
    
def wordcloud_abstracts(df, name):     
    abstract_words = df["abstract_inverted_index"]
    abstract_words = list(filter(None, abstract_words))
    num_articles = len(abstract_words)  # Count the number of articles used
    
    frequencies = {}
    
    for pub in abstract_words:
        for word, indices in pub.items():
            word = clean_word(word)
            # add new word to frequencies
            if word in frequencies:
                frequencies[word] += len(indices)
            # add new words that are not stopwords
            elif word.lower() not in stopwords: 
                frequencies[word] = len(indices)
    
    # make wordcloud of abstract word frequencies
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
    # save wordcloud for this concept
    # Save the word cloud as PNG and TIFF
    png_path = os.path.join(output_dir, f"wordcloud_{name}.png")
    tiff_path = os.path.join(output_dir, f"wordcloud_{name}.tif")
    
    plt.savefig(png_path, format="png", dpi=600, bbox_inches="tight")
    plt.savefig(tiff_path, format="tiff", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    plt.show()
    
    # Print the figure description and list of additional stopwords
    print(f"Figure S2: A word cloud to visualise the most common words occurring in title and abstract of the {num_articles} articles found. This gives a visual representation of the subjects of the articles and a qualitative check that we have predominantly filtered for taxonomic articles.")
    print(f"As certain words had been used to select the articles in the first place in addition to the default stopwords of the package the following words were used: {', '.join(sorted(additional_stopwords))}")
    print(f"Word cloud saved as:\nPNG: {png_path}\nTIFF: {tiff_path}")

articles = pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")
wordcloud_abstracts(articles, "european_taxonomic_articles")
