import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.util import prompt_for_user_token
from run_cosine_sim import get_cosine_similarities, get_doc2vec_audio_features
import pickle


class GeneratePlaylistAPI:

    def __init__(self, song_data, lyrics_features, client_id, client_secret):
        self.song_data = song_data
        self.lyrics_features = lyrics_features

        token = prompt_for_user_token('lmack22295',
                                           scope='playlist-modify-private,playlist-modify-public',
                                           client_id=client_id,
                                           client_secret=client_secret,
                                           redirect_uri="https://localhost:8080")
        sp = spotipy.Spotify(auth=token)
        self.spotify_api = sp

    def generate_user_playlist_recs(self, song_name, song_recs):
        self.spotify_api.user_playlist_create(user='lmack22295', name="song_recs_{}".format(song_name))
        playlist = self.spotify_api.user_playlist_create(user='lmack22295',
                                                         name="song_recs_{}".format(song_name))
        print("Creating Playlist...")
        self.spotify_api.user_playlist_add_tracks(
            user='lmack22295',
            playlist_id=playlist['id'],
            tracks=song_recs.track_id.values
        )
        print("Playlist has been loaded to Spotify")

    def lookup_artist(self):
        artist_name = input("Which artist's songs would you like to select from?")
        song_list = list(self.song_data[self.song_data.artist_name == artist_name].song_name.values)
        print("Here is a list of songs by {}".format(artist_name))
        print()
        print(song_list)
        print()
        print()
        print()
        song_lookup = input("Which song would you like to generate a playlist for?")
        print()
        print()
        print()
        try:
            self.get_similar_songs(song_lookup, artist_name)
        except Exception:
            print("Song {} by {} Doesn't Exist".format(song_lookup, artist_name))

    def get_similar_songs(self, song_name, artist_name=None, num_songs=20):
        if artist_name:
            song_idx = \
                self.song_data[(self.song_data.song_name == song_name) &
                               (self.song_data.artist_name == artist_name)].index.values[0]
        else:
            song_idx = self.song_data[self.song_data.song_name == song_name].index.values[0]

        # Calculate cosine similarity scores between song_name and all other songs
        similarity = cosine_similarity(self.lyrics_features, self.lyrics_features[song_idx:song_idx + 1, :])[:, 0]
        song_recs = self.generate_song_recs_data(similarity, num_songs)

        ans = input("Should I create this playlist on Spotify? - Enter y or n.")
        if ans.lower() == 'y':
            return self.generate_user_playlist_recs(song_name, song_recs)
        return song_recs


    def generate_song_recs_data(self, similarity_scores, num_songs):
        song_recs = \
            pd.DataFrame(
                {'song_name': self.song_data.song_name,
                 'artist_name': self.song_data.artist_name,
                 'similarity': similarity_scores,
                 'track_id': self.song_data.id}).drop_duplicates(
                ['song_name', 'artist_name']
            ).sort_values('similarity', ascending=False)[:num_songs]
        print(song_recs[['song_name', 'artist_name']])
        return song_recs


if __name__ == '__main__':
    try:
        with open('./data/doc2vec_audio_lyrics_features.pkl', 'rb') as read_file:
            lyrics_features = pickle.load(read_file)
        song_data = pd.read_pickle("./data/latest_model_data.pkl")
    except Exception:
        song_data = pd.read_pickle("./data/latest_lyrics_data.pkl")
        # load similarity scores
        lyrics_features = get_doc2vec_audio_features()

    # set up spotify api
    client_id = '7085a21ce4124b3e89db61d750b133a7'
    client_secret = '2b02da51f99f4470a1c2ef91f28a0957'

    playlist = GeneratePlaylistAPI(song_data=song_data,
                                   lyrics_features=lyrics_features,
                                   client_id=client_id,
                                   client_secret=client_secret)

    keep_lookup = 'y'
    while keep_lookup == 'y':
        playlist.lookup_artist()
        keep_lookup = input("Should I lookup another song? (y/n)")
