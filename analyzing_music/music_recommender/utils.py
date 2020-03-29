from tqdm import tqdm
import numpy as np

def add_audio_features_to_recommendation_vector(vector_data, audio_data):
    """
    :param vector_data: (n x m) vector of data describing n songs with m features
    :param audio_data: (n x k) vector of audio data with k audio features per song
    :return: (n x (m + k)) vector of song-data for song recommendations & similarity scoring
    """
    audio_feature_list = []
    for j in tqdm(range(len(audio_data))):
        i = audio_data[j:j+1]
        curr_audio_value = [i.tempo.values[0], i.valence.values[0], i.energy.values[0],
                              i.danceability.values[0], i.acousticness.values[0], i.instrumentalness.values[0],
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