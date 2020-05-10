import argparse
import os
import sqlite3
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from sklearn.feature_extraction.text import TfidfVectorizer


"""
This script takes a zettelkasten note filename and sorts the available notes by their similarity
using Term Frequency-Inverse Document Frequency (TF-IDF). The idea is to use this to help one make
connections in their zettelkasten they may have not thought of initially. 

I'm not sure how well this works in practice yet since my zettelkasten is just starting to fill up.
It does seem to find notes I would say are generally related. I have limited the search to print the
top 20 matches.

I currently utilize sirupsen's search tool to use this (https://github.com/sirupsen/zk/blob/master/bin/zks). 
I have a second search function for when I want to try TF-IDF that puts 'python --filename "zk filename.md" |' in
front of the fzf. This will give you a view to scroll through related files with the same opening and linking commands
as zk-search. 
"""


def vectorize_text(series):
    """
    Uses sklearn text vectorizer. Will do the necessary preprocessing like removing stop words,
    transform to lowercase etc.

    :param series: Pandas Series object
    :return: matrix of tf-idf features
    """
    return TfidfVectorizer().fit_transform(series.values)


def index_from_title(series, title):
    return series[series == title].index


def similarity_index(search_index, vectors):
    """
    Uses cosine similarity to find which documents are the most similar to the file index passed
    in search_index
    :param search_index: Index of file you want similar files to
    :param vectors: Vector of TF-IDF vector features for each document
    :return: Returns the index numbers of the decuments in order of similarity
    """
    cosine_similarities = linear_kernel(vectors[search_index], vectors).flatten()
    return (-cosine_similarities).argsort()


def relevant_titles(df, title, title_col, text_col):
    """
    Uses indexes from similarity_index to sort the DataFrame of notes by similarity
    :param df: DataFame of notes (from zettelkasten database)
    :param title: Title to search for similar files
    :param title_col: Name of column in DataFrame that has titles of each note
    :param text_col: Name of column in DataFrame that has the body of each note
    :return: DataFrame sorted by similarity to the note title passed
    """
    vectors = vectorize_text(df[text_col])
    searching_index = index_from_title(df[title_col], title)
    sim_index = similarity_index(searching_index, vectors)
    return df.iloc[sim_index][title_col].values


class CustomAction(argparse.Action):
    # Needed this to handle white space in filenames passed, even when in quotes idk why
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, " ".join(values))


class TfidfSearch:

    def __init__(self):

        self.zk_path = os.environ['ZK_PATH']
        self.conn = sqlite3.connect(os.path.join(self.zk_path, "index.db"))
        self.cursor = self.conn.cursor()
        self.num_files_to_show = 20

    def application_logic(self, filename):
        df = pd.read_sql("select * from zettelkasten", con=self.conn)
        for file in relevant_titles(df, filename, title_col="title", text_col="body")[:self.num_files_to_show]:
            print(file)

    def run(self):
        parser = argparse.ArgumentParser(description='Process some integers.')
        parser.add_argument('--filename', dest='filename', action=CustomAction, type=str, nargs='+',
                            help='filename to search for similarity')
        args = parser.parse_args()

        self.application_logic(args.filename)


if __name__ == "__main__":
    TfidfSearch().run()
