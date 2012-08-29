from django.test import TestCase

from blog.models import Post, Comment, Movie, Actor
from blog.mockups import factory


class BaseTestCase(TestCase):

    def assertInstanceOf(self, class_obj, instance):
        self.assertTrue(isinstance(instance, class_obj))

    def assertNotEmpty(self, value):
        self.assertTrue(value != [] and value != "")

class MockupTests(BaseTestCase):

    def setUp(self):
        self.mock_post = factory["post"].create()

    def test_create(self):
        "It creates a mockup object of the model"

        self.assertInstanceOf(Post, self.mock_post)

    def test_populate_textfield(self):
        "It populates textfield attributes with generated data"

        self.assertNotEmpty(self.mock_post.content)


class MockupForceTests(BaseTestCase):

    def test_populate_force(self):
        "You can force a specific value into a field."

        post = factory["post"].create(content="Homer Simpson")
        self.assertEqual('Homer Simpson', post.content)

    def test_related(self):
        "You can request to-many relationships to be mocked-up as well"

        post = factory["post"].create(comments=2)

        self.assertEqual(2, len(post.comments.all()))
        self.assertEqual(2, len(Comment.objects.all()))
        self.assertEqual(1, len(Post.objects.all()))

    def test_m2m_1(self):
        "It handles m2m relationships correctly"

        movie = factory['movie'].create(actors=2)

        self.assertEqual(2, len(movie.actors.all()))
        self.assertEqual(2, len(Actor.objects.all()))
        self.assertEqual(1, len(Movie.objects.all()))

        for actor in Actor.objects.all():
            self.assertEqual(1, len(actor.movies.all()))

    def test_m2m_2(self):
        "It handles m2m relationships correctly (other side)"

        actor = factory['actor'].create(movies=2)

        self.assertEqual(2, len(actor.movies.all()))
        self.assertEqual(1, len(Actor.objects.all()))
        self.assertEqual(2, len(Movie.objects.all()))

        for movie in Movie.objects.all():
            self.assertEqual(1, len(movie.actors.all()))
