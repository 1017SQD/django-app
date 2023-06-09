# Generated by Django 4.1 on 2023-03-31 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_alter_userprofile_lang"),
    ]

    operations = [
        migrations.AlterField(
            model_name="follower",
            name="description",
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AlterField(
            model_name="following",
            name="description",
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AlterField(
            model_name="mutualfollower",
            name="description",
            field=models.CharField(blank=True, max_length=250),
        ),
        migrations.AlterField(
            model_name="notfollowingback",
            name="description",
            field=models.CharField(blank=True, max_length=250),
        ),
    ]
