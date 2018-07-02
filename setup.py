#!/usr/bin/python


from setuptools import setup

import runpy


version = runpy.run_path('distance/_version.py')['__version__']

setup(
    name='distanceutils',
    version=version,
    description='Utilities for the Refract Studios game Distance',
    license='MIT',
    author_email='code.danielk@gmail.com',
    url='https://gitlab.com/ferreum/distanceutils',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'construct>=2.8,<3.0',
        'numpy>=1.13.3,<2.0',
        'numpy-quaternion>=2017.10.19',
    ],
    keywords='distance user profile level map game data utilities',
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


# vim:set sw=4 ts=8 sts=4 et:
