from tastypie.resources import ModelResource
from tastypie.api import Api
from tastypie import fields
from models import Entry, Comment


class EntryResource(ModelResource):

    class Meta:
        queryset = Entry.objects.all()


class CommentResource(ModelResource):

    entry = fields.ForeignKey("blog.api.EntryResource", attribute="entry")
    upvotes = fields.IntegerField(readonly=True)

    class Meta:
        queryset = Comment.objects.all()


api = Api(api_name="v1")
api.register(EntryResource())
api.register(CommentResource())
