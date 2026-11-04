"""
Unit and integration tests for AutoTyper engine, queue logic, and code indentation.
"""

import unittest
from autotyper.engine import AutoTypeEngine, AutoTypeConfig


class TestAutoTypeEngine(unittest.TestCase):
    def setUp(self):
        self.config = AutoTypeConfig(
            char_delay_ms=0.0,
            jitter_percent=0.0,
            countdown_seconds=0.0,
            play_sound=False,
            indent_mode="code_editor"
        )
        self.engine = AutoTypeEngine(self.config)

    def test_single_content_loading(self):
        text = "def foo():\n    return 42"
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
        self.engine.set_queue_index(99)
        self.assertEqual(self.engine.queue_index, 2)

    def test_crlf_normalization(self):
        text_crlf = "Line 1\r\nLine 2\r\nLine 3"
        self.engine.load_content(text_crlf)
        self.assertEqual(self.engine.queue[0], "Line 1\nLine 2\nLine 3")


if __name__ == "__main__":
    unittest.main()
