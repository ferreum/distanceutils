import unittest
from io import StringIO
from textwrap import dedent

from distance.printing import PrintContext


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.out = StringIO()
        self.p = PrintContext.for_test(file=self.out)

    def assertResult(self, expect):
        if expect.startswith('\n'):
            expect = expect[1:]
        self.assertEqual(self.out.getvalue(), dedent(expect))


class TreeTest(BaseTest):

    def test_basic(self):
        p = self.p
        p("Root")
        with p.tree_children():
            p.tree_next_child()
            p(f"First")
            p.tree_next_child()
            p(f"Second")

        self.assertResult("""
        Root
        ├─ First
        └─ Second
        """)

    def test_next_child_after_object(self):
        p = self.p
        p("Root")
        with p.tree_children():
            p(f"First")
            p.tree_next_child()
            p(f"Second")
            p.tree_next_child()

        self.assertResult("""
        Root
        ├─ First
        └─ Second
        """)

    def test_nested(self):
        p = self.p
        p("Root")
        with p.tree_children():
            p.tree_next_child()
            p(f"First")
            with p.tree_children():
                p.tree_next_child()
                p(f"Second")
            p.tree_next_child()
            p(f"Third")
        self.assertResult("""
        Root
        ├─ First
        │  └─ Second
        └─ Third
        """)

    def test_nested_after_empty(self):
        # Nested tree cannot start after empty child - it
        # connects to the line before it.
        p = self.p
        p("Root")
        with p.tree_children():
            p.tree_next_child()
            p(f"First")
            p.tree_next_child()
            with p.tree_children():
                p.tree_next_child()
                p(f"Second")
            p(f"Third")
        self.assertResult("""
        Root
        ├─ First
        │  └─ Second
        └─ Third
        """)

    def test_nested_end_empty(self):
        p = self.p
        p("Root")
        with p.tree_children():
            p.tree_next_child()
            p(f"First")
            p.tree_next_child()
            with p.tree_children():
                p.tree_next_child()
                p(f"Second")
                with p.tree_children():
                    p.tree_next_child()
        self.assertResult("""
        Root
        └─ First
           └─ Second
        """)

    def test_count_unbuffered(self):
        p = self.p
        p("Root")
        with p.tree_children(2):
            p(f"First")

            self.assertResult("""
            Root
            ├─ First
            """)

            p.tree_next_child()

            p(f"Second")

            self.assertResult("""
            Root
            ├─ First
            └─ Second
            """)

            p.tree_next_child()
        self.assertResult("""
        Root
        ├─ First
        └─ Second
        """)

    def test_count_unbuffered_nested(self):
        p = self.p
        p("Root")
        with p.tree_children(2):
            p.tree_next_child()

            p(f"First")
            with p.tree_children(1):
                p.tree_next_child()
                p(f"One")

            p.tree_next_child()
            p(f"Second")

            with p.tree_children(1):
                p(f"Two")
                p.tree_next_child()
            p.tree_next_child()

        self.assertResult("""
        Root
        ├─ First
        │  └─ One
        └─ Second
           └─ Two
        """)

    def test_multiline_child(self):
        p = self.p
        p("Root")
        with p.tree_children():
            p(f"First 0")
            p(f"First 1")
            p(f"First 2")

        self.assertResult("""
        Root
        └─ First 0
           First 1
           First 2
        """)

    def test_multiline_child_unbuffered(self):
        p = self.p
        p("Root")
        with p.tree_children(1):
            p(f"First 0")
            p(f"First 1")
            p(f"First 2")

        self.assertResult("""
        Root
        └─ First 0
           First 1
           First 2
        """)

    def test_buffered_within_unbuffered(self):
        p = self.p
        p("Root")
        with p.tree_children(1):
            p(f"Child 0")
            with p.tree_children():
                p(f"Child 0-0")

        self.assertResult("""
        Root
        └─ Child 0
           └─ Child 0-0
        """)


# vim:set sw=4 ts=8 sts=4 et:
