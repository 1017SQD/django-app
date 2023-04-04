from decouple import config
import tweepy

def get_api(request):
	#Application key
	TWITTER_CONSUMER_KEY = config("TWITTER_API_KEY")
	TWITTER_CONSUMER_SECRET = config("TWITTER_API_SECRET_KEY")
	# set up and return a twitter api object
	oauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
	access_key = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token']
	access_secret = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token_secret']
	oauth.set_access_token(access_key, access_secret)
	api = tweepy.API(oauth)
	return api

def user_credentials(request):
    access_key = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token']
    access_secret = request.session['oauth_%s_access_token' % 'api.twitter.com']['oauth_token_secret']
    return access_key, access_secret
 