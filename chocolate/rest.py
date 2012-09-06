from tastypie.resources import ModelResource
from tastypie import fields
from models import Mockup, ModelFactory

import generators
import json


FIELDCLASS_TO_GENERATOR = {
    fields.BooleanField: generators.BooleanGenerator,
    fields.DateField: generators.DateGenerator,
    fields.DateTimeField: generators.DateTimeGenerator,
    fields.IntegerField: generators.IntegerGenerator,
    fields.FloatField: generators.FloatGenerator,
    fields.TimeField: generators.TimeGenerator,
    # field generators
    fields.CharField: generators.CharFieldGenerator,
    fields.DecimalField: generators.DecimalFieldGenerator,
}


class UnregisteredResource(Exception):
    pass


class TastyMockup(object):

    def __init__(self, resource, factory):
        self.resource = resource
        self.factory = factory
        self.model_class = self.resource._meta.object_class

    def create(self, **kwargs):
        "Obtains a mockup model and its uri"

        model = self.factory.model_factory[self.model_class].create(**kwargs)

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
        output = {}

        #for key, value in mockup.data.items():
        for field_name, field in self.resource.fields.items():

            if isinstance(field, fields.ForeignKey):
                related_resource = field.to_class()
                related_model_class = self.factory[related_resource].model_class

                if kwargs.get(field_name, None).__class__ == related_model_class:
                    related_obj = kwargs[field_name]
                else:
                    related_obj = self.factory.model_factory[related_model_class].create()

                value = related_resource.get_resource_uri(related_obj)
            else:
                try:
                    generator_class = FIELDCLASS_TO_GENERATOR[field.__class__]
                    attribute = field.attribute

                    if field_name in kwargs:
                        value = kwargs[field_name]
                    elif isinstance(attribute, basestring):
                        model_field = self.model_class._meta.get_field(attribute)
                        value = Mockup.generate_value(model_field)
                    else:
                        if issubclass(generator_class, generators.FieldGenerator):
                            generator = generator_class(field)
                        elif issubclass(generator_class, generators.Generator):
                            generator = generator_class()

                        value = generator.get_value()

                    if value is None:
                        continue
                except KeyError:
                    continue

            output[field_name] = value

            try:
                del output['resource_uri']
            except KeyError:
                pass

        return output


class TastyFactory(object):

    def __init__(self, api):
        self.api = api
        self.model_factory = ModelFactory()
        self.mockups = {}

        for resource_name, resource in self.api._registry.items():
            model_class = resource._meta.object_class
            self.model_factory.register(model_class)

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
