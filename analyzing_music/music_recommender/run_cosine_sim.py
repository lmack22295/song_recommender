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

def add_audio_features_to_recommendation_vector(vector_data, audio_data):
    audio_feature_list = []
    for j in tqdm(range(len(audio_data))):
        i = audio_data[j:j+1]
        curr_audio_value = [i.tempo.values[0], i.valence.values[0], i.energy.values[0],
                              i.danceability.values[0], i.accousticness.values[0], i.instrumentalness.values[0],
                              i.speechiness.values[0], i.liveness.values[0], i.loudness.values[0]]
        curr_vector_data = vector_data[j]
        audio_feature_list.append(np.append(curr_vector_data, curr_audio_value))
    return np.array(audio_feature_list)

def get_audio_feature_vector(data):
    audio_feature_list = []
    for j in range(len(data)):
        i = data[j:j+1]
        print(j)
        curr_audio_value = [i.tempo.values[0], i.valence.values[0], i.energy.values[0],
                              i.danceability.values[0], i.accousticness.values[0], i.instrumentalness.values[0],
                              i.speechiness.values[0], i.liveness.values[0], i.loudness.values[0]]
        audio_feature_list.append(np.array(curr_audio_value))
    return np.array(audio_feature_list)

print("Applying trained LDA modelto tf-idf lyrics features...")
# topic_probabilities = lda.transform(tfidf)
print("Topic probabilities for song-lyrics have been successfully loaded")
print("Calculating cosine similarity scores of topics probabilities")
# cosine_sims_topics_only = cosine_similarity(topic_probabilities)
print("Cosine similarities have ben successfully calculated")

# audio_feature_vect = get_audio_feature_vector(lyrics)
print("Calculating cosine similarity scores of audio features")
# cosine_sims_audio_only = cosine_similarity(audio_feature_vect)
print("Cosine similarities have ben successfully calculated")

# audio_feature_vector_lda = add_audio_features_to_recommendation_vector(topic_probabilities, lyrics)
lyrics = pd.read_csv("latest_lyrics_data.csv")
doc2vec_matrix = Doc2Vec.load("d2v_updated.model").docvecs.vectors_docs
audio_feature_vector_doc2vec = add_audio_features_to_recommendation_vector(doc2vec_matrix, lyrics)

print("Calculating cosine similarity scores of audio features and topic probabilities")
# cosine_sims_topics_audio = cosine_similarity(audio_feature_vector_lda)

print("Calculating cosine similarity scores of audio features")

print("Calculating cosine similarity scores of audio features and doc2vec outputs")
cosine_sims_doc2vec_audio = cosine_similarity(audio_feature_vector_doc2vec)
pd.DataFrame(cosine_sims_doc2vec_audio, columns=lyrics.song_name).to_pickle("cosine_sims_d2v.pkl")
print("Cosine similarities have ben successfully calculated")