import os
import slack
import spotipy
import pandas
from spotipy.oauth2 import SpotifyClientCredentials
from get_creds import *
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter


#Creates spotify object
def get_spotify():
    spotify_client_id = get_creds('spotify_client_id')
    spotify_client_secret = get_creds('spotify_client_secret')
    client_credentials_manager = SpotifyClientCredentials(client_id=spotify_client_id,client_secret=spotify_client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp

#Gets spotify artist from search string
def get_artist(sp, artist_name):
    results = sp.search(q='artist:{}'.format(artist_name), type='artist')
    items = results['artists']['items']
    if len(items) > 0:
        return items[0]
    else:
        return None

#Gets recommendations for artist
def get_artist_recs(sp, artist):
    results = sp.recommendations(seed_artists=[artist['id']])
    return results['tracks']

#Gets recommendations for related artists
def get_related_artist_recs(sp,artist_name):
    artist = get_artist(sp,artist_name)
    artist_rslt_name = artist['items'][0]['name']
    artist_rslt_uri = artist['items'][0]['uri']
    related = sp.artist_related_artists(uri)
    return related

#Gets top tracks for artist
def get_artist_top_tracks(sp,artist_name):
    artist = get_artist(sp,artist_name)
    artist_uri = artist['items'][0]['uri']
    topresults = sp.artist_top_tracks(artist_uri)
    return topresults

#Finds your playlist based on search string
def get_my_playlist(sp,playlist_name):
    playlists = sp.current_user_playlists()
    for playlist in playlists:
        if playlist_name.lower() in playlist['name'].lower():
            return playlist

#Gets available genre list
def get_genre_list(sp):
    return sp.recommendation_genre_seeds()

#Gets recommendations based on genre search
def get_genre_recs(sp,genre):
    results = sp.recommendations(seed_genres=[genre])
    return results['tracks']


#Finds your top artists (short_term, medium_term, long_term)
def get_my_top_artists(sp):
    #ranges = ['short_term','medium_term','long_term']
    short_term_results = sp.current_user_top_artists(time_range='short_term', limit=10)
    medium_term_results = sp.current_user_top_artists(time_range='medium_term', limit=10)
    long_term_results = sp.current_user_top_artists(time_range='long_term', limit=10)
    return short_term_results, medium_term_results, long_term_results

#Finds your top tracks (short_term, medium_term, long_term)
def get_my_top_tracks(sp):
    short_term_results = sp.current_user_top_tracks(time_range='short_term', limit=10)
    medium_term_results = sp.current_user_top_tracks(time_range='medium_term', limit=10)
    long_term_results = sp.current_user_top_tracks(time_range='long_term', limit=10)
    return short_term_results, medium_term_results, long_term_results

#Creates slack object
def get_slack(slack_bot_token):
    slk = slack.WebClient(token=slack_bot_token)
    return slk

#List slack channels
def list_slack_channels(slk):
    channels_call = slk.api_call('channels.list')
    if channels_call.get('ok'):
        return channels_call['channels']
    return None

#Sends slack message
def send_slack_message(slk, message_text, channel):
    #channel_name = 'personal-api'
    slk.chat_postMessage(
        channel = channel,
        text = message_text#,
        #username = 'pythonbot',
        #icon_emoji = ':robot_face'
        )

#Function for creating text based on user command
def get_message_text(command):
    if command == 'menu':
        return """Please choose one of the below options:
        1) Get song recommendations for an artist
        2) Get song recommendations for similar artists
        3) Get top songs for an artist
        4) Get song recommendations for a genre
        5) Get my top 10 artists
        6) Get my top 10 songs"""

#Some lists and items used for handling
processed_requests = []

#Function to process
def process_request(message, slk):
    if len(processed_requests) > 0:
        prev_request = processed_requests[len(processed_requests)-1]
    if 'yo!' in message.get('text'):
        #print('Sending menu')
        send_slack_message(slk, get_message_text('menu'), message['channel'])
        processed_requests.append(message.get('text'))
        return

#Initializing web app
app = Flask(__name__)
slack_signing_secret = get_creds('slack_signing_secret')
slack_events_adapter = SlackEventAdapter(slack_signing_secret, "/slack/events")
slack_bot_token = get_creds('slack_bot_oauth_token')
slack_client = get_slack(slack_bot_token)

#Receiving a message
@slack_events_adapter.on('message')
def handle_message(event_data):
    message = event_data['event']
    #print(message)
    if message.get('subtype') is None:
        process_request(message, slack_client)

#Error handling
@slack_events_adapter.on('error')
def error_handler(err):
    print('ERROR: {}'.format(str(err)))

slack_events_adapter.start(port=3000)#,debug=True)
