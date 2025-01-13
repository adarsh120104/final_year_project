# Generated by Django 4.2.4 on 2024-12-26 08:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Telegram_Analysis', '0002_telegramgroup_delete_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_link', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=100)),
                ('message_text', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='TelegramGroup',
        ),
    ]
