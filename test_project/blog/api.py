from tastypie.resources import ModelResource
from tastypie.api import Api
from models import Post


class PostResource(ModelResource):

    class Meta:
        queryset = Post.objects.all()

api = Api(api_name="v1")
api.register(PostResource())
