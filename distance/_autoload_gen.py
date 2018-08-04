"""Functions for autoload generation."""


import os
import importlib

from distance.classes import ClassCollection, _load_impls_to_colls


value_types = int, float, bytes, str, bool, type(None),
sequence_types = tuple,
set_types = set,
mapping_types = dict,


def write_autoload_module(module_name, impl_modules, keys):
    parent_modname, sep, mod_basename = module_name.rpartition('.')
    parent_mod = importlib.import_module(parent_modname)
    dirname = os.path.dirname(parent_mod.__file__)
    filename = os.path.join(dirname, mod_basename + ".py")
    content = _generate_autoload_content(module_name, impl_modules, keys)
    with open(filename, 'w') as f:
        f.write(content)


def _generate_autoload_content(module_name, impl_modules, keys):
    text = [
        '''"""Auto-generated module for autoload definitions."""\n''',
        "\n",
        "# This is generated code. Do not modify.\n",
        "\n",
        "content_map = ",
    ]
    colls = {k: ClassCollection(key=k) for k in keys}
    _load_impls_to_colls(colls, impl_modules)
    content = {k: p._generate_autoload_content()
               for k, p in colls.items()}
    text.extend(_generate_source(content, 0))
    text.append("\n")
    return ''.join(text)


def _generate_source(content, indent):
    typ = type(content)
    if typ in value_types:
        yield repr(content)
    elif typ in sequence_types:
        yield "("
        for i, v in enumerate(content):
            if i:
                yield " "
            yield from _generate_source(v, indent + 1)
            yield ","
        yield ")"
    elif typ in set_types:
        if not content:
            yield "set()"
        else:
            yield "{\n"
            for v in content:
                yield "    " * (indent + 1)
                yield from _generate_source(v, indent + 1)
                yield ",\n"
            yield "    " * indent + "}"
    elif typ in mapping_types:
        yield "{\n"
        for k, v in content.items():
            yield "    " * (indent + 1)
            yield from _generate_source(k, indent + 1)
            yield ": "
            yield from _generate_source(v, indent + 1)
            yield ",\n"
        yield "    " * indent + "}"
    else:
        raise TypeError(f"Autoload content of invalid type (a {typ.__name__!r}): {content}")


# vim:set sw=4 et:
