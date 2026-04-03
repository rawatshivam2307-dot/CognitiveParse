import unittest

from backend.parser import cognitive_parser


class ParserTests(unittest.TestCase):
    def test_valid_general_python_code(self):
        code = """
from dataclasses import dataclass

@dataclass
class Item:
    name: str

def build(values):
    return [v * 2 for v in values if v % 2 == 0]

async def main():
    data = build([1, 2, 3, 4])
    print({"result": data})
"""
        result = cognitive_parser.parse_code(code)
        self.assertTrue(result.valid)
        self.assertEqual(result.ast["root"], "Module")
        self.assertGreater(result.ast["node_count"], 0)

    def test_detect_syntax_error(self):
        code = "def broken(:\n    pass\n"
        with self.assertRaises(SyntaxError):
            cognitive_parser.parse_code(code)

    def test_detect_indentation_error(self):
        code = "if True:\nprint('x')\n"
        with self.assertRaises(SyntaxError) as ctx:
            cognitive_parser.parse_code(code)
        self.assertIn("indent", str(ctx.exception).lower())

    def test_detect_unterminated_construct(self):
        code = "x = [1, 2, 3\n"
        with self.assertRaises(SyntaxError) as ctx:
            cognitive_parser.parse_code(code)
        self.assertTrue(any(k in str(ctx.exception).lower() for k in ["closed", "eof", "unterminated", "was never closed"]))


if __name__ == "__main__":
    unittest.main()
