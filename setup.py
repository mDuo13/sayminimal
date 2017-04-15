"""setuptools based setup module"""

from setuptools import setup

# Convert the markdown readme to ReST using Pandoc
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except ImportError:
    long_description = open('README.md').read()


setup(
    name='sayminimal',
    version="3.0.0a1",
    description='A minimalist write-only Twitter/Mastodon client.',
    long_description=long_description,
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications',
    ],
    keywords='twitter mastodon social microblogging',
    packages=[
        'sayminimal',
    ],
    entry_points={
        'console_scripts': [
            'sayminimal = sayminimal.tweet:main',
        ],
    },
    install_requires=[
        'PyYAML',
        'tweepy',
    ],
    package_data={
        '': ["fusion.glade"],
    }
)
