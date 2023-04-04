from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='main-home'),
    path("test", views.user_timeline, name='user-timeline'),
    path('non_followers', views.non_followers, name='non-followers'),
    path('mutual_followers', views.mutual_followers, name='mutual-followers'),
    path('unfollow/<int:user_id>/', views.unfollow, name='unfollow'),
    path('followers', views.followers, name='followers'),
    path('following', views.following, name='following'),
    path('tweets', views.tweets, name='tweets'),
]