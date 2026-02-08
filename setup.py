"""Setup configuration for whyis_agentic package."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="whyis_agentic",
    version="0.1.0",
    author="Whyis Knowledge Graph Team",
    description="A Gen AI agentic inference plugin for Whyis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/whyiskg/whyis_agentic",
    packages=find_packages(exclude=["tests*"]),
    package_data={
        'whyis_agentic': ['vocab.ttl'],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rdflib>=6.0.0",
        "flask-pluginengine>=0.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "github": [
            # GitHub Copilot SDK (uses OpenAI package as official client)
            "openai>=1.0.0",
        ],
    },
)
