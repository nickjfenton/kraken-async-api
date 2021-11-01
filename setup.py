import pathlib

from setuptools import setup

long_description = pathlib.Path("README.md").read_text()

# for options, see https://github.com/pypa/sampleproject/blob/main/setup.py
setup(
    name='kraken-async-api',
    version='0.1.1b1',
    packages=['kraken_async_api'],
    url='https://github.com/nickjfenton/kraken-async-api',
    license='MIT',
    author='nickjfenton',
    author_email='nickjfenton@yahoo.co.uk',
    description='Asynchronous Websockets API for the Kraken Cryptocurrency Exchange',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9"
    ],
    install_requires=[
        "aiohttp",
        "websockets"
    ],
    python_requires=">=3.4.0"
)
