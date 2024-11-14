from setuptools import setup, find_packages
import os
import re

def get_version():
    init_path = os.path.join("ez_commit", "__init__.py")
    with open(init_path, "r") as f:
        content = f.read()
    version_match = re.search(r'^__version__ = ["\']([^"\']*)["\']', content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name="ez-commit",
    version=get_version(),
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "gitpython>=3.1.0",
        "click>=8.0.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        'console_scripts': [
            'ez-commit=ez_commit.cli:main',
        ],
    },
    author="Cline",
    author_email="cline@example.com",
    description="A tool to generate commit messages from git diffs using OpenAI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ez-commit",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
