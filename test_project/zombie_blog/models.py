from blog.models import Comment
from django.db import models
from django.contrib.auth.models import User as DjangoUser

class User(DjangoUser):
    brains_eaten = models.IntegerField(default=0)

class Entry(models.Model):
    content = models.TextField()
    zombie_author = models.ForeignKey(User, related_name="zombie_entries")
    created = models.DateTimeField()
    zombie_count = models.IntegerField(default=1)

class GutturalComment(Comment):
    translation = models.TextField()
