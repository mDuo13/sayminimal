"""setuptools based setup module"""

from setuptools import setup

long_description = open('README.md').read()


setup(
    name='sayminimal',
    version="4.0.0",
    description='A minimalist write-only Mastodon client.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/mduo13/sayminimal',
    author='mDuo13',
    author_email='mduo13@gmail.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Communications',
    ],
    keywords='mastodon social microblogging',
    packages=[
        'sayminimal',
    ],
    entry_points={
        'console_scripts': [
            'sayminimal = sayminimal.toot:main',
        ],
    },
    install_requires=[
        'PyYAML',
        'Mastodon.py'
    ],
    package_data={
        '': ["v4.glade"],
    }
)
