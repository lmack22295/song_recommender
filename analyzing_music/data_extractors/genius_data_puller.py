from bs4 import BeautifulSoup
import ssl
import json
from urllib.request import Request, urlopen
from tqdm import tqdm
import pandas as pd
import re
from analyzing_music.data_extractors import spotipy_data_puller
from analyzing_music.data_extractors.lyrics_cleaner import clean_lyrics_data

GENIUS_API_KEY = '2qq1ZZDwqUbHXCm7p9QFyhK7ZNKgslA8EgWf7BUonfz5PKPSPHtJ0ISVj3nyeHat'


class GeniusDataPuller:

    def __init__(self, artist_list, song_list, uri_list):
        self.artists = artist_list
        self.songs = song_list
        self.uris = uri_list

    def build_song_lyrics_data(self):
        # For ignoring SSL certificate errors
        songs_dataset = pd.DataFrame()
        count = 0

        for i in tqdm(range(len(self.songs))):
            print("Artist: {}; Song: {}".format(self.artists[i], self.songs[i]))
            curr_artist, curr_song, curr_uri = self.artists[i], self.songs[i], self.uris[i]
            try:
                curr_lyrics = self.scrape_genius_for_song_lyrics(curr_artist,
                                                                 curr_song)
                count = count + 1
                songs_dataset = songs_dataset.append(pd.DataFrame({'artist_name': [curr_artist],
                                                                   'song_name': [curr_song],
                                                                   'uri': [curr_uri],
                                                                   'lyrics': [curr_lyrics]}))
                print("Successfully loaded song {}".format(self.songs[i]))
            except Exception:
                songs_dataset = songs_dataset.append(pd.DataFrame({'artist_name': [curr_artist],
                                                                   'song_name': [curr_song],
                                                                   'uri': [curr_uri],
                                                                   'lyrics': [None]}))
                print("Failed in Error")

        return songs_dataset

    def get_song_lyrics_from_genius_api(self, artist_name, song_title):
        api = genius.Genius(GENIUS_API_KEY, verbose=False)
        try:
            song = api.search_song(song_title, artist=artist_name)
            song_album = song.album
            song_album_url = song.album_url
            featured_artists = song.featured_artists
            song_lyrics = re.sub("\n", " ", song.lyrics)
            song_media = song.media
            song_url = song.url
            song_writer_artists = song.writer_artists
            song_year = song.year
        except:
            song_album = "null"
            song_album_url = "null"
            featured_artists = "null"
            song_lyrics = "null"
            song_media = "null"
            song_url = "null"
            song_writer_artists = "null"
            song_year = "null"
        return song_lyrics

    def scrape_genius_for_song_lyrics(self, artist, song):
        feature_idx = song.find(' (feat')
        song = song[:feature_idx] if feature_idx != -1 else song
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # Input from user
        url = self.get_genius_song_url(artist, song)

        # Making the website believe that you are accessing it using a mozilla browser
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webpage = urlopen(req).read()

        # Creating a BeautifulSoup object of the html page for easy extraction of data.

        soup = BeautifulSoup(webpage, 'html.parser')
        html = soup.prettify('utf-8')
        song_json = dict()
        song_json["Lyrics"] = [];
        song_json["Comments"] = [];

        # Extract Title of the song
        for title in soup.findAll('title'):
            song_json["Title"] = title.text.strip()

        # Extract the release date of the song
        for span in soup.findAll('span', attrs={'class': 'metadata_unit-info metadata_unit-info--text_only'}):
            song_json["Release date"] = span.text.strip()

        # Extract the Comments on the song
        for div in soup.findAll('div', attrs={'class': 'rich_text_formatting'}):
            comments = div.text.strip().split("\n")
            for comment in comments:
                if comment != "":
                    song_json["Comments"].append(comment);

        # Extract the Lyrics of the song
        for div in soup.findAll('div', attrs={'class': 'lyrics'}):
            song_json["Lyrics"].append(div.text.strip().split("\n"));

        song_json['artist_name'] = artist
        song_json['song_name'] = song
        # Save the json created with the file name as title + .json
        # with open("music_lyrics/" + song_json["Title"] + '.json', 'w+') as outfile:
        #     json.dump(song_json, outfile, indent=4, ensure_ascii=False)
        #
        # # Save the html content into an html file with name as title + .html
        # with open("music_lyrics/" + song_json["Title"] + '.html', 'wb') as file:
        #     file.write(html)

        return ' '.join(song_json['Lyrics'][0])


    def get_genius_song_url(self, artist_name, song_name):
        song_name = song_name.replace(',', '').replace('\'', '').replace('.', '').replace('(', '').replace(')',
                                                                                                           '').replace(
            '!', '').replace('&', '').replace('+', '').replace('?', '')
        base_url = "https://genius.com/"
        suffix = 'lyrics'
        artist_part = '-'.join(artist_name.split(' '))
        song_part = '-'.join(song_name.split(' '))
        return base_url + artist_part + '-' + song_part + '-' + suffix


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

if __name__ == '__main__':
    # update_lyrics_dataset()
    artist_list = \
        ['Alt-J', 'James Taylor', 'Jack Johnson', 'Flume', 'FKJ',
         'James Blake', 'Gunna', 'Noname', 'Oh Wonder',
         'Mac Demarco', 'Jhene Aiko', 'JMSN', 'Calvin Harris',
         'Travis Scott', 'Young Thug', 'John Mayer',
         'The Weeknd', 'The Roots', 'Childish Gambino']
    latest_lyrics_data = pd.read_csv("latest_lyrics_data.csv")

    # initialize spotify data puller to access audio data from spotify API
    spotify = spotipy_data_puller.SpotipyDataPuller(client_id='7085a21ce4124b3e89db61d750b133a7',
                                client_secret='2b02da51f99f4470a1c2ef91f28a0957')

    for artist in artist_list:
        try:
            master_artist_data = pd.read_csv("spotify_artist_data_{}.csv".format(artist))
        except:
            song_data, audio_data, _ = spotify.build_artist_song_dataset([artist])
            # Get Spotify song_metadata and audio features from Spotify API
            master_artist_data = song_data.merge(audio_data,
                                                 left_on='song_uri',
                                                 right_on='uri')
            master_artist_data.to_csv("spotify_artist_data_{}.csv".format(artist))

            master_audio_data = pd.read_csv("master_audio_data.csv")
            master_audio_data = master_audio_data.append(audio_data).drop_duplicates()
            master_audio_data.to_csv("master_audio_data.csv", index=False)

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

            # master_lyrics_data = master_lyrics_data.append(curr_lyrics_data)
            # clean, stem, lemmatize, and remove english stopwords
            curr_lyrics_data = clean_lyrics_data(curr_lyrics_data)
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
            latest_lyrics_data.drop_duplicates().to_csv("latest_lyrics_data2.csv", index=False)
