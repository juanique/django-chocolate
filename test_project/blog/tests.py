# -*- coding: utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User

from chocolate.models import ModelFactory, Mockup
from chocolate.rest import TastyFactory
from api import api
from blog.models import Entry, Comment, Movie, Actor


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
            user = CustomMockupTestCase.modelfactory['user'].create(first_name=first_name)
            data.set("author", user)

    @classmethod
    def setUpClass(cls):
        cls.modelfactory = ModelFactory()
        cls.modelfactory.register(User, cls.UserMockup)
        cls.modelfactory.register(Comment, cls.CommentMockup)


    def test_custom_mockup(self):
        """Custom mockup clases can be used"""

        user = self.modelfactory['user'].create()
        self.assertEquals("Juan", user.first_name)

    def test_rewrite_default(self):
        """Custom top default values"""

        user = self.modelfactory['user'].create(first_name="Felipe")
        self.assertEquals("Felipe", user.first_name)

    def test_custom_nested_mockup(self):
        """Custom Comment mockup top over default User Mockup"""

        comment = self.modelfactory['comment'].create(first_name="Felipe")
        self.assertEquals('Felipe', comment.author.first_name)


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

        get_data = self.tastyfactory['entry'].create_get_data(content="Some content")

        self.assertInstanceOf(dict, get_data)
        self.assertEquals("Some content", get_data['content'])

    def test_example_post(self):
        "It can generate a sample post data."

        post_data = self.tastyfactory['comment'].create_post_data(content="Some content")

        self.assertInstanceOf(dict, post_data)
        self.assertEquals("Some content", post_data['content'])
        self.assertInstanceOf(basestring, post_data['entry'])

    def test_example_post_force(self):
        "When creating mockup test data, foreign rels can be forced."

        blog_entry_uri, blog_entry = self.tastyfactory['entry'].create()
        post_data = self.tastyfactory['comment'].create_post_data(entry=blog_entry)

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


class CustomMockupTests(BaseTestCase):

    class CommentMockup(Mockup):

        def mockup_data(self, data, **kwargs):
            first_name = data.force.get('first_name')
            user = CustomMockupTestCase.modelfactory['user'].create(first_name=first_name)
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
        comment_uri, comment = self.tastyfactory['comment'].create(first_name="Felipe")
        self.assertEqual("Felipe", comment.author.first_name)