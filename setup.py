""" Wheel Config
"""
from setuptools import setup


def get_readme_md_contents():
    """ Reads the contents of README file
    """
    return get_file("README.md")


def get_version():
    """ Returns the contents of the VERSION file
    """
    return get_file("VERSION")


def get_file(filename: str) -> str:
    """ Returns the contents of the passed-in filename
    """
    with open(filename, encoding="utf-8") as f:
        return f.read()

NAME = "awair-command-line"
PACKAGE = NAME.replace("-", "_")


setup(
    install_requires=["delegator.py>=0.1.1",
                      "datadog>=0.25.0",
                      "python-aqi>=0.6.1",
                      "requests>=2.0.0"],
    python_requires=">3.6.0",
    description="Awair command line. Displays data from all Awair devices on your network. Also shows corresponding Purple Air AQI",  # noqa  # pylint: disable=line-too-long
    entry_points={"console_scripts": [f"awair={PACKAGE}.awair:main"]},
    name=NAME,
    packages=[PACKAGE],
    url=f"https://github.com/obradovic/{NAME}",
    author="Zo Obradovic",
    author_email="ping@obradovic.com",
    version=get_version(),
    long_description=get_readme_md_contents(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
