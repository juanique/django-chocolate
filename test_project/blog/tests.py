# -*- coding: utf-8 -*-
""" tests for the blog app """
from api import api

from django.test import TestCase
from django.contrib.auth.models import User

from mock import patch

from chocolate.models import ModelFactory, Mockup
from chocolate.models import UnregisteredModel, MultipleMockupsReturned
from chocolate.generators import CharFieldGenerator
from chocolate.rest import TastyFactory

from blog.models import Entry, Comment, SmartTag, Movie, Actor

from zombie_blog.models import Entry as ZombieEntry
from zombie_blog.models import User as ZombieUser
from zombie_blog.models import GutturalComment


class BaseTestCase(TestCase):

    def assertInstanceOf(self, class_obj, instance):
        self.assertTrue(isinstance(instance, class_obj))

    def assertNotEmpty(self, value):
        self.assertTrue(value != [] and value != "")


class ChocolateTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.modelfactory = ModelFactory()
        cls.modelfactory.register(Entry)
        cls.modelfactory.register(User)
        cls.modelfactory.register(Comment)
        cls.modelfactory.register(SmartTag)
        cls.modelfactory.register(Movie)
        cls.modelfactory.register(Actor)

        cls.tastyfactory = TastyFactory(api)


class CustomMockupTestCase(BaseTestCase):

    class UserMockup(Mockup):

        def mockup_data(self, data, **kwargs):
            data.set("first_name", "Juan")

    class CommentMockup(Mockup):

        def mockup_data(self, data, **kwargs):
            first_name = data.force.get('first_name')
            user = CustomMockupTestCase.modelfactory[User].create(
                first_name=first_name)
            data.set("author", user)
            data.set("rating", None)

    @classmethod
    def setUpClass(cls):
        cls.modelfactory = ModelFactory()
        cls.modelfactory.register(User, cls.UserMockup)
        cls.modelfactory.register(Comment, cls.CommentMockup)

    def test_custom_mockup(self):
        """Custom mockup clases can be used"""

        user = self.modelfactory[User].create()
        self.assertEquals("Juan", user.first_name)

    def test_rewrite_default(self):
        """Custom top default values"""

        user = self.modelfactory[User].create(first_name="Felipe")
        self.assertEquals("Felipe", user.first_name)

    def test_custom_nested_mockup(self):
        """Custom Comment mockup top over default User Mockup"""

        comment = self.modelfactory['comment'].create(first_name="Felipe")
        self.assertEquals('Felipe', comment.author.first_name)

    def test_none_values_in_data(self):
        """Custom Comment mockup with None value for the rating attribute"""

        comment = self.modelfactory['comment'].create(first_name="Felipe")
        self.assertIsNone(comment.rating)


class MockupTests(ChocolateTestCase):

    @classmethod
    def setUpClass(cls):
        super(MockupTests, cls).setUpClass()
        cls.mock_entry = cls.modelfactory["entry"].create()

    def test_create(self):
        "It creates a mockup object of the model"

        self.assertInstanceOf(Entry, self.mock_entry)

    def test_populate_textfield(self):
        "It populates textfield attributes with generated data"

        self.assertNotEmpty(self.mock_entry.content)


class MockupForceTests(ChocolateTestCase):

    def test_populate_force(self):
        "You can force a specific value into a field."

        entry = self.modelfactory["entry"].create(content="Homer Simpson")
        self.assertEqual('Homer Simpson', entry.content)

    def test_related_quantity(self):
        """You can request to-many relationships to be mocked-up
        specifing the ammount of related objs."""

        entry = self.modelfactory["entry"].create(comments=2)

        self.assertEqual(2, len(entry.comments.all()))
        self.assertEqual(2, len(Comment.objects.all()))
        self.assertEqual(1, len(Entry.objects.all()))

    def test_related_explicit(self):
        """You can request to-many relationships to be mocked-up
        expliciting the related objs."""

        comment1 = self.modelfactory['comment'].create()
        comment2 = self.modelfactory['comment'].create()
        comments = [comment1, comment2]

        entry = self.modelfactory["entry"].create(comments=comments)

        self.assertEqual(set(entry.comments.all()), set(comments))

    def test_m2m_quantity_1(self):
        "It handles m2m relationships correctly"

        movie = self.modelfactory['movie'].create(actors=2)

        self.assertEqual(2, len(movie.actors.all()))
        self.assertEqual(2, len(Actor.objects.all()))
        self.assertEqual(1, len(Movie.objects.all()))

        for actor in Actor.objects.all():
            self.assertEqual(1, len(actor.movies.all()))

    def test_m2m_quantity_2(self):
        "It handles m2m relationships correctly (other side)"

        actor = self.modelfactory['actor'].create(movies=2)

        self.assertEqual(2, len(actor.movies.all()))
        self.assertEqual(1, len(Actor.objects.all()))
        self.assertEqual(2, len(Movie.objects.all()))

        for movie in Movie.objects.all():
            self.assertEqual(1, len(movie.actors.all()))


class MockupResourceTests(ChocolateTestCase):

    def test_create_resource(self):
        "It allows the creation of test resources."

        entry_uri, entry = self.tastyfactory['entry'].create()

        self.assertInstanceOf(Entry, entry)
        self.assertInstanceOf(basestring, entry_uri)

    def test_example_get(self):
        "It can generate a sample get response."

        get_data = self.tastyfactory['entry'].create_get_data(
            content="Some content")

        self.assertInstanceOf(dict, get_data)
        self.assertEquals("Some content", get_data['content'])

    def test_example_post(self):
        "It can generate a sample post data."

        post_data = self.tastyfactory['comment'].create_post_data(
            content="Some content")

        self.assertInstanceOf(dict, post_data)
        self.assertEquals("Some content", post_data['content'])
        self.assertInstanceOf(basestring, post_data['entry'])

    def test_example_post_force(self):
        "When creating mockup test data, foreign rels can be forced."

        blog_entry_uri, blog_entry = self.tastyfactory['entry'].create()
        post_data = self.tastyfactory['comment'].create_post_data(
            entry=blog_entry)

        self.assertInstanceOf(dict, post_data)
        self.assertEquals(blog_entry_uri, post_data['entry'])

    def test_create_resource_no_tz(self):
        """It allows the creation of test resources.
        with datetime fields even if USE_TZ is set to False

        """

        with self.settings(USE_TZ=False):
            entry_uri, entry = self.tastyfactory['entry'].create()

        self.assertInstanceOf(Entry, entry)
        self.assertInstanceOf(basestring, entry_uri)

    def test_no_readonly_post_data(self):
        """Readonly attributes are not generated for post data."""

        post_data = self.tastyfactory['comment'].create_post_data()
        self.assertTrue('upvotes' not in post_data)

    def test_no_resource_id_postdata(self):
        """The resource_uri and id fields are excluded since they
        are generated on creation"""

        post_data = self.tastyfactory['comment'].create_post_data()
        self.assertTrue('resource_uri' not in post_data)
        self.assertTrue('id' not in post_data)

    def test_key_can_equal_resource_name(self):
        """The key will be based upon the 'resource_name' attribute if it
        exists."""
        resources = self.tastyfactory.api._canonicals
        for resource_name in resources:
            resource = resources[resource_name]
            key = self.tastyfactory.get_key(resource)

            # calling the canonical_resource_for method is a way of asserting
            # the key used by the tasty factory is the resource_name of the
            #  resource class
            api.canonical_resource_for(key)


class CustomMockupTests(BaseTestCase):

    class CommentMockup(Mockup):

        def mockup_data(self, data, **kwargs):
            first_name = data.force.get('first_name')
            user = CustomMockupTestCase.modelfactory[User].create(
                first_name=first_name)
            data.set("author", user)

    @classmethod
    def setUpClass(cls):
        cls.modelfactory = ModelFactory()
        cls.modelfactory.register(Entry)
        cls.modelfactory.register(User)
        cls.modelfactory.register(Comment, cls.CommentMockup)
        cls.modelfactory.register(Movie)
        cls.modelfactory.register(Actor)

        cls.tastyfactory = TastyFactory(api, cls.modelfactory)

    def test_tasty_factory(self):
        comment_uri, comment = self.tastyfactory['comment'].create(
            first_name="Felipe")
        self.assertEqual("Felipe", comment.author.first_name)


class MockupDefaultValues(ChocolateTestCase):

    def test_check_default_value_on_movie_score(self):
        "It create a mockup with default values instead random"

        movie = self.modelfactory["movie"].create()
        self.assertEquals(0, movie.score)


class DuplicateUniqueValuesTests(ChocolateTestCase):

    @patch.object(CharFieldGenerator, 'get_value')
    def test_throw_exception_duplicate_unique_value(self, mock_my_method):
        """It must return different value if an unique value is duplicated"""

        list_of_return_values = [u'Movie_1', u'Movie_2', u'Movie_2']

        def side_effect():
            return list_of_return_values.pop()

        mock_my_method.side_effect = side_effect

        movie_1 = self.modelfactory["movie"].create()
        movie_2 = self.modelfactory["movie"].create()
        self.assertNotEquals(movie_1.name, movie_2.name)


class RepeatedModelNameTests(ChocolateTestCase):
    """ Tests for the case in which different apps have models with the same
    name

    """

    def test_models_with_same_name(self):
        """ tests that the __getitem__ method of ModelFactory correctly
        throws exceptions when models with the same name are registered

        """
        # test that pre-registering the zombie_blog.models.Entry model,
        # everything works as usual

        self.modelfactory["entry"].create()
        self.modelfactory["blog.entry"].create()
        self.modelfactory[Entry].create()
        with self.assertRaises(UnregisteredModel):
            self.modelfactory["zombie_blog.entry"].create()

        # now register the ZombieEntry
        self.modelfactory.register(ZombieEntry)

        with self.assertRaises(MultipleMockupsReturned):
            self.modelfactory["entry"].create()
        self.modelfactory["blog.entry"].create()
        self.modelfactory["zombie_blog.entry"].create()


class ModelInheritanceTests(ChocolateTestCase):
    """ Tests for the case in which model inheritance is applied """

    def test_model_inheritance(self):
        """ tests that the __getitem__ method of ModelFactory correctly
        throws exceptions when a registered model inherits from other model.

        """

        self.modelfactory.register(GutturalComment)

        comment_count = Comment.objects.all().count()
        gutural_comment_count = GutturalComment.objects.all().count()

        self.modelfactory[GutturalComment].create()

        self.assertEquals(comment_count + 1, Comment.objects.all().count())
        self.assertEquals(gutural_comment_count + 1,
                          GutturalComment.objects.count())

    def test_same_name_model_inheritance(self):
        """ tests that the __getitem__ method of ModelFactory correctly
        throws exceptions when a registered model inherits from other model
        with the same name

        """
        # test that pre-registering the zombie_blog.models.User model,
        # everything works as usual
        self.modelfactory["user"].create()
        self.modelfactory["auth.user"].create()
        self.modelfactory[User].create()
        with self.assertRaises(UnregisteredModel):
            self.modelfactory["zombie_blog.user"].create()

        # now register the ZombieUser
        self.modelfactory.register(ZombieUser)

        with self.assertRaises(MultipleMockupsReturned):
            self.modelfactory["user"].create()
        self.modelfactory["auth.user"].create()
        self.modelfactory["zombie_blog.user"].create()
