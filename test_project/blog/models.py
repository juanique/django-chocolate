from django.db import models
from django.contrib.auth.models import User


class Entry(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField()


class Comment(models.Model):
    post = models.ForeignKey(Entry, related_name='comments')
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField()


class SmartTag(models.Model):
    entry = models.ForeignKey(Entry, related_name='smart_tags')
    name = models.CharField(max_length=32)


class Actor(models.Model):
    name = models.CharField(max_length=32)


class Movie(models.Model):
    name = models.CharField(max_length=32)
    actors = models.ManyToManyField(Actor, related_name='movies')
    score = models.IntegerField(default=0)
