import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xspfgen",
    packages=setuptools.find_packages(),
    author="Adam Bukolt",
    author_email="abukolt@gmx.com",
    description="Package to create an XSPF playlist (Vlc compatible)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'xspfgen=xspf.handler:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
