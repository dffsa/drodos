# Generated by Django 2.0.4 on 2018-05-08 15:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sitepr', '0024_auto_20180508_1557'),
    ]

    operations = [
        migrations.RenameField(
            model_name='storeditem',
            old_name='groupOnly',
            new_name='groupShared',
        ),
    ]