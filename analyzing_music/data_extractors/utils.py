import pandas as pd
from analyzing_music.data_extractors.genius_data_puller import GeniusDataPuller


def update_lyrics_dataset():
    lyrics_data = pd.read_csv("master_lyrics_data.csv")
    song_data = pd.read_csv("master_spotify_song_metadata.csv")
    audio_data = pd.read_csv("master_audio_data.csv")
    song_data = song_data.merge(audio_data, how='left', left_on='song_uri', right_on='uri')

    audio_data = lyrics_data.merge(audio_data, on='uri', how='right')

    new_uris = list(audio_data.loc[pd.isnull(audio_data.artist_name)].uri.values)
    print(len(new_uris))
    song_data = song_data[song_data.song_uri.isin(new_uris)].sort_values('artist_name')

    for i in range(int(len(song_data) / 1000)):
        start_idx, end_idx = i * 1000, i * 1000 + 1000
        genius = GeniusDataPuller(song_data.artist_name.values[start_idx:end_idx],
                                  song_data.song_name.values[start_idx:end_idx],
                                  song_data.uri.values[start_idx:end_idx])
        song_dataset = genius.build_song_lyrics_data(lyrics_data)
        lyrics_data = lyrics_data.append(song_dataset)

        lyrics_data.to_csv("master_lyrics_data.csv", index=False)
        print("Stored lyrics_data for song_uris indexed from {} to {}".format(start_idx, end_idx))