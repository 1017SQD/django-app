# Generated by Django 4.1 on 2023-04-02 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_usertimeline_quoted_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="follower",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="following",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="mutualfollower",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="notfollowingback",
            name="location",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
