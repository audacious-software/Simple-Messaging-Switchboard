# pylint: skip-file
# Generated by Django 3.2.15 on 2022-09-29 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
                ('package_name', models.CharField(max_length=1024, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
                ('identifier', models.SlugField(max_length=1024, unique=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('configuration', models.TextField(default='{}')),
                ('channel_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simple_messaging_switchboard.channeltype')),
            ],
        ),
    ]
