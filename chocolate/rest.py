from tastypie.resources import ModelResource
import json


class UnregisteredResource(Exception):
    pass


class TastyMockup(object):

    def __init__(self, resource, factory):
        self.resource = resource
        self.factory = factory

    def create(self, **kwargs):
        "Obtains a mockup model and its uri"

        model_class = self.resource._meta.object_class
        model = self.factory.model_factory[model_class].create(**kwargs)

        return self.resource.get_resource_uri(model), model

    def create_get_data(self, format=None, **kwargs):
        """Obtains a data set as it may be obtained from a GET request.
        If a format is provided, a string is returned using the specified format.
        If no format is provided, the data is returned as a python dict.

        """
        model_uri, model = self.create(**kwargs)
        bundle = self.resource.build_bundle(obj=model, request=None)
        bundle = self.resource.full_dehydrate(bundle)

        if not format:
            json_str = self.resource.serialize(None, bundle, "application/json")
            return json.loads(json_str)
        else:
            return self.resource.serialize(None, bundle, format)

    def create_post_data(self, format=None, **kwargs):
        """Obtains a data set which may be posted to create a new
        object for the mocked up resource.

        """
        model_class = self.resource._meta.object_class
        mockup = self.factory.model_factory[model_class].get_mockup_data()

        output = {}

        #for key, value in mockup.data.items():
        for field in self.resource.fields:
            print "===%s===" % field
            try:
                value = mockup.data[field]
                print "%s => %s" % (field, value)
            except KeyError:
                pass

        return output


class TastyFactory(object):

    def __init__(self, model_factory, api):
        self.api = api
        self.model_factory = model_factory
        self.mockups = {}

        for resource_name, resource in self.api._registry.items():
            print resource
            model_class = resource._meta.object_class

            self.register(resource)
            self.model_factory.register(model_class)

    def get_key(self, resource):
        key = resource
        if isinstance(resource, ModelResource):
            key = resource.__class__.__name__

        key = key.lower()

        if key.endswith("resource"):
            key = key[0:-len("resource")]

        return key

    def register(self, resource):
        """Registers a resource to allow mockup creations of that resource's model."""

        key = self.get_key(resource)

        self.mockups[key] = TastyMockup(resource, self)

    def __getitem__(self, resource):
        key = self.get_key(resource)

        try:
            return self.mockups[key]
        except KeyError:
            raise UnregisteredResource(key)
