from analyzing_music.data_extractors.spotipy_data_puller import SpotipyDataPuller
from analyzing_music.data_extractors.genius_data_puller import GeniusDataPuller
from analyzing_music.data_extractors import lyrics_cleaner
import pandas as pd


if __name__ == '__main__':

    lyrics_filepath = "./data/latest_lyrics_data.csv"
    artist_filename = "./data/spotify_artist_data_{}.csv"
    audio_filepath = "./data/master_data/master_audio_data.csv"
    master_read_filepath = "./data/master_data/master_lyrics_data.csv"

    spotify_client_id = input('Input your spotify client_id')
    spotify_client_secret = input('Input your spotify client secret')

    artist_list = \
        ['Rex Orange County']
    latest_lyrics_data = pd.read_csv(lyrics_filepath)
    master_lyrics_data = pd.read_csv(master_read_filepath)

    # initialize spotify data puller to access audio data from spotify API
    spotify = SpotipyDataPuller(client_id=spotify_client_id,
                                client_secret=spotify_client_secret)

    for artist in artist_list:
        try:
            master_artist_data = pd.read_csv(artist_filename.format(artist))
            print("Successfully retrieved {} songs from cache".format(artist))
        except:
            # Get Spotify song_metadata and audio features from Spotify API
            song_data, audio_data, _ = spotify.build_artist_song_dataset([artist])

            master_artist_data = song_data.merge(audio_data,
                                                 left_on='song_uri',
                                                 right_on='uri')
            master_artist_data.to_csv(artist_filename.format(artist))

        # filter songs:
        existing_uris = latest_lyrics_data.uri.values
        master_artist_data = master_artist_data[master_artist_data['song_uri'].apply(lambda x: x not in existing_uris)]

        if not master_artist_data.empty:
            genius = GeniusDataPuller(master_artist_data.artist_name.values,
                                      master_artist_data.song_name.values,
                                      master_artist_data.song_uri.values)

            # get lyrics data from genius
            song_dataset = genius.build_song_lyrics_data()

            if not song_dataset.empty:
                try:
                    # merge lyrics + audio data
                    curr_lyrics_data = song_dataset.merge(master_artist_data,
                                                          left_on=['artist_name', 'song_name', 'uri'],
                                                          right_on=['artist_name', 'song_name', 'uri'])

                    # clean, stem, lemmatize, and remove english stopwords
                    non_null_lyrics_data = curr_lyrics_data[pd.notnull(curr_lyrics_data.lyrics)]
                    null_lyrics_data = curr_lyrics_data[pd.isnull(curr_lyrics_data.lyrics)]
                    if not non_null_lyrics_data.empty:
                        non_null_lyrics_data = lyrics_cleaner.clean_lyrics_data(non_null_lyrics_data)
                    curr_lyrics_data = non_null_lyrics_data.append(null_lyrics_data)


                    # update lyrics dataset
                    pre_length = latest_lyrics_data.shape[0]
                    latest_lyrics_data = latest_lyrics_data.append(curr_lyrics_data[latest_lyrics_data.columns])
                    post_length = latest_lyrics_data.shape[0]

                    assert pre_length <= post_length

                    latest_lyrics_data.to_csv(lyrics_filepath, index=False)
                except Exception:
                    print("failed")
