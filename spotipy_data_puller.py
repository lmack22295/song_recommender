import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
import pandas as pd
import numpy as np

class SpotipyDataPuller:

    def __init__(self, client_id, client_secret):
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        # spotify object to access API #chosen artist
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def get_artist_uri(self, artist_name):
        result = self.sp.search(artist_name)  # search query
        for i in result['tracks']['items']:
            if (i['artists'][0]['name'].lower() == artist_name.lower()):
                return i['artists'][0]['uri']
        print("Could not find uri for {}".format(artist_name))
        return None

    def get_album_info_for_artist(self, name):
        # Extract Artist's uri
        artist_uri = self.get_artist_uri(name)
        # Pull all of the artist's albums
        sp_albums = self.sp.artist_albums(artist_uri, album_type='album')
        # Store artist's albums' names' and uris in separate lists
        album_names = []
        album_uris = []
        for i in range(len(sp_albums['items'])):
            album_names.append(sp_albums['items'][i]['name'])
            album_uris.append(sp_albums['items'][i]['uri'])

        print("Successfully pulled albums from Spotify API for {}".format(name))
        return album_uris, album_names

    def get_genres_from_artist(self, artist_name):
        artist_uri = self.get_artist_uri(artist_name)
        return self.sp.artist(artist_uri)['genres']

    def get_album_tracks(self, album_uri, album_name):
        # Create keys-values of empty lists inside nested dictionary for album
        album_dict = dict()
        album_dict['album'] = []  # create empty list
        album_dict['track_number'] = []
        album_dict['id'] = []
        album_dict['song_name'] = []
        album_dict['song_uri'] = []
        tracks = self.sp.album_tracks(album_uri)  # pull data on album tracks
        for n in range(len(tracks['items'])):  # for each song track
            album_dict['album'].append(album_name)  # append album name tracked via album_count
            album_dict['track_number'].append(tracks['items'][n]['track_number'])
            album_dict['id'].append(tracks['items'][n]['id'])
            album_dict['song_name'].append(tracks['items'][n]['name'])
            album_dict['song_uri'].append(tracks['items'][n]['uri'])
        return album_dict

    def get_song_metadata_from_album(self, album_uris, album_names):
        spotify_albums = dict()
        for uri, name in zip(album_uris, album_names):
            spotify_albums[uri] = self.get_album_tracks(uri, name)

        track_data = pd.DataFrame()
        for k in spotify_albums.keys():
            track_data = track_data.append(pd.DataFrame(spotify_albums[k]))

        return track_data

    def build_artist_genre_data(self, artist_list):
        artist_genres = pd.DataFrame()
        for artist in tqdm(artist_list):
            try:
                artist_genres = artist_genres.append(
                    pd.DataFrame({'artist': artist, 'genres': get_genres_from_artist(artist)}))
            except Exception:
                ""
        return artist_genres

    def audio_features(self, uris):
        # Add new key-values to store audio features
        acousticness = []
        danceability = []
        energy = []
        instrumentalness = []
        liveness = []
        loudness = []
        speechiness = []
        tempo = []
        valence = []
        popularity = []
        successful_uris = []

        for track in tqdm(uris):
            # Pull audio features per track
            features = self.sp.audio_features(track)
            if features != [None]:
                # Append to relevant key-value
                acousticness.append(features[0]['acousticness'])
                danceability.append(features[0]['danceability'])
                energy.append(features[0]['energy'])
                instrumentalness.append(features[0]['instrumentalness'])
                liveness.append(features[0]['liveness'])
                loudness.append(features[0]['loudness'])
                speechiness.append(features[0]['speechiness'])
                tempo.append(features[0]['tempo'])
                valence.append(features[0]['valence'])
                # Popularity is stored elsewhere
                pop = self.sp.track(track)
                popularity.append(pop['popularity'])
                successful_uris.append(track)

                pd.DataFrame({'uri': successful_uris,
                              'danceability': danceability,
                              'energy': energy,
                              'accousticness': acousticness,
                              'instrumentalness': instrumentalness,
                              'liveness': liveness,
                              'loudness': loudness,
                              'speechiness': speechiness,
                              'tempo': tempo,
                              'valence': valence,
                              'popularity': popularity})

        return pd.DataFrame({'uri': uris,
                             'danceability': danceability,
                             'energy': energy,
                             'accousticness': acousticness,
                             'instrumentalness': instrumentalness,
                             'liveness': liveness,
                             'loudness': loudness,
                             'speechiness': speechiness,
                             'tempo': tempo,
                             'valence': valence,
                             'popularity': popularity})

    def build_artist_song_dataset(self, artist_list, get_genres=False):
        song_metadata = pd.DataFrame()
        audio_metadata = pd.DataFrame()
        artist_genres = pd.DataFrame()
        for artist in tqdm(artist_list):
            print("Pulling data for {}".format(artist))
            try:
                album_uris, album_names = self.get_album_info_for_artist(artist)
                curr_song_metadata = self.get_song_metadata_from_album(album_uris, album_names).assign(
                    artist_name=lambda x: artist)
                song_metadata = song_metadata.append(curr_song_metadata)

                print("Pulling audio features from Spotify API for songs by {}".format(artist))
                curr_audio_data = self.audio_features(curr_song_metadata.song_uri.values)
                audio_metadata = audio_metadata.append(curr_audio_data)
                print("Successfully pulled audio features from Spotify API for {} songs by {}".format(len(audio_metadata),
                                                                                                          artist))

                if get_genres:
                    artist_genres = artist_genres.append(self.get_genres_from_artist(artist))
                print("Data for {} albums and genres has been collected".format(artist))
            except Exception:
                print("Failed to collect data for {} albums and genres".format(artist))
        return song_metadata, audio_metadata, artist_genres

def update_spotify_audio_dataset(spotify_data_puller):
    song_data = pd.read_csv("master_spotify_song_metadata.csv")
    existing_audio_data = pd.read_csv("master_audio_data.csv")
    song_data = song_data.merge(existing_audio_data, how='left', left_on='song_uri', right_on='uri')
    song_data = song_data[pd.isnull(song_data.tempo)]

    for i in range(int(len(song_data) / 1000)):
        start_idx, end_idx = i*1000, i*1000 + 1000
        curr_audio_data = spotify_data_puller.audio_features(song_data.song_uri.values[start_idx:end_idx])
        audio_data = existing_audio_data.append(curr_audio_data)

        audio_data.to_csv("master_audio_data.csv", index=False)
        print("Stored audio_data for song_uris indexed from {} to {}".format(start_idx, end_idx))

if __name__ == '__main__':
    artist_list = ['Kanye West']

    spotify = SpotipyDataPuller(client_id = ,
                                client_secret = )

    update_spotify_audio_dataset(spotify)
    # for artist in artist_list:
    #     song_data, audio_data, _ = spotify.build_artist_song_dataset([artist])
    #     master_artist_data = song_data.merge(audio_data,
    #                                          left_on='song_uri',
    #                                          right_on='uri')
    #
    #     master_artist_data.to_csv("spotify_artist_data_{}.csv".format(artist))
    #     print("Spotify audio data for artist: {} has been successfully loaded".format(artist))
