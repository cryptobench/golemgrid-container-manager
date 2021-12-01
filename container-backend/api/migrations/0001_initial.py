# Generated by Django 3.2.9 on 2021-11-09 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaskContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scene', models.CharField(blank=True, max_length=128, null=True)),
                ('task_args', models.JSONField(null=True)),
                ('task_id', models.UUIDField(unique=True)),
                ('ip', models.GenericIPAddressField(protocol='IPv4')),
                ('container_id', models.CharField(blank=True, max_length=64, null=True)),
            ],
        ),
    ]