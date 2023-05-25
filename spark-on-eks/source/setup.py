# // Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# // SPDX-License-Identifier: MIT-0
import setuptools

try:
    with open("../README.md") as fp:
        long_description = fp.read()
except IOError as e:
    long_description = ''

setuptools.setup(
    name="sql-based-etl",
    version="2.0.0",

    description="A CDK v2 Python app for SQL-based ETL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    author="meloyang",

    package_dir={"": "./"},
    packages=setuptools.find_packages(where="./"),

    install_requires=[
        "constructs>=10.0.0,<11.0.0",
        "aws-cdk-lib==2.67.0",
        "aws-cdk.lambda-layer-kubectl-v24==2.0.118",
        "pyyaml==5.4",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: MIT License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
