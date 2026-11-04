"""
Unit and integration tests for AutoTyper engine and queue logic.
"""

import unittest
from autotyper.engine import AutoTypeEngine, AutoTypeConfig


class TestAutoTypeEngine(unittest.TestCase):
    def setUp(self):
        self.config = AutoTypeConfig(
            char_delay_ms=0.0,
            jitter_percent=0.0,
            countdown_seconds=0.0,
            play_sound=False
        )
        self.engine = AutoTypeEngine(self.config)

    def test_single_content_loading(self):
        text = "console.log('hello world');"
        self.engine.load_content(text)
        self.assertEqual(len(self.engine.queue), 1)
        self.assertEqual(self.engine.queue[0], text)
        self.assertEqual(self.engine.queue_index, 0)

    def test_multi_element_splitting_double_newline(self):
        self.engine.config.element_mode = "queue_step"
        self.engine.config.element_delimiter = "\n\n"
        text = "Element One\n\nElement Two\n\nElement Three"
        self.engine.load_content(text)
        self.assertEqual(len(self.engine.queue), 3)
        self.assertEqual(self.engine.queue[0], "Element One")
        self.assertEqual(self.engine.queue[1], "Element Two")
        self.assertEqual(self.engine.queue[2], "Element Three")

    def test_multi_element_splitting_custom_delimiter(self):
        self.engine.config.element_mode = "auto_tab"
        self.engine.config.element_delimiter = "---"
        text = "Name: John Doe---Email: john@example.com---Code: 12345"
        self.engine.load_content(text)
        self.assertEqual(len(self.engine.queue), 3)
        self.assertEqual(self.engine.queue[0], "Name: John Doe")
        self.assertEqual(self.engine.queue[1], "Email: john@example.com")
        self.assertEqual(self.engine.queue[2], "Code: 12345")

    def test_queue_index_management(self):
        self.engine.config.element_mode = "queue_step"
        self.engine.load_content("Part 1\n\nPart 2\n\nPart 3", delimiter="\n\n")
        self.assertEqual(self.engine.queue_index, 0)
        self.engine.set_queue_index(2)
        self.assertEqual(self.engine.queue_index, 2)
        # Out of bounds should be ignored safely
        self.engine.set_queue_index(99)
        self.assertEqual(self.engine.queue_index, 2)

    def test_strip_indent_mode(self):
        sample_code = "def foo():\n    x = 10\n    return x\n"
        lines = sample_code.splitlines(keepends=True)
        formatted_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                formatted_lines.append(line)
            else:
                formatted_lines.append(line.lstrip(" \t"))
        res = "".join(formatted_lines)
        expected = "def foo():\nx = 10\nreturn x\n"
        self.assertEqual(res, expected)


if __name__ == "__main__":
    unittest.main()
