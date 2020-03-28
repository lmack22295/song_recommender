import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import util


class GeneratePlaylistAPI:

    def __init__(self, song_data, doc2vec_model, spotify_api):
        self.song_data = song_data
        self.doc2vec_model = doc2vec_model
        self.spotify_api = spotify_api

    def generate_user_playlist_recs(self, song_name, song_recs):
        playlist = self.spotipy_api.user_playlist_create(user='lmack22295', name="song_recs_{}".format(song_name))
        print("Creating Playlist...")
        self.spotify_api.user_playlist_add_tracks(
            user='lmack22295',
            playlist_id=playlist['id'],
            tracks=song_recs.track_id.values
        )
        print("Playlist has been loaded to Spotify")

    def lookup_artist(self, artist_name):
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
        similarity = cosine_similarity(self.doc2vec_model,
                                       self.doc2vec_model[song_idx:song_idx + 1, :])[:, 0]
        song_recs = self.generate_song_recs_data(similarity, num_songs)

        ans = input("Should I create this playlist on Spotify? - Enter y or n.")
        if ans.lower() == 'y':
            return self.generate_user_playlist_recs(song_name, artist_name, song_recs)
        return song_recs

    def generate_song_recs_data(self, similarity_scores, num_songs):
        song_recs = \
            pd.DataFrame(
                {'song_name': self.song_data.song_name,
                 'artist': self.song_data.artist_name,
                 'similarity': similarity_scores,
                 'track_id': self.song_data.id}).drop_duplicates(
                ['song_name', 'artist']
            ).sort_values('similarity', ascending=False)[:num_songs]
        print(song_recs[['song_name', 'artist_name']])
        return song_recs