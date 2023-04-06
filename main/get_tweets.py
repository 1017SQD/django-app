import tweepy
import pandas as pd
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer
import re
import unicodedata
import numpy as np
import os
import requests
import base64

def get_tweets(api):
    """
    Retrieves tweets from the auth user using the specified Twitter API.

    Parameters
    ----------
    api: tweepy.API
        Twitter API object used to access the user's tweets.

    Returns
    -------
    list of tweepy.models.Status
        List of the user's tweets.
    """
    tweets = api.user_timeline(count=200,
                               exclude_replies=False,
                               include_rts=False,
                               # Necessary to keep the full text
                               # otherwise only the first 140 words are extracted
                               tweet_mode='extended'

                               )
    return tweets

def get_all_tweets(api):
    """
    Retrieves all tweets from the specified user using the specified Twitter API.

    Parameters
    ----------
    screen_name : str
        Screen name of the user whose tweets are to be retrieved.
    api: tweepy.API
        Twitter API object used to access the user's tweets.

    Returns
    -------
    list of tweepy.models.Status
        List of all the user's tweets.
    """
    tweets = get_tweets(api)
    all_tweets = []
    all_tweets.extend(tweets)
    oldest_id = tweets[-1].id
    while True:
        tweets = api.user_timeline(count=200,
                                   exclude_replies=False,
                                   include_rts=False,
                                   max_id=oldest_id - 1,
                                   # Necessary to keep the full text
                                   # otherwise only the first 140 words are extracted
                                   tweet_mode='extended'
                                   )
        if not len(tweets):
            break
        oldest_id = tweets[-1].id
        all_tweets.extend(tweets)

    return all_tweets

# Function for polarity score
def polarity_score(tweet):
    return TextBlob(tweet, pos_tagger=PatternTagger(), analyzer=PatternAnalyzer()).sentiment[0]

# Function to get sentiment type
def sentimenttextblob(tweet):
    polarity = polarity_score(tweet)
    if polarity < 0:
        return ("Negative", polarity)
    elif polarity == 0:
        return ("Neutral", polarity)
    else:
        return ("Positive", polarity)

def get_bearer_token(api_key, api_secret_key):
    # Créer l'en-tête d'autorisation en encodant la clé API et la clé secrète
    key_secret = '{}:{}'.format(api_key, api_secret_key).encode('ascii')
    b64_encoded_key = base64.b64encode(key_secret).decode('ascii')

    # Définir les paramètres pour la requête POST
    headers = {
        'Authorization': 'Basic {}'.format(b64_encoded_key),
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    data = {
        'grant_type': 'client_credentials',
    }

    # Envoyer la requête POST à l'API Twitter
    response = requests.post(
        'https://api.twitter.com/oauth2/token',
        headers=headers,
        data=data,
    )

    # Vérifier si la requête a réussi et renvoyer le jeton d'accès
    if response.status_code == 200:
        access_token = response.json()['access_token']
        return access_token
    else:
        raise Exception('Impossible d\'obtenir le jeton d\'accès. Code d\'erreur : {}'.format(response.status_code))

def get_tweets_info(tweet_ids, bearer_token):
    #bearer_token = os.environ.get("BEARER_TOKEN")
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "ids": tweet_ids,
        "tweet.fields": "public_metrics",
        "expansions": "attachments.media_keys",
        "media.fields": "public_metrics"
    }
    response = requests.get("https://api.twitter.com/2/tweets", headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def status(api):
    tweet_source = []
    year = []
    year_month = []
    week = []
    month = []
    hour = []
    tweets_txt = []
    nb_retweet = []
    nb_fav = []
    sentiment = []
    score = []
    media_type = []
    
    for status in get_all_tweets(api):
        tweet_source.append(status.source)
        year.append(int(status.created_at.strftime("%Y")))
        year_month.append(status.created_at.strftime("%Y-%m"))
        week.append(status.created_at.strftime('%A'))
        month.append(status.created_at.strftime('%B'))
        hour.append(status.created_at.strftime('%H'))
        tweets_txt.append(status.full_text)
        sent = sentimenttextblob(status.full_text)
        sentiment.append(sent[0])
        score.append(sent[1])
        nb_retweet.append(status.retweet_count)
        nb_fav.append(status.favorite_count)
        
        if 'extended_entities' in status._json:
            for media in status._json['extended_entities']['media']:
                media_type.append(media['type'])
        else:
            media_type.append('text')
      
    dict_metrics = {'tweet_source':tweet_source, 'year':year,
          'tweets_txt':tweets_txt, 'nb_retweet':nb_retweet,
          'nb_favorite':nb_fav, 'year_month':year_month,
          'week':week, 'month':month, 'hour':hour,
          'sentiment':sentiment, 'score':score,
          'media_type':media_type}
    
    df_metrics = pd.DataFrame(dict_metrics)
    return df_metrics

def cleaning_tweets(tweet):
    """
    Clean up a tweet by removing links, hashtags, mentions and emoticons.

    Parameters
    ----------
    tweet : str
        Tweet to clean up.

    Returns
    -------
    str
        Tweet cleaned up.
    """
    regex_pattern = re.compile(pattern="["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictograms
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    pattern = re.compile(r'(https?://)?(www\.)?(\w+\.)?(\w+)(\.\w+)(/.+)?')
    tweet = re.sub(regex_pattern, '', tweet)  # replaces the pattern with ''
    tweet = re.sub(pattern, '', tweet)
    tweet = re.sub(r'@[^\s]+', '', tweet)
    tweet = re.sub(r'#[^\s]+', '', tweet)
    tweet = re.sub(r'https?://[A-Za-z0-9./]+', '', tweet)
    # Removes user mentions
    tweet = re.sub(r'@[A-Za-z0-9]+', '', tweet)
    tweet = tweet.strip()
    return tweet

def remove_emojis(tweets):
    text = cleaning_tweets(tweets)
    # Create an empty list to store the cleaned text
    cleaned_text = []

    # Scroll through each character of the text
    for character in text:
        # Use the `category` function of the `unicodedata` library to get the Unicode category of the character
        character_category = unicodedata.category(character)
        # If the character's Unicode category is not "So" (Symbol, Other), add the character to the clean text list
        if character_category != "So":
            cleaned_text.append(character)

    # Join the characters in the cleaned text list into a string and return it
    return "".join(cleaned_text)

def process_tweets(tweets):
    """
    Processes tweets by removing empty words.

    Parameters
    ----------
    tweets : list of str
        List of tweets to process.

    Returns
    -------
    list of str
        List of processed tweets.
    """
    # Obtenir le chemin absolu du fichier french_stopwords.txt
    stopwords_path = os.path.join(os.path.dirname(__file__), 'french_stopwords.txt')
    with open(stopwords_path, "r", encoding="utf-8") as stopwords_file:
        stopwords = []
        for line in stopwords_file:
            word = line.split("|")[0].strip()
            stopwords.append(word)

    cleaned_tweets = []
    for tweet in tweets.lower().split():
        if (tweet not in stopwords) and (len(tweet) > 1):
            cleaned_tweets.append(remove_emojis(tweet))
                      
    return cleaned_tweets