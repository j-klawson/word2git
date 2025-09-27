from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="word2git",
    version="0.1.0",
    author="Keith Lawson",
    author_email="",
    description="Word-first document workflows with Git integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pypandoc>=1.11",
        "jinja2>=3.1.0",
        "pyyaml>=6.0",
        "lxml>=4.9.0",
        "click>=8.0.0",
        "pathlib>=1.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
        ]
    },
    entry_points={
        "console_scripts": [
            "word2git=word2git.cli:main",
        ],
    },
)