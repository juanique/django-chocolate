from chocolate import Factory
from django.contrib.auth.models import User
from models import Post, Comment, Movie, Actor

factory = Factory()
factory.register(Post)
factory.register(User)
factory.register(Comment)
factory.register(Movie)
factory.register(Actor)
