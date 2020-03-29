from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
import pandas as pd
import re
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import util
from utils import add_audio_features_to_recommendation_vector, get_audio_feature_vector
import pickle


def get_cosine_similarities():
    print("Applying trained LDA modelto tf-idf lyrics features...")
    # topic_probabilities = lda.transform(tfidf)
    print("Topic probabilities for song-lyrics have been successfully loaded")
    print("Calculating cosine similarity scores of topics probabilities")
    # cosine_sims_topics_only = cosine_similarity(topic_probabilities)
    print("Cosine similarities have been successfully calculated")

    # audio_feature_vect = get_audio_feature_vector(lyrics)
    print("Calculating cosine similarity scores of audio features")
    # cosine_sims_audio_only = cosine_similarity(audio_feature_vect)
    print("Cosine similarities have been successfully calculated")

    # audio_feature_vector_lda = add_audio_features_to_recommendation_vector(topic_probabilities, lyrics)
    lyrics = pd.read_csv("./data/latest_lyrics_data.csv")
    doc2vec_matrix = Doc2Vec.load("d2v_updated.model").docvecs.vectors_docs

    print("Adding audio features to doc2vec matrix")
    audio_feature_vector_doc2vec = add_audio_features_to_recommendation_vector(doc2vec_matrix, lyrics)

    print("Calculating cosine similarity scores of audio features and topic probabilities")
    # cosine_sims_topics_audio = cosine_similarity(audio_feature_vector_lda)

    print("Calculating cosine similarity scores of audio features")

    print("Calculating cosine similarity scores of audio features and doc2vec outputs")
    cosine_sims_doc2vec_audio = cosine_similarity(audio_feature_vector_doc2vec)
    print("Cosine similarities have been successfully calculated")
    pd.DataFrame(cosine_sims_doc2vec_audio, columns=lyrics.song_name).to_pickle("cosine_sims_d2v.pkl")
    print("Cosine similarities have been successfully stored")


def get_doc2vec_audio_features():
    """
    :return:
        Load lyrics dataset
        Train doc2vec model on song-lyrics
        Merge spotify audio features with doc2vec scores
    """
    try:
        lyrics = pd.read_pickle("./data/latest_model_data.pkl")
        doc2vec_matrix = Doc2Vec.load("d2v_updated.model").docvecs.vectors_docs
    except Exception:
        lyrics = pd.read_csv("./data/latest_lyrics_data.csv")
        doc2vec_model = train_doc2vec_model(lyrics)
        doc2vec_matrix = doc2vec_model.docvecs.vectors_docs

    print("Adding audio features to doc2vec matrix")
    audio_feature_vector_doc2vec = add_audio_features_to_recommendation_vector(doc2vec_matrix, lyrics)
    with open('./data/doc2vec_audio_lyrics_features.pkl', 'wb') as write_file:
        pickle.dump(audio_feature_vector_doc2vec, write_file)
    return audio_feature_vector_doc2vec


def train_doc2vec_model(lyrics_data):
    """
    :param lyrics_data: pandas DataFrame of song-lyrics
    :return: Train doc2vec model on stemmed song lyrics
    """
    from gensim.models.doc2vec import Doc2Vec, TaggedDocument
    from nltk.tokenize import word_tokenize

    print("Tagging lyrics data for doc2vec algorithm")
    tagged_data = [TaggedDocument(words=word_tokenize(str(_d).lower()), tags=[str(i)]) for i, _d in enumerate(lyrics_data.lyrics_clean_stemmed)]
    max_epochs = 7
    vec_size = 20
    alpha = 0.025

    model = Doc2Vec(vector_size=vec_size,
                    alpha=alpha,
                    min_alpha=0.00025,
                    min_count=1,
                    dm=1)

    print("Building vocabulary for doc2vec algorithm")
    model.build_vocab(tagged_data)

    print("Training doc2vec model")
    for epoch in range(max_epochs):
        print('iteration {0}'.format(epoch))
        model.train(tagged_data,
                    total_examples=model.corpus_count,
                    epochs=model.iter)
        # decrease the learning rate
        model.alpha -= 0.0002
        # fix the learning rate, no decay
        model.min_alpha = model.alpha

    model.save("d2v_updated.model")
    print("Doc2Vec Model Saved")
    lyrics_data.to_pickle("./data/latest_model_data.pkl")
    return model
