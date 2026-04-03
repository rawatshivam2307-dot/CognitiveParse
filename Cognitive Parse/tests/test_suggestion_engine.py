import unittest

from backend.suggestion_engine import suggest


class SuggestionEngineTests(unittest.TestCase):
    def test_missing_colon_pattern(self):
        text = suggest(token="", message="invalid syntax", line_text="if x > 0")
        self.assertIn("Add ':'", text)

    def test_keyword_similarity(self):
        text = suggest(token="whle", message="invalid syntax", line_text="whle x > 0:")
        self.assertIn("while", text)

    def test_unterminated_message(self):
        text = suggest(token="", message="unterminated string literal", line_text="x = 'abc")
        self.assertIn("unfinished", text)


if __name__ == "__main__":
    unittest.main()
