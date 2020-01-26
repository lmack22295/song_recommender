import urllib.request
import urllib.parse
import urllib.error
from bs4 import BeautifulSoup
import ssl
import json
import ast
import os
from urllib.request import Request, urlopen
from tqdm import tqdm
import pandas as pd
import numpy as np
from spotipy_data_puller import SpotipyDataPuller

class GeniusDataPuller:

    def __init__(self, artist_list, song_list):
        self.artists = artist_list
        self.songs = song_list

    def build_song_lyrics_data(self, lyrics_data):
        # For ignoring SSL certificate errors
        songs_dataset = pd.DataFrame()
        count = 0
        for i in tqdm(range(len(self.songs))):
            print("Artist: {}; Song: {}".format(self.artists[i], self.songs[i]))
            curr_artist, curr_song = self.artists[i], self.songs[i]
            if len(lyrics_data.loc[(lyrics_data.artist_name == curr_artist) &
                               (lyrics_data.song_name == curr_song)]) == 0:
                try:
                    curr_lyrics = self.get_song_lyrics_from_genius(curr_artist,
                                                              curr_song)
                    count = count + 1
                    songs_dataset = songs_dataset.append(pd.DataFrame({'artist': [curr_artist],
                                                                       'song': [curr_song],
                                                                       'lyrics': [curr_lyrics]}))
                    print("Successfully loaded song {}".format(self.songs[i]))
                except Exception:
                    print("Failed in Error")
            else:
                print("Already have lyrics for {} by {}".format(curr_song, curr_artist))

        return songs_dataset


    def get_song_lyrics_from_genius(self, artist, song):
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
        with open("music_lyrics/" + song_json["Title"] + '.json', 'w+') as outfile:
            json.dump(song_json, outfile, indent=4, ensure_ascii=False)

        # Save the html content into an html file with name as title + .html
        with open("music_lyrics/" + song_json["Title"] + '.html', 'wb') as file:
            file.write(html)

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


if __name__ == '__main__':
    artist_list = ['MGMT']
    master_lyrics_data = pd.read_csv("master_lyrics_data.csv")

    # initialize spotify data puller to access audio data from spotify API
    spotify = SpotipyDataPuller(client_id=,
                                client_secret=)

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

        genius = GeniusDataPuller(master_artist_data.artist_name.values, master_artist_data.song_name.values)
        song_dataset = genius.build_song_lyrics_data(master_lyrics_data)

        if not song_dataset.empty:
            curr_lyrics_data = song_dataset.merge(master_artist_data,
                                           left_on=['artist', 'song'],
                                           right_on=['artist_name', 'song_name'])
            curr_lyrics_data.to_csv("spotify_artist_lyrics_data_{}.csv".format(artist))

            master_lyrics_data = master_lyrics_data.append(curr_lyrics_data)
            master_lyrics_data = master_lyrics_data[['accousticness', 'album',
                                                     'artist_name', 'danceability', 'energy',
                                                     'id', 'instrumentalness',
                                                     'liveness', 'loudness', 'lyrics',
                                                     'popularity',
                                                     'song_name', 'song_uri', 'speechiness',
                                                     'tempo', 'track_number',
                                                     'uri', 'valence']]
            master_lyrics_data.drop_duplicates().to_csv("master_lyrics_data.csv", index=False)
