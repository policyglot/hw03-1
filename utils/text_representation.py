import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer

from utils.spacy_tokenizer import spacy_tokenize


def _levels(demographics, d_levels=None, print_levels=False):
    """The demographic levels to iterate over
    
    Parameters
    ----------
    demographics : pd.Series
        Demographic labels
    d_levels : list, default None
        The specific demographic levels desired
    print_levels : bool, default False
        Whether to print the demographic levels
    
    Returns
    -------
    levels : iterable
        The unique (sorted) levels in `demographics`
    """
    levels = demographics.unique()
    if d_levels:
        assert set(d_levels).issubset(levels)
        levels = d_levels
    levels.sort()
    if print_levels:
        print('Levels (in order):', levels, end='\n\n')
    return levels

def _multinomial(corpus, kwargs):
    """Tokens counts by document using the spaCy tokenizer

    Parameters
    ----------
    corpus : array-like
        A collection of documents
    kwargs : dict or None
        Keyword arguments of variable length

    Returns
    -------
    X : scipy.sparse.csr.csr_matrix
        The multinomial representation shape (n_samples, n_features)
    v : list
        Vocabulary
    """
    if kwargs:
        cv = CountVectorizer(tokenizer=spacy_tokenize, **kwargs)
    else:
        cv = CountVectorizer(tokenizer=spacy_tokenize)
    X = cv.fit_transform(corpus)
    v = cv.get_feature_names()
    return X, v

def _tfidf(X):
    """tf-idf representation of a count matrix

    Parameters
    ----------
    X : scipy.sparse.csr.csr_matrix
        `_multinomial()` output

    Returns
    -------
    X_ : scipy.sparse.csr.csr_matrix
        The tf-idf representation
    """
    tt = TfidfTransformer()
    X_ = tt.fit_transform(X)
    return X_

def feature_vectors(corpus, kwargs=None):
    """Multinomial and TF-IDF representations

    Paramaters
    ----------
    corpus : array-like
        A collection of documents
    kwargs : dict, default None
        Keyword arguments of variable length
        See sklearn.feature_extraction.text.CountVectorizer
        for accepted keyword arguments

    Returns
    -------
    count : scipy.sparse.csr.csr_matrix
        The multinomial representation shape (n_samples, n_features)
    tfidf : scipy.sparse.csr.csr_matrix
        The tf-idf representation
    vocab : list
        Vocabulary
    """
    assert isinstance(corpus, (list, pd.Series))
    count, vocab = _multinomial(corpus, kwargs)
    tfidf = _tfidf(count)
    return count, tfidf, vocab

def tfidf_matrices(corpus, demographics, vocabulary=None):
    """For creating tfidf matrices of:
        * documents
        * demographic levels

    Parameters
    ----------
    corpus : pd.Series
        A collection of documents
    demographics : pd.Series
        Demographic labels
    vocabulary : list, default None
        Tokens to consider

    Returns
    -------
    doc_level, demo_level : (sparse matrix, sparse matrix)
        Document-level tfidf matrix
        Demographic-level tfidf matrix

    Notes
    -----
    The "demographic levels" tfidf matrix represents
    demographic archetypes. Token counts are aggregated
    by demographic level prior to creating the tfidf
    representation.
    """
    assert (isinstance(corpus, pd.Series) and
            isinstance(demographics, pd.Series))
    assert corpus.shape[0] == demographics.shape[0]
    doc_level, _ = _multinomial(corpus, vocabulary=vocabulary)
    levels = _levels(demographics)
    splits = []
    for level in levels:
        mask = demographics.values == level
        splits.append(np.asarray(doc_level[mask].sum(axis=0))[0])
    demo_level = np.stack(splits)
    return _tfidf(doc_level), _tfidf(demo_level)
