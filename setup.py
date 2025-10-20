"""
Setup file for surreality-logging package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="surreality-logging",
    version="0.1.0",
    author="Surreality AI",
    author_email="dev@surreality.ai",
    description="Standardized logging configuration for Surreality AI services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SurrealityAI/surreality-logging",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required
    ],
)
