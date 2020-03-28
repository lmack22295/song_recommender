from analyzing_music.data_extractors.spotipy_data_puller import SpotipyDataPuller
from analyzing_music.data_extractors.genius_data_puller import GeniusDataPuller
from analyzing_music.data_extractors import lyrics_cleaner


if __name__ == '__main__':

    lyrics_read_filepath = "./data/latest_lyrics_data.csv"
    lyrics_write_filepath = "./data/latest_lyrics_data2.csv"
    artist_filename = "spotify_artist_data_{}.csv"
    audio_filepath = "master_audio_data.csv"

    spotify_client_id = '7085a21ce4124b3e89db61d750b133a7'
    spotify_client_secret = '2b02da51f99f4470a1c2ef91f28a0957'
    # update_lyrics_dataset()
    artist_list = \
        ['Clairo','Alt-J', 'James Taylor', 'Jack Johnson', 'Flume', 'FKJ',
         'James Blake', 'Gunna', 'Noname', 'Oh Wonder',
         'Mac Demarco', 'Jhene Aiko', 'JMSN', 'Calvin Harris',
         'Travis Scott', 'Young Thug', 'John Mayer',
         'The Weeknd', 'The Roots', 'Childish Gambino']
    latest_lyrics_data = pd.read_csv(lyrics_read_filepath)

    # initialize spotify data puller to access audio data from spotify API
    spotify = SpotipyDataPuller(client_id=spotify_client_id,
                                client_secret=spotify_client_secret)

    for artist in artist_list:
        try:
            master_artist_data = pd.read_csv(artist_filename.format(artist))
        except:
            song_data, audio_data, _ = spotify.build_artist_song_dataset([artist])
            # Get Spotify song_metadata and audio features from Spotify API
            master_artist_data = song_data.merge(audio_data,
                                                 left_on='song_uri',
                                                 right_on='uri')
            master_artist_data.to_csv(artist_filename.format(artist))

            master_audio_data = pd.read_csv(audio_filepath)
            master_audio_data = master_audio_data.append(audio_data).drop_duplicates()
            master_audio_data.to_csv(audio_filepath, index=False)

        genius = GeniusDataPuller(master_artist_data.artist_name.values,
                                  master_artist_data.song_name.values,
                                  master_artist_data.song_uri.values)
        song_dataset = genius.build_song_lyrics_data(latest_lyrics_data)

        if not song_dataset.empty:
            print(song_dataset.columns)
            curr_lyrics_data = song_dataset.merge(master_artist_data,
                                                  left_on=['artist_name', 'song_name'],
                                                  right_on=['artist_name', 'song_name'])
            curr_lyrics_data.to_csv("spotify_artist_lyrics_data_{}.csv".format(artist))

            # clean, stem, lemmatize, and remove english stopwords
            curr_lyrics_data = lyrics_cleaner.clean_lyrics_data(curr_lyrics_data)
            latest_lyrics_data = latest_lyrics_data.append(curr_lyrics_data)

            # master_lyrics_data = master_lyrics_data[['accousticness', 'album',
            #                                          'artist_name', 'danceability', 'energy',
            #                                          'id', 'instrumentalness',
            #                                          'liveness', 'loudness', 'lyrics',
            #                                          'popularity',
            #                                          'song_name', 'song_uri', 'speechiness',
            #                                          'tempo', 'track_number',
            #                                          'uri', 'valence']]
            # master_lyrics_data.drop_duplicates().to_csv("master_lyrics_data.csv", index=False)
            latest_lyrics_data.drop_duplicates().to_csv(save_filepath, index=False)
