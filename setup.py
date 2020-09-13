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


setup(
    version=get_version(),
    install_requires=["delegator.py>=0.1.1", "python-aqi>=0.6.1", "requests>=2.0.0"],
    python_requires=">3.6.0",
    entry_points={"console_scripts": ["awair=awair_command_line.awair:main"]},
    name="awair-command-line",
    url="https://github.com/obradovic/awair-command-line",
    description="Awair command line",
    author="Zo Obradovic",
    author_email="ping@obradovic.com",
    long_description=get_readme_md_contents(),
    long_description_content_type="text/markdown",
    packages=["awair_command_line"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
