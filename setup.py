#!/usr/bin/python


from setuptools import setup


setup(
    name='distanceutils',
    version='0.1',
    description='Utilities for the game Distance by Refract Studios',
    license='MIT',
    author_email='code.danielk@gmail.com',
    url='https://github.com/ferreum/distanceutils',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='distance game data utilities',
    packages=['distance', 'distance_scripts'],
    entry_points={
        'console_scripts': [
            'dst-bytes = distance_scripts.bytes:main',
            'dst-objtobytes = distance_scripts.objtobytes:main',
            'dst-querymaps = distance_scripts.querymaps:main',
            'dst-mklevelinfos = distance_scripts.mklevelinfos:main',
            'dst-teletodot = distance_scripts.teletodot:main',
        ]
    },
)


# vim:set sw=4 ts=8 sts=4 et sr ft=python fdm=marker tw=0:
