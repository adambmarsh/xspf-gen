import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

requirements = [
    'attrs==22.2.0',
    'beautifulsoup4==4.12.2',
    'check-wheel-contents==0.4.0',
    'click==8.1.3',
    'dbus-next==0.2.3',
    'dbus-python==1.3.2',
    'dbusnotify==0.0.2',
    'dbus-notifier=0.1.1',
    'idna==3.4',
    'lxml==4.9.2',
    'packaging==23.1',
    'pydantic==1.10.8',
    'python-dotenv==1.0.0',
    'sniffio==1.3.0',
    'soupsieve==2.4',
    'tomli==2.0.1',
    'typing_extensions==4.6.3',
    'wheel-filename==1.4.1'
]

setuptools.setup(
    name="xspfgen",
    packages=setuptools.find_packages(),
    version="0.2.0",
    author="Adam Bukolt",
    author_email="abukolt@gmx.com",
    description="Package to create an XSPF playlist (Vlc compatible)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requirements,
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
