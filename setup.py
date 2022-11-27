from setuptools import setup, find_packages
from pathlib import Path

# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='matrix-sm-poster-basis-poster',
    version='0.1',
    description='The Basis Poster for the matrix-sm-poster.',
    long_description=long_description,
    long_description_content_type='text/markdown',

    author='polyma3000',

    packages=find_packages(),

    install_requires=[
        'PyYAML',
        'apscheduler'
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
