from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pyLasec",
    version="0.0.1",
    author="Josué Morais",
    description="Library with resources used by the Control and Automation Engineering course at the Federal University of Uberlândia",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["pyLasec"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[],
    dependency_links=['https://github.com/josuemoraisgh/pyLasec']
)
