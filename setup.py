from setuptools import setup, find_packages

from basis_poster import __version__

setup(
    name='matrix-sm-poster-basis-poster',
    version=__version__,
    description='The Basis Poster for the matrix-sm-poster.',

    author='polyma3000',

    packages=find_packages(),

    install_requires=[
        'PyYAML',
    ],

    classifiers=[
        'Intended Audience :: Developers',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
