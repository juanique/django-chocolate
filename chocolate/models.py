# -*- coding: utf-8 -*-
import types

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import NOT_PROVIDED
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.db.models.fields.related import ManyRelatedObjectsDescriptor
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor
from django.db import models

import generators


FIELDCLASS_TO_GENERATOR = {
    models.BooleanField: generators.BooleanGenerator,
    models.DateField: generators.DateGenerator,
    models.DateTimeField: generators.DateTimeGenerator,
    models.EmailField: generators.EmailGenerator,
    models.IntegerField: generators.IntegerGenerator,
    models.BigIntegerField: generators.IntegerGenerator,
    models.FloatField: generators.FloatGenerator,
    models.IPAddressField: generators.IPAddressGenerator,
    models.NullBooleanField: generators.NullBooleanGenerator,
    models.PositiveIntegerField: generators.PositiveIntegerGenerator,
    models.PositiveSmallIntegerField: generators.PositiveSmallIntegerGenerator,
    models.SlugField: generators.SlugGenerator,
    models.SmallIntegerField: generators.SmallIntegerGenerator,
    models.TextField: generators.LoremGenerator,
    models.TimeField: generators.TimeGenerator,
    models.URLField: generators.URLGenerator,
    # field generators
    models.CharField: generators.CharFieldGenerator,
    models.DecimalField: generators.DecimalFieldGenerator,
    models.FilePathField: generators.FilePathFieldGenerator,
}


class UnregisteredModel(Exception):
    pass


def get_field_from_related_name(model_class, related_name):
    for field in model_class._meta.local_fields:
        try:
            if field.related.get_accessor_name() == related_name:
                return field
        except AttributeError:
            pass
    return None


class ModelFactory(object):

    def __init__(self):
        self.mockups = {}

    def get_key(self, model):
        """ Returns the key of a mockup class for a given model """
        key = model
        if not isinstance(model, basestring):
            content_type = ContentType.objects.get_for_model(model)
            key = ".".join(content_type.natural_key())

        return key.lower()

    def register(self, model, mockup_class=None):
        """Registers a model to allow mockup creations of that model."""

        mockup_class = mockup_class or Mockup

        key = self.get_key(model)
        self.mockups[key] = mockup_class(model, self)

    def __getitem__(self, model):
        key = self.get_key(model)

        try:
            return self.mockups[key]
        except KeyError:
            if not isinstance(model, basestring):
                self.register(model)
                return self[model]
            raise UnregisteredModel(key)


class MockupData(object):

    def __init__(self, factory=None, force=None):
        self.data = {}
        self.force = force or {}
        self.factory = factory

        self.preset_forced()

    def preset_forced(self):
        """Sets the forced data onto the dataset."""

        self.data.update(self.force)

    def __getitem__(self, name):
        return self.data[name]

    def __setitem__(self, name, value):
        self.data[name] = value

    def __delitem__(self, name):
        del self.data[name]

    def update(self, data):
        return self.data.update(data)

    def to_dict(self):
        return self.data

    def set(self, name, constant=None, model=None):
        if name in self.force:
            #Already forced
            return

        if model is not None:
            obj = self.factory[model].create()
            self.data[name] = obj
            return

        if constant is not None:
            self.data[name] = constant
            return

    def get_data_dict(self, fields):
        data = {}

        for field in fields:
            try:
                data[field] = self[field]
            except KeyError:
                #we have no data for this field.
                pass

        return data

    def create_model(self, model_class):
        "Obtains an instance of the model using this data set."

        tomany_fields, regular_fields = self.get_fields(model_class)

        tomany_data = self.get_data_dict(tomany_fields)
        regular_data = self.get_data_dict(regular_fields)

        model = model_class(**regular_data)
        model.save()

        for tomany_field, values in tomany_data.items():
            manager = getattr(model, tomany_field)
            related_model = manager.model

            reverse_related_name = get_field_from_related_name(
                related_model, tomany_field)

            if type(values) is int:
                objs = []
                for x in range(0, values):
                    if reverse_related_name is None:
                        data = {}
                    else:
                        data = {reverse_related_name.name: model}
                    objs.append(self.factory[related_model].create(**data))
                values = objs
            if type(values) is not list:
                values = [values]

            try:
                for value in values:
                    force = {}
                    for field in manager.through._meta.fields:
                        if isinstance(field, ForeignKey):
                            if isinstance(model, field.rel.to):
                                force[field.name] = model
                            elif isinstance(value, field.rel.to):
                                force[field.name] = value
                    self.factory[manager.through].create(**force)
            except AttributeError:
                for value in values:
                    manager.add(value)
        return model

    def get_fields(self, model_class):
        """Obtains a list of fields of the given model class separated
        between to-many and non-to-many (regular)"""

        many = []
        regular = []

        class_fields = model_class._meta.get_all_field_names()
        for field in class_fields:
            try:
                field_obj = model_class._meta.get_field(field)
                is_tomany = isinstance(field_obj, ManyToManyField)
            except Exception:
                try:
                    field_obj = getattr(model_class, field)
                    is_tomany = isinstance(
                        field_obj,
                        ForeignRelatedObjectsDescriptor)
                    is_tomany = is_tomany or isinstance(
                        field_obj, ManyRelatedObjectsDescriptor)
                except AttributeError:
                    #probably a to-many field with no reverse relationship
                    #defined
                    continue

            if is_tomany:
                many.append(field)
            else:
                regular.append(field)

        return many, regular


class Mockup(object):

    def __init__(self, model_class, factory):
        self.model_class = model_class
        self.factory = factory

    @staticmethod
    def generate_value(field, model_data=None):
        """Obtains a automatically generated value for a given a django model
        field

        """
        value = None
        if field.default is not NOT_PROVIDED:
            if type(field.default) in [types.FunctionType, types.LambdaType]:
                value = field.default()
            else:
                value = field.default
        else:
            field_type = type(field)
            generator_class = FIELDCLASS_TO_GENERATOR[field_type]
            if issubclass(generator_class, generators.FieldGenerator):
                generator = generator_class(field)
            elif issubclass(generator_class, generators.Generator):
                generator = generator_class()
            value = generator.get_value()
            if field.unique:
                while True:
                    try:
                        field.model.objects.get(**{field.name: value})
                        value = generator.get_value()
                    except:
                        break
        if value is not None:
            if model_data:
                model_data.set(field.name, value)
            else:
                return value

    def mockup_data(self, data):
        pass

    def get_mockup_data(self, **kwargs):

        force = kwargs

        model_class = self.model_class
        model_data = MockupData(force=force, factory=self.factory)

        self.mockup_data(model_data)

        fields = model_class._meta.fields
        for field in fields:

            if field.name in model_data.data:
                continue

            if isinstance(field, ForeignKey):
                related_model = field.rel.to
                model_data.set(field.name, model=related_model)
            else:
                try:
                    Mockup.generate_value(field, model_data)
                except KeyError, e:
                    if e.args[0] != models.fields.AutoField:
                        msg = "Could not mockup data for %s.%s %s"
                        msg %= (model_class.__name__, field.name, e.args[0])
                        raise Exception(msg)

        return model_data

    def create(self, **kwargs):
        """Creates a mockup object."""

        return self.get_mockup_data(**kwargs).create_model(self.model_class)
