# Generated by Django 4.2 on 2023-11-03 15:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0002_alter_gameturn_current_player"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamesession",
            name="chat_messages",
            field=models.ManyToManyField(blank=True, to="game.chatmessage"),
        ),
    ]
