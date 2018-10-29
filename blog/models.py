from django.contrib.postgres.fields import ArrayField
from django.db import models


class Post(models.Model):
    uuid = models.UUIDField(primary_key=True)
    date = models.DateTimeField()
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, null=True, blank=True)
    categories = ArrayField(models.CharField(max_length=20), default=list)
    tags = ArrayField(models.CharField(max_length=20), default=list)
    keywords = ArrayField(models.CharField(max_length=20), default=list)
    content = models.TextField()
    active = models.BooleanField(default=False)
    create_datetime = models.DateTimeField(auto_now_add=True)
    update_datetime = models.DateTimeField(auto_now=True)
