from django.contrib.postgres.fields import ArrayField
from django.db import models


class Note(models.Model):
    uuid = models.UUIDField(primary_key=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, db_index=True)
    tags = ArrayField(models.CharField(max_length=20), default=list)
    content = models.TextField()
    active = models.BooleanField(default=False)
    create_datetime = models.DateTimeField()
    update_datetime = models.DateTimeField()
