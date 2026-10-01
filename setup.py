"""setuptools based setup module"""

from setuptools import setup

long_description = open('README.md').read()


setup(
    name='sayminimal',
    version="4.1.0",
    description='A minimalist write-only Mastodon client.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/mduo13/sayminimal',
    author='mDuo13',
    author_email='mduo13@gmail.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
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
