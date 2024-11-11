from setuptools import setup, find_packages

setup(
    name="ez-commit",
    version="0.1.0",
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
