import argparse
from asyncio import base_futures
import json
import requests
import urllib

def call_lyrics_api(artist, title):
    artist_encoded = urllib.parse.quote(artist)
    title_encoded = urllib.parse.quote(title)
    url = "https://api.lyrics.ovh/v1/{}/{}".format(artist_encoded, title_encoded)
    
    try:
        print('Making API call to', url)
        response = requests.get(url=url)

    except:
        print("Something went wrong with the request")
    else:
        return response.json()

def call_genius_api(path, params=None):
    base_url = "https://api.genius.com"
    url = base_url + path
    client_access_token = "GxnxVPwhrcqp-D62SmF2kad0WVt-uL-w8hZLOmwpWuhU_zp5LH1ERZ0lY7ds-GNf"

    headers = {
        "user-agent": '',
        "Authorization": "Bearer {}".format(client_access_token)
        }

    try:
        print('Making API call to', url)
        response = requests.get(url=url, headers=headers, params=params)

    except:
        print("Something went wrong with the request")
    else:
        

        return response.json()


def get_artist_ID(name):
    """
    We don't know the artist's ID, so we need to perform a search.
    To do that, we need to find a page on the genuis website for one of the artist's songs and then pull the artist's ID from that page's data
    """
    path =  "/search?q=" + urllib.parse.quote(name)

    data = call_genius_api(path)
    
    artist_song = data["response"]["hits"][0]

    if artist_song:
        artist_id = artist_song["result"]["primary_artist"]["id"]
        print("Found the Genius ID for the artist:", artist_id)
        return artist_id
    else:
        print('No data found for the artist')
        return
        

def get_artist_songs(artist_id):
    """
    Accepts an artist's ID and uses it to retrieve the artist's recordings.

    Genius API returns paginated results. You have to retrieve the songs page by page.

    The songs of the artist will be returned as an array of song IDs.

    """

    current_page = 1
    per_page = 100
  
    next_page = True

    songs = [] 

    while next_page:
        path = "/artists/{}/songs/".format(artist_id)

        params = {
        "page": current_page,
        "per-page": per_page
        }

        data = call_genius_api(path=path, params=params) # get json of songs

        page_songs = data['response']['songs']

        if page_songs:
           
            songs += page_songs
        
            current_page += 1
            print("Page {} finished scraping".format(current_page))
            
            # Uncomment this to test the code. The service will retrive the first 2 pages of song data only rather than all the pages of the artist's songs
            #if current_page == 2:
               # break

        else:
            # If page_songs is empty, quit
            next_page = False

    return songs

def parse_lyrics_and_count_words(lyrics):
    word_count = 0
    song_count = 0
    for line in lyrics:
        song_count +=1

        line_edit = line
       
        # Removing \n and \t charaters from the start and end
        line_edit = line_edit.strip('\n')
        line_edit = line_edit.strip('\t')

        # Remove \n and \t characters form the middle
        line_edit = line_edit.replace('\n',' ')
        line_edit = line_edit.replace('\t',' ')

        # Split the string into individual words and count them
        words = line_edit.split()
        word_count += len(words)

    if(song_count > 0):
        return round(word_count/song_count, 2)
    return 0
        


def get_lyrics(songs, artist_id):
    """
    Given the IDs for an artist's songs, retrieve their lyrics and count the number of words

    Assumption: We are only interested in songs where the artist was the primary artist. Songs where the artist just featured but was not the main artist will be excluded

    The URL for the lyrics of a given song are found on the "url" and "path" properties of the song.
    But accessing it directly via API returns an error: {'meta': {'status': 403, 'message': 'Action forbidden for current scope'}}

    You therefore need to use an alternative means to get the lyrics. I chose to use the lyrics.ovh API for this part. 
    It fits the application well, because it only returns lyrics for the primary artist only. 

    eg Umbrella is a song by Rihanna & Jay Z. The API will only return lyrics when you specify only Rihanna as the artist

    Note: we will only count the songs for which we could obtain lyrics

    """
    lyrics = []
    for song in songs:
        if song["primary_artist"]["id"] == artist_id:
            artist = song["artist_names"]
            title = song["title"]

            data = call_lyrics_api(artist, title)
          
            if 'lyrics' in data:
                text = data["lyrics"]
                lyrics.append(text)
            else:
                print('Did not find lyrics for the song')
    return lyrics



def calculate_average_words(name):
    print('Retrieving ID of the artist')
    artist_id = get_artist_ID(name)

    print('Retrieving songs for', name,'with ID', artist_id)
    songs = get_artist_songs(artist_id)

    print('Retrieving lyrics')
    lyrics = get_lyrics(songs, artist_id)

    print('Parsing lyrics')
    result = parse_lyrics_and_count_words(lyrics)

    output = 'We found {} songs for {}. The average/mean number of words in those songs was found to be {}'.format(len(lyrics), name, result )
    print(output)

def main():
    # Step 1: create an ArgumentParser object
    # The ArgumentParser object will hold all the information necessary to parse the command line into Python data types
    parser = argparse.ArgumentParser(description='A command line tool for interacting with APIs')

    # Step 2: Add arguments by making calls to the add_argument() method. 
    # This will tell the ArgumentParser how to expect an input string on the command line and assign it to the property called 'average'
    parser.add_argument('-a','--average', dest='average', help='name of artist for whom we want to find the average number of words in their songs')

    # Step 3: Parse arguments. 
    args = parser.parse_args()
    if args.average:
        name = args.average
        calculate_average_words(name)

    else:
        print('Use the -h or --help flags for help')


if __name__ == '__main__':
    main()