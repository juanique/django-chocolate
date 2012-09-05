from chocolate.models import ModelFactory
from chocolate.rest import TastyFactory

from django.contrib.auth.models import User

from models import Post, Comment, Movie, Actor
from api import api

modelfactory = ModelFactory()
modelfactory.register(Post)
modelfactory.register(User)
modelfactory.register(Comment)
modelfactory.register(Movie)
modelfactory.register(Actor)

tastyfactory = TastyFactory(modelfactory, api)
