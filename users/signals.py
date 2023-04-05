from django.db.models.signals import post_save
from django.dispatch import receiver
import tweepy
from users.models import UserProfile, NotFollowingBack, Follower, Following, MutualFollower, UserTimeline

@receiver(post_save, sender=NotFollowingBack)
def update_not_following_back(sender, instance, **kwargs):
    # Récupération de l'API
    api = tweepy.API(instance.user.twitter_api.auth)

    # Récupération des informations de l'utilisateur sur Twitter
    user = api.get_user(user_id=instance.user_twitter_id)

    # Mise à jour des informations dans la base de données
    instance.name = user.name
    instance.screen_name = user.screen_name
    instance.profile_image_url = user.profile_image_url.replace("_normal", "")
    instance.description = user.description
    instance.location = user.location
    instance.save()

# Connectez la fonction update_not_following_back au signal post_save
# post_save.connect(update_not_following_back, sender=NotFollowingBack)

@receiver(post_save, sender=Follower)
def update_follower(sender, instance, **kwargs):
    # Récupération de l'API
    api = tweepy.API(instance.user.twitter_api.auth)

    # Récupération des informations de l'utilisateur sur Twitter
    user = api.get_user(user_id=instance.user_twitter_id)

    # Mise à jour des informations dans la base de données
    instance.name = user.name
    instance.screen_name = user.screen_name
    instance.profile_image_url = user.profile_image_url.replace("_normal", "")
    instance.description = user.description
    instance.location = user.location
    instance.save()

@receiver(post_save, sender=Following)
def update_following(sender, instance, **kwargs):
    # Récupération de l'API
    api = tweepy.API(instance.user.twitter_api.auth)

    # Récupération des informations de l'utilisateur sur Twitter
    user = api.get_user(user_id=instance.user_twitter_id)

    # Mise à jour des informations dans la base de données
    instance.name = user.name
    instance.screen_name = user.screen_name
    instance.profile_image_url = user.profile_image_url.replace("_normal", "")
    instance.description = user.description
    instance.location = user.location
    instance.save()
    
@receiver(post_save, sender=MutualFollower)
def update_mutual_follower(sender, instance, **kwargs):
    # Récupération de l'API
    api = tweepy.API(instance.user.twitter_api.auth)

    # Récupération des informations de l'utilisateur sur Twitter
    user = api.get_user(user_id=instance.user_twitter_id)

    # Mise à jour des informations dans la base de données
    instance.name = user.name
    instance.screen_name = user.screen_name
    instance.profile_image_url = user.profile_image_url.replace("_normal", "")
    instance.description = user.description
    instance.location = user.location
    instance.save()