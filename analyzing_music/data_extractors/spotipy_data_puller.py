import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
import pandas as pd
import numpy as np

class SpotipyDataPuller:
    AUDIO_FEATURE_NAMES = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness',
                           'loudness', 'speechiness', 'tempo', 'valence', 'popularity', 'uri']

    def __init__(self, client_id, client_secret):
        client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        # spotify object to access API #chosen artist
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def get_artist_uri(self, artist_name):
        """
        :param artist_name: artist_name
        :return: Spotify uri associated with artist_name
        """
        result = self.sp.search(artist_name)  # search query
        for i in result['tracks']['items']:
            if (i['artists'][0]['name'].lower() == artist_name.lower()):
                return i['artists'][0]['uri']
        print("Could not find uri for {}".format(artist_name))
        return None

    def get_album_info_for_artist(self, name):
        """
        :param name: artist_name
        :return: Spotify uri and album name for all albums by `name`
        """
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
        """
        :param artist_name: artist_name
        :return: List of genres associated with `artist_name` from Spotify API
        """
        artist_uri = self.get_artist_uri(artist_name)
        return self.sp.artist(artist_uri)['genres']

    def get_album_tracks(self, album_uri, album_name):
        """
        :param album_uri: Spotify unique-identifier for album
        :param album_name: album_name
        :return: meta-data for all songs in album_name from Spotify API
        """
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
        """
        :param album_uris: list of unique-identifiers of albums
        :param album_names: list of album_names
        :return: meta-data from Spotify API for all songs in the list of album_names
        """
        spotify_albums = dict()
        for uri, name in zip(album_uris, album_names):
            spotify_albums[uri] = self.get_album_tracks(uri, name)

        track_data = pd.DataFrame()
        for k in spotify_albums.keys():
            track_data = track_data.append(pd.DataFrame(spotify_albums[k]))

        return track_data

    def build_artist_genre_data(self, artist_list):
        """
        :param artist_list: list of artist_names
        :return:
        """
        artist_genres = pd.DataFrame()
        for artist in tqdm(artist_list):
            try:
                artist_genres = artist_genres.append(
                    pd.DataFrame({'artist': artist, 'genres': self.get_genres_from_artist(artist)}))
            except Exception:
                ""
        return artist_genres

    def audio_features(self, uris):
        """
        :param uris: list of song_uris
        :return: List of audio features for the associated song_uris from Spotify API
        """
        # Initialize dictionary of audio features
        audio_dict = dict()
        for feat in self.AUDIO_FEATURE_NAMES:
            audio_dict[feat] = []

        for track in tqdm(uris):
            # Pull audio features per track
            features = self.sp.audio_features(track)
            if features != [None]:
                # Append to relevant key-value
                for feature_name in self.AUDIO_FEATURE_NAMES:
                    # Get value of feature_name for track
                    curr_feature_value = self.sp.track(track) if feature_name == 'popularity'\
                                                              else track if feature_name == 'uri' \
                                                              else features[0][feature_name]
                    # Add audio_features for `track` to feature set
                    curr_feature_value_arr = audio_dict[feature_name]
                    curr_feature_value_arr.append(curr_feature_value)
                    audio_dict[feature_name] = curr_feature_value_arr

        return pd.DataFrame(audio_dict)


    def build_artist_song_dataset(self, artist_list, get_genres=False):
        """
        :param artist_list: list of artist names
        :param get_genres: if True, return the genre of all artists in artist_list
        :return:

        For each artist:
            1. Get info (spotify uri and name) for all albums by the artist from Spotify API
            2. Get metadata for all songs from each album from Spotify API
            3. if `get_genres == True` then get artist genres from Spotify API
        """
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
    audio_data = pd.read_csv("master_audio_data.csv")
    song_data = song_data.merge(audio_data, how='left', left_on='song_uri', right_on='uri')
    song_data = song_data[pd.isnull(song_data.tempo)]
    
    for i in range(int(len(song_data) / 1000)):
        start_idx, end_idx = i*1000, i*1000 + 1000
        curr_audio_data = spotify_data_puller.audio_features(song_data.song_uri.values[start_idx:end_idx])
        audio_data = audio_data.append(curr_audio_data)

        audio_data.to_csv("master_audio_data.csv", index=False)
        print("Stored audio_data for song_uris indexed from {} to {}".format(start_idx, end_idx))

if __name__ == '__main__':
    artist_list = ['Alicia Keys']

    spotify = SpotipyDataPuller(client_id = '7085a21ce4124b3e89db61d750b133a7',
                                client_secret = '2b02da51f99f4470a1c2ef91f28a0957')

    update_spotify_audio_dataset(spotify)
    # for artist in artist_list:
    #     song_data, audio_data, _ = spotify.build_artist_song_dataset([artist])
    #     master_artist_data = song_data.merge(audio_data,
    #                                          left_on='song_uri',
    #                                          right_on='uri')
    #
    #     master_artist_data.to_csv("spotify_artist_data_{}.csv".format(artist))
    #     print("Spotify audio data for artist: {} has been successfully loaded".format(artist))
