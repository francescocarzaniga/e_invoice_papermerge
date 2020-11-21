from setuptools import setup, find_packages


with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='e_invoice',
    version="0.1.0",
    packages=find_packages(include=['papermerge.apps.*']),
    include_package_data=True,
    license='Apache 2.0 License',
    url='https://papermerge.com/',
    description=("Papermerge App for e-invoice ingestion"),
    long_description=long_description,
    author='Francesco Carzaniga',
    author_email='francesco.carzaniga@verdeplus.net',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
