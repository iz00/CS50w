# Generated by Django 5.0.1 on 2024-02-10 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0008_alter_listing_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
