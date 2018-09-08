#!/usr/bin/python


from setuptools import setup, find_packages

import runpy


version = runpy.run_path('distance/_version.py')['__version__']

setup(
    name='distanceutils',
    version=version,
    description='Read and modify .bytes files of the Refract Studios game Distance',
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
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        'construct>=2.9,<3.0',
        'numpy>=1.13.3,<2.0',
        'numpy-quaternion>=2017.10.19',
        'trampoline',
    ],
    keywords='distance game bytes file level map read edit modify',
    packages=find_packages('.', exclude=['tests', 'tests.*']),
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
