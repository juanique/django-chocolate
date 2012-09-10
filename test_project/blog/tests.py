from django.test import TestCase

from blog.models import Post, Comment, Movie, Actor

from blog.mockups import modelfactory
from blog.mockups import tastyfactory


class BaseTestCase(TestCase):

    def assertInstanceOf(self, class_obj, instance):
        self.assertTrue(isinstance(instance, class_obj))

    def assertNotEmpty(self, value):
        self.assertTrue(value != [] and value != "")


class MockupTests(BaseTestCase):

    def setUp(self):
        self.mock_post = modelfactory["post"].create()

    def test_create(self):
        "It creates a mockup object of the model"

        self.assertInstanceOf(Post, self.mock_post)

    def test_populate_textfield(self):
        "It populates textfield attributes with generated data"

        self.assertNotEmpty(self.mock_post.content)


class MockupForceTests(BaseTestCase):

    def test_populate_force(self):
        "You can force a specific value into a field."

        post = modelfactory["post"].create(content="Homer Simpson")
        self.assertEqual('Homer Simpson', post.content)

    def test_related_quantity(self):
        """You can request to-many relationships to be mocked-up
        specifing the ammount of related objs."""

        post = modelfactory["post"].create(comments=2)

        self.assertEqual(2, len(post.comments.all()))
        self.assertEqual(2, len(Comment.objects.all()))
        self.assertEqual(1, len(Post.objects.all()))

    def test_related_explicit(self):
        """You can request to-many relationships to be mocked-up
        expliciting the related objs."""

        comment1 = modelfactory['comment'].create()
        comment2 = modelfactory['comment'].create()
        comments = [comment1, comment2]

        post = modelfactory["post"].create(comments=comments)

        self.assertEqual(set(post.comments.all()), set(comments))

    def test_m2m_quantity_1(self):
        "It handles m2m relationships correctly"

        movie = modelfactory['movie'].create(actors=2)

        self.assertEqual(2, len(movie.actors.all()))
        self.assertEqual(2, len(Actor.objects.all()))
        self.assertEqual(1, len(Movie.objects.all()))

        for actor in Actor.objects.all():
            self.assertEqual(1, len(actor.movies.all()))

    def test_m2m_quantity_2(self):
        "It handles m2m relationships correctly (other side)"

        actor = modelfactory['actor'].create(movies=2)

        self.assertEqual(2, len(actor.movies.all()))
        self.assertEqual(1, len(Actor.objects.all()))
        self.assertEqual(2, len(Movie.objects.all()))

        for movie in Movie.objects.all():
            self.assertEqual(1, len(movie.actors.all()))


class MockupResourceTests(BaseTestCase):

    def test_create_resource(self):
        "It allows the creation of test resources."

        post_uri, post = tastyfactory['post'].create()

        self.assertInstanceOf(Post, post)
        self.assertInstanceOf(basestring, post_uri)

    def test_example_get(self):
        "It can generate a sample get response."

        get_data = tastyfactory['post'].create_get_data(content="Some content")

        self.assertInstanceOf(dict, get_data)
        self.assertEquals("Some content", get_data['content'])

    def test_example_post(self):
        "It can generate a sample post data."

        post_data = tastyfactory['comment'].create_post_data(content="Some content")

        self.assertInstanceOf(dict, post_data)
        self.assertEquals("Some content", post_data['content'])
        self.assertInstanceOf(basestring, post_data['post'])

    def test_example_post_force(self):
        "When creating mockup test data, foreign rels can be forced."

        blog_post_uri, blog_post = tastyfactory['post'].create()
        post_data = tastyfactory['comment'].create_post_data(post=blog_post)

        self.assertInstanceOf(dict, post_data)
        self.assertEquals(blog_post_uri, post_data['post'])

    def test_create_resource_no_tz(self):
        """It allows the creation of test resources.
        with datetime fields even if USE_TZ is set to False

        """

        with self.settings(USE_TZ=False):
            post_uri, post = tastyfactory['post'].create()

        self.assertInstanceOf(Post, post)
        self.assertInstanceOf(basestring, post_uri)
