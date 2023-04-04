from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_twitter_id = models.BigIntegerField()
    name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(max_length=160, blank=True)
    protected = models.BooleanField(default=False)
    followers_count = models.IntegerField(null=True)
    friends_count = models.IntegerField(null=True)
    listed_count = models.IntegerField(null=True)
    created_at = models.DateTimeField(null=True)
    favourites_count = models.IntegerField(null=True)
    verified = models.BooleanField(default=False)
    statuses_count = models.IntegerField(null=True)
    lang = models.CharField(max_length=2, blank=True, null=True)
    profile_image_url = models.URLField(blank=True)
    profile_banner_url = models.URLField(blank=True)
    
    def __str__(self):
        return f'{self.name} ({self.screen_name})'

class UserTimeline(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(null=True)
    tweet = models.TextField(max_length=280, blank=True)
    tweet_id = models.BigIntegerField()
    sentiment = models.TextField(max_length=10, blank=True)
    polarity = models.FloatField(null=True)
    source = models.CharField(max_length=25, blank=True)
    in_reply_to_screen_name = models.CharField(max_length=15, null=True)
    is_quote_status = models.BooleanField(default=False)
    quoted_status = models.TextField(max_length=280, blank=True)
    retweet_count = models.IntegerField(null=True)
    favorite_count = models.IntegerField(null=True)
    lang = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.tweet_id}'

    class Meta:
        verbose_name_plural = 'User Timelines'

class NotFollowingBack(models.Model):
    user_twitter_id = models.BigIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    profile_image_url = models.URLField(blank=True)
    description = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f'{self.name} ({self.screen_name})'

class Follower(models.Model):
    user_twitter_id = models.BigIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    profile_image_url = models.URLField(blank=True)
    description = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f'{self.name} ({self.screen_name})'
    
class Following(models.Model):
    user_twitter_id = models.BigIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    profile_image_url = models.URLField(blank=True)
    description = models.CharField(max_length=250, blank=True)
    
    def __str__(self):
        return f'{self.name} ({self.screen_name})'

class MutualFollower(models.Model):
    user_twitter_id = models.BigIntegerField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=15)
    location = models.CharField(max_length=255, blank=True)
    profile_image_url = models.URLField(blank=True)
    description = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return f'{self.name} ({self.screen_name})'