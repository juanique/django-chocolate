from django.db import models
from django.contrib.auth.models import User


class Entry(models.Model):
    content = models.TextField()
    zombie_author = models.ForeignKey(User, related_name="zombie_entries")
    created = models.DateTimeField()
    zombie_count = models.IntegerField(default=1)

class Comment(models.Model):
    post = models.ForeignKey(Entry, related_name='zombie_comments')
    content = models.TextField()
    zombie_author = models.ForeignKey(User,
                                      related_name="authored_zombie_comments")
    created = models.DateTimeField()
