

import unittest

from distance import DefaultClasses
from distance.bytes import Magic, Section
from distance.base import (
    ObjectFragment,
    BaseObject,
    Fragment,
)
from distance._impl.level_objects.objects import (
    GoldenSimple,
)
from distance._impl.fragments.levelfragments import (
    GoldenSimplesFragment,
)
from distance.classes import ClassCollection, TagError


def TagFragment(name, tag, **kw):
    kw['class_tag'] = tag
    return type(name, (Fragment,), kw)


class CustomGSFragment(Fragment):
    class_tag = 'GoldenSimples'
    default_container = Section(base=GoldenSimplesFragment.base_container, version=9001)


class BaseObjectTest(unittest.TestCase):

    def test_getitem_object(self):
        obj = BaseObject()

        self.assertEqual(list(obj.fragments), [obj['Object']])

    def test_getitem_goldensimples(self):
        obj = GoldenSimple(type='CubeGS')
        frag = obj['GoldenSimples']
        expect = next(f for f in obj.fragments if isinstance(f, GoldenSimplesFragment))
        self.assertEqual(frag, expect)

    def test_getitem_empty_fragments(self):
        obj = BaseObject()
        obj.fragments = []

        with self.assertRaises(KeyError) as cm:
            obj['Object']
        self.assertEqual(cm.exception.is_present, False)

    def test_getitem_unimplemented_version(self):
        coll = ClassCollection()
        coll.add_fragment(ObjectFragment)
        coll.fragment(TagFragment('Frag1', 'Test', default_container=Section(Magic[2], 20, 1)))
        classes = DefaultClasses.copy(fragments=coll)

        obj = BaseObject(probers=classes)
        obj.fragments = [ObjectFragment(), Fragment(container=Section(Magic[2], 20, 10))]

        with self.assertRaises(KeyError) as cm:
            obj['Test']
        self.assertEqual(cm.exception.is_present, True)

    def test_setitem_replaces_fragment(self):
        obj = BaseObject(type='Test')
        child = BaseObject(type='Child')
        frag = ObjectFragment(children=[child])

        obj['Object'] = frag

        self.assertEqual(obj.fragments, [frag])
        self.assertIs(obj['Object'], frag)
        self.assertEqual(obj.children, [child])

    def test_setitem_adds_fragment(self):
        obj = BaseObject(type='Test')
        frag = GoldenSimplesFragment()

        obj['GoldenSimples'] = frag

        self.assertEqual([obj['Object'], frag], list(obj.fragments))
        self.assertIs(frag, obj['GoldenSimples'])

    def test_setitem_unknown_tag_error(self):
        obj = BaseObject(type='Test')
        frag = GoldenSimplesFragment()

        with self.assertRaises(KeyError):
            obj['TeleporterExit'] = frag

    def test_setitem_checks_fragment_type(self):
        obj = BaseObject(type='Test')
        frag = Fragment()

        with self.assertRaises(LookupError) as cm:
            obj['unknown'] = frag
        self.assertRegex(str(cm.exception), 'unknown')

    def test_delitem_removes(self):
        obj = BaseObject(type='Test')

        del obj['Object']

        self.assertEqual([], obj.fragments)
        self.assertFalse('Object' in obj)

    def test_delitem_missing(self):
        obj = BaseObject(type='Test')

        with self.assertRaises(KeyError):
            del obj['GoldenSimples']

    def test_delitem_unknown_tag_error(self):
        obj = BaseObject(type='Test')

        with self.assertRaises(TagError):
            del obj['unknown']

    def test_fragments_created_add(self):
        obj = BaseObject(type='Test')
        objfrag = obj['Object']
        gsfrag = GoldenSimplesFragment()

        obj.fragments += [gsfrag]

        self.assertEqual(list(obj.fragments), [objfrag, gsfrag])

    def test_fragments_read_add(self):
        obj = BaseObject('tests/in/customobject/2cubes.bytes')
        gsfrag = GoldenSimplesFragment()

        obj.fragments += [gsfrag]

        self.assertEqual(len(obj.fragments), 4)
        self.assertEqual(obj.fragments[-1], gsfrag)
        self.assertEqual(obj.sections[-1], gsfrag.container)

    def test_getitem_after_setitem_custom_impl(self):
        obj = BaseObject()
        frag = CustomGSFragment()

        obj['GoldenSimples'] = frag
        result = obj['GoldenSimples']
        result_any = obj.get_any('GoldenSimples')

        self.assertIs(result, frag)
        self.assertIs(result_any, frag)
        self.assertEqual(9001, obj.sections[-1].version)

    def test_contains_after_setitem_custom_impl(self):
        obj = BaseObject()
        frag = CustomGSFragment()

        obj['GoldenSimples'] = frag

        self.assertTrue('GoldenSimples' in obj)
        self.assertTrue(obj.has_any('GoldenSimples'))


# vim:set sw=4 et:
