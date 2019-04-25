import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tootgroup.py",
    version="1.0.0",
    author="Andreas Schreiner",
    author_email="andreas.schreiner@sonnenmulde.at",
    description="Emulate group accounts on Mastodon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oe4dns/tootgroup.py",
    packages=setuptools.find_packages(),
    keywords="mastodon toot group fediverse",
    classifiers=[
        "Environment :: Console",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "Mastodon.py",
        "appdirs",
    ],
    scripts=["tootgroup.py"],
)