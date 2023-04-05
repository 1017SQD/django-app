from django.shortcuts import render, redirect
from django.views.generic import ListView
from main.utils import get_api
import plotly.express as px
from . import get_tweets
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from users.models import UserProfile, NotFollowingBack, Follower, Following, MutualFollower, UserTimeline
from django.core.paginator import Paginator
import plotly.graph_objects as go
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.db import transaction
import threading
from django.db.models import Q
import tweepy
from queue import Queue

def get_user_profile(request):
    api = get_api(request)
    verify_credentials = api.verify_credentials()
    user_twitter_id = verify_credentials.id
    name = verify_credentials.name
    screen_name = verify_credentials.screen_name
    location = verify_credentials.location
    description = verify_credentials.description
    protected = verify_credentials.protected
    followers_count = verify_credentials.followers_count
    friends_count = verify_credentials.friends_count
    listed_count = verify_credentials.listed_count
    created_at = verify_credentials.created_at
    favourites_count = verify_credentials.favourites_count
    verified = verify_credentials.verified
    statuses_count = verify_credentials.statuses_count
    lang = verify_credentials.lang
    profile_image_url = verify_credentials.profile_image_url.replace("_normal", "")
    profile_banner_url = api.get_profile_banner(screen_name=screen_name)['sizes']['600x200']['url']
    
    # create or get user profile
    profile, created = UserProfile.objects.update_or_create(
        user=request.user,
        defaults={
            'user_twitter_id': user_twitter_id,
            'name': name,
            'screen_name': screen_name,
            'location' : location,
            'description': description,
            'protected' : protected,
            'followers_count': followers_count,
            'friends_count': friends_count,
            'listed_count' : listed_count,
            'created_at' : created_at,
            'favourites_count' : favourites_count,
            'verified' : verified,
            'statuses_count': statuses_count,
            'lang' : lang,
            'profile_image_url': profile_image_url,
            'profile_banner_url': profile_banner_url,
        }
    )
    if created:
        profile.save()

    # Récupérer les informations des utilisateurs à partir de la base de données
    user_profile_description = list(UserProfile.objects.filter(user=request.user).values())
    return user_profile_description

def get_user_timeline(request):
    api = get_api(request)
    statuses = get_tweets.get_all_tweets(api)
    
    for status in statuses:
        tweet = get_tweets.cleaning_tweets(status.full_text)
        sent = get_tweets.sentimenttextblob(tweet)
        sentiment = sent[0]
        polarity = sent[1]
        is_quote_status = status.is_quote_status
        quoted_status = ''
        
        if is_quote_status:
            quoted_status=status.quoted_status.text
            
        # update or get user timeline
        timeline, created = UserTimeline.objects.update_or_create(
            user=request.user.userprofile,
            tweet_id=status.id,
            defaults={
                'user': request.user.userprofile,
                'tweet_id': status.id,
                'tweet': tweet,
                'sentiment': sentiment,
                'polarity': polarity,
                'source': status.source,
                'in_reply_to_screen_name': status.in_reply_to_screen_name,
                'is_quote_status': is_quote_status,
                'quoted_status': quoted_status,
                'retweet_count': status.retweet_count,
                'favorite_count': status.favorite_count,
                'lang': status.lang
            }
        )
        if created:
            timeline.save()
    
    # Récupère les informations sur les tweets des utilisateurs à partir de la base de données
    user_timeline_info = list(UserTimeline.objects.filter(user=request.user.userprofile).values())
    return user_timeline_info

def add_users_chunk(request_user, api, chunk, model, result_queue):
    users_to_add_data = []
    try:
        users = []
        for user_id in chunk:
            user = api.get_user(user_id=user_id)
            users.append(user)
    except tweepy.errors as e:
        print("Error occurred while fetching user")
        
    for twitter_user in users:
        user_to_add = model(
            user=request_user,
            user_twitter_id=twitter_user.id,
            name=twitter_user.name,
            screen_name=twitter_user.screen_name,
            profile_image_url=twitter_user.profile_image_url.replace("_normal", ""),
            description=twitter_user.description,
            location=twitter_user.location
        )
        users_to_add_data.append(user_to_add)
    result_queue.put(users_to_add_data)

def update_table(request, api, tweepy_user_ids, model):
    tweepy_user_ids # following_ids = api.get_friend_ids()

    # Récupération des utilisateurs existants
    existing_users = model.objects.filter(user=request.user.userprofile)
    existing_user_ids = set(existing_users.values_list('user_twitter_id', flat=True))

    # Suppression d'utilisateurs
    user_ids_to_delete = existing_user_ids - tweepy_user_ids
    model.objects.filter(user=request.user.userprofile, user_twitter_id__in=user_ids_to_delete).delete()

    # Ajout d'utilisateurs
    user_ids_to_add = set(tweepy_user_ids) - existing_user_ids
    chunk_size = 100 # Taille des sous-listes
    user_ids_chunks = [list(user_ids_to_add)[i:i+chunk_size] for i in range(0, len(user_ids_to_add), chunk_size)]
    users_to_add_data = []

    result_queue = Queue()            
    threads = []
    for chunk in user_ids_chunks:
        thread = threading.Thread(target=add_users_chunk, args=(request.user.userprofile, api, chunk, model, result_queue))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
        print(f"Thread {thread} finished")
        
    while not result_queue.empty():
        users_to_add_data += result_queue.get()
    
    model.objects.bulk_create(users_to_add_data)
    
    # Récupération des informations des utilisateurs à partir de la base de données
    users_info = list(existing_users.filter(Q(user_twitter_id__in=tweepy_user_ids) | Q(user_twitter_id__in=user_ids_to_add)).values())
    return users_info

@transaction.atomic
def get_non_followers(request):
    try:
        api = get_api(request)
        # Récupération de la liste des abonnements de l'utilisateur
        friend_ids = api.get_friend_ids()
        # Récupération de la liste des abonnés de l'utilisateur
        follower_ids = api.get_follower_ids()
        # Vérification des abonnements qui ne suivent pas en retour
        not_following_back_ids = set(friend_ids) - set(follower_ids)
        non_followers = update_table(request, api, not_following_back_ids, NotFollowingBack)
    except:
        pass
    
    return non_followers

@transaction.atomic
def get_mutual_followers(request):
    try:
        api = get_api(request)    
        # Récupération de la liste des abonnements de l'utilisateur
        friends = api.get_friend_ids()
        # Récupération de la liste des abonnés de l'utilisateur
        followers = api.get_follower_ids()
        # Intersection entre les abonnements et abonnés
        followers_set = set(followers)
        friends_set = set(friends)
        mutual_ids = followers_set.intersection(friends_set)
        mutuals_info = update_table(request, api, mutual_ids, MutualFollower)
    except:
        pass
    
    return mutuals_info

@transaction.atomic
def get_followers(request):
    try:
        api = get_api(request)
        follower_user_ids = api.get_follower_ids()
        follower_ids = set(follower_user_ids)
        followers_info = update_table(request, api, follower_ids, Follower)
    except:
        pass
    
    return followers_info

@transaction.atomic
def get_following(request):
    try:
        api = get_api(request)
        following_user_ids = api.get_friend_ids()
        following_ids = set(following_user_ids)
        following_info = update_table(request, api, following_ids, Following)
    except:
        pass
    
    return following_info


@login_required
def user_timeline(request):
    user_timeline_info = list(UserTimeline.objects.filter(user=request.user.userprofile).values())
    print(pd.DataFrame(user_timeline_info))
    # api_key, api_secret_key = user_credentials(request)
    # api = get_api(request)
    # print(api_key, api_secret_key)
    #bearer_token = get_tweets.get_bearer_token(api_key, api_secret_key)
    #tweets = api.user_timeline(count=1, include_rts=False, exclude_replies=False, screen_name="1O17SQD")
    #tweet_ids = []
    #for s in tweets:
     #   tweet_ids.append(s.id)
    #for id in tweet_ids:
     #   print(get_tweets.get_tweets_info(id, bearer_token))
    context = {
        'res' : user_timeline_info
    }
    return render(request, 'main/tweets.html', context)

def metrics(request):
    api = get_api(request)
    df_metrics = get_tweets.status(api)
    df_fig1 = df_metrics.groupby(['tweet_source', 'year'])['tweet_source'].count().reset_index(name='nb_source')
    df_fig2 = df_metrics.groupby(['year_month', 'year'])['nb_retweet'].sum().reset_index(name='nb_rt')
    df_fig3 = df_metrics.groupby(['year_month', 'year'])['nb_favorite'].sum().reset_index(name='nb_fav')
    df_fig4 = df_metrics.groupby(['sentiment', 'year'])['sentiment'].count().reset_index(name='nb_sent')
    df_fig5 = df_metrics.groupby(['year_month', 'year'])['tweets_txt'].count().reset_index(name='nb_tweet')
    df_fig6 = df_metrics.groupby(['month'])['tweets_txt'].count().reset_index(name='nb_tweet')
    df_fig7 = df_metrics.groupby(['week'])['tweets_txt'].count().reset_index(name='nb_tweet')
    df_score = df_metrics.groupby(['year_month', 'year'])['score'].mean().reset_index(name='avg_score_sent')
    return df_fig1, df_fig2, df_fig3, df_fig4, df_fig5, df_fig6, df_fig7, df_score, df_metrics

@login_required
def home(request):
    df_fig1, df_fig2, df_fig3, df_fig4, df_fig5, df_fig6, df_fig7, df_score, df_metrics = metrics(request)
    
    fig1 = px.pie(data_frame=df_fig1, names="tweet_source",
                  values="nb_source", hole=.5,
                  color_discrete_sequence=px.colors.sequential.RdBu)

    fig1.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        title_text="Sentiment Analysis",
                        annotations=[dict(text='GHG', x=0.5, y=0.5, font_size=20, showarrow=False)])
    fig1.update_traces(textinfo='label+percent', hoverinfo="label+percent+name")
    
    chart = fig1.to_html(config={'displayModeBar': False})
        
    fig4 = px.pie(data_frame=df_fig4, names='sentiment',
                    values='nb_sent',hole=.5,
                    color_discrete_sequence=px.colors.sequential.RdBu)
    fig4.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        title_text="Sentiment Analysis",
                        annotations=[dict(text='GHG', x=0.5, y=0.5, font_size=20, showarrow=False)])
    fig4.update_traces(textinfo='label+percent', hoverinfo="label+percent+name")
    
    chart4 = fig4.to_html(config={'displayModeBar': False})
    
    fig5 = make_subplots(rows=2, cols=2, start_cell="bottom-left")

    fig5.add_trace(go.Scatter(x=df_fig5['year_month'], y=df_fig5['nb_tweet']),
                row=1, col=1)

    fig5.add_trace(go.Scatter(x=df_fig2['year_month'], y=df_fig2['nb_rt']),
                row=1, col=2)

    fig5.add_trace(go.Scatter(x=df_fig3['year_month'], y=df_fig3['nb_fav']),
                row=2, col=1)

    fig5.add_trace(go.Scatter(x=df_score['year_month'], y=df_score['avg_score_sent']),
                row=2, col=2)
    
    fig5.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        title_text="Tweets by Year")

    chart5 = fig5.to_html(config={'displayModeBar': False})
    
    #px.set_mapbox_access_token(open(".mapbox_token").read())
    fig6 = go.Figure(go.Scattergeo())
    fig6.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    chart6 = fig6.to_html(config={'displayModeBar': False})
    
    fig7 = px.line(data_frame=df_fig4, x="year", y="nb_sent", color='sentiment')
    fig7.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        xaxis_title=None,
                        yaxis_title=None,
                        title='Sentiment by Year',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    chart7 = fig7.to_html(config={'displayModeBar': False})

    fig8 = go.Figure(go.Indicator(
        domain = {'x': [0, 1], 'y': [0, 1]},
        value = round(df_metrics['score'].mean(), 3),
        mode = "gauge+number",
        title = {'text': "Score"},
        gauge = {'axis': {'range': [-1, 1]},
                'bar': {'color': "#2a3f5f"}
            }))
    
    fig8.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    chart8 = fig8.to_html(config={'displayModeBar': False})
    
    fig2 = go.Figure(go.Indicator(
        mode = "number+delta",
        value = 400,
        number = {'prefix': "$"},
        delta = {'reference': 320, 'relative': True},
        domain = {'x': [0, 1], 'y': [0, 1]}))

    fig2.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    chart2 = fig2.to_html(config={'displayModeBar': False})
    
    fig3 = go.Figure(go.Indicator(
        mode = "number+delta",
        value = 350,
        number = {'prefix': "$"},
        delta = {'reference': 400, 'relative': True},
        domain = {'x': [0, 1], 'y': [0, 1]}))
    
    fig3.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    chart3 = fig3.to_html(config={'displayModeBar': False})
    
    fig9 = px.bar(data_frame=df_fig6, x='month', y='nb_tweet', color='month',
                    category_orders=dict(month=["January", "February",
                                            "March", "April", "May",
                                            "June", "July", "August",
                                            "September", "October", "November",
                                            "December"]))
    
    fig9.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        xaxis_title=None,
                        yaxis_title=None,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    chart9 = fig9.to_html(config={'displayModeBar': False})
    
    fig10 = px.bar(data_frame=df_fig7, x='week', y='nb_tweet',
                    category_orders=dict(week=["Monday", "Tuesday",
                                            "Wednesday", "Thursday", "Friday",
                                            "Saturday", "Sunday"]))
    
    fig10.update_layout(margin=dict(l=20, r=20, t=30, b=20),
                        xaxis_title=None,
                        yaxis_title=None,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)')
    
    fig10.update_traces(marker_color='red',)
    
    chart10 = fig10.to_html(config={'displayModeBar': False})
    
    user_profile_twitter = get_user_profile(request)
            
    context = {'chart' : chart, 'chart2': chart2,
                'chart3': chart3, 'chart4': chart4,
                'chart5': chart5, 'chart6': chart6,
                'chart7': chart7, 'chart8': chart8,
                'chart9': chart9, 'chart10': chart10,
                'user_profile_twitter' : user_profile_twitter
                }
    
    return render(request, 'main/home.html', context)

@login_required
def non_followers(request):
    # Set up Pagination
    p = Paginator(get_non_followers(request), 8)
    page = request.GET.get('page')
    not_following_back_info = p.get_page(page)
    nums = "a" * not_following_back_info.paginator.num_pages
    
    user_profile_twitter = get_user_profile(request)
    
    context = {
        'not_following_back_info' : not_following_back_info,
        'user_profile_twitter' : user_profile_twitter,
        'nums' : nums
    }
    return render(request, 'main/non_followers.html', context)
    
def unfollow(request, user_id):
    api = get_api(request)
    api.destroy_friendship(user_id=user_id)
    return redirect('unfollowers')
    
@login_required    
def followers(request):
    # Set up Pagination
    p = Paginator(get_followers(request), 8)
    page = request.GET.get('page')
    followers = p.get_page(page)
    nums = "a" * followers.paginator.num_pages
    
    user_profile_twitter = get_user_profile(request)
    
    context = {
        'followers' : followers,
        'user_profile_twitter' : user_profile_twitter,
        'nums':nums
    }
    
    return render(request, 'main/followers.html', context)

@login_required
def following(request):
    # Set up Pagination
    p = Paginator(get_following(request), 8)
    page = request.GET.get('page')
    following = p.get_page(page)
    nums = "a" * following.paginator.num_pages
    
    user_profile_twitter = get_user_profile(request)
    
    context = {
        'myfollowing' : following,
        'user_profile_twitter' : user_profile_twitter,
        'nums' : nums
    }
    return render(request, 'main/following.html', context)

@login_required     
def mutual_followers(request):
    # Set up Pagination
    p = Paginator(get_mutual_followers(request), 8)
    page = request.GET.get('page')
    mutual_followers = p.get_page(page)
    nums = "a" * mutual_followers.paginator.num_pages
    
    user_profile_twitter = get_user_profile(request)
    
    context = {
        'mutual_followers' : mutual_followers,
        'user_profile_twitter' : user_profile_twitter,
        'nums' : nums
    }
    return render(request, 'main/mutual_followers.html', context)

@login_required    
def tweets(request):
    return render(request, 'main/tweets.html')

