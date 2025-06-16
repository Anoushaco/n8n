import unittest
from app.main import greet
from app.utils import get_current_time

class TestMain(unittest.TestCase):

    def test_greet(self):
        self.assertEqual(greet("Test"), "Hello, Test!")
        self.assertEqual(greet(""), "Hello, !")

    def test_get_current_time(self):
        # This test is a bit tricky as time changes.
        # We'll just check if it returns a string.
        self.assertIsInstance(get_current_time(), str)
        # A more robust test would involve mocking datetime.datetime.now()

if __name__ == "__main__":
    unittest.main()
