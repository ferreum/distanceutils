#!/usr/bin/python


from setuptools import setup

import distance

setup(
    name='distanceutils',
    version=distance.__version__,
    description='Utilities for the Refract Studios game Distance',
    license='MIT',
    author_email='code.danielk@gmail.com',
    url='https://github.com/ferreum/distanceutils',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='distance game data utilities',
    packages=['distance', 'distance.filter', 'distance_scripts'],
    entry_points={
        'console_scripts': [
            'dst-bytes = distance_scripts.bytes:main',
            'dst-objtobytes = distance_scripts.objtobytes:main',
            'dst-querymaps = distance_scripts.querymaps:main',
            'dst-mklevelinfos = distance_scripts.mklevelinfos:main',
            'dst-teletodot = distance_scripts.teletodot:main',
            'dst-mkcustomobject = distance_scripts.mkcustomobject:main',
            'dst-filterlevel = distance_scripts.filterlevel:main',
        ]
    },
)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
