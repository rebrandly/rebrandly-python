import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="rebrandly-official",
    version="0.0.1",
    author="Rebrandly",
    author_email="dev@rebrandly.com",
    description="A Python SDK to wrap Rebrandly's API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rebrandly/rebrandly-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
