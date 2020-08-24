import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name='ocrlayout',  
    version='0.8',
    author="Nicolas Uthurriague",
    author_email="puthurr@hotmail.com",
    description="A Helper class to get more meaninful text out of common OCR outputs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://puthurr.github.io/",
    project_urls={
    'Documentation': 'https://puthurr.github.io/',
    'Source': 'https://github.com/puthurr/ocrlayout/',
    'Tracker': 'https://github.com/puthurr/ocrlayout/issues',
    },
    license='MIT',
    packages=setuptools.find_packages(),
    package_data={'ocrlayout': ['config/*.*']},
    classifiers=[
    "Programming Language :: Python :: 3.7",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    ],
    keywords='OCR, Computer Vision, Text Extraction, Knowledge Mining, BoundingBoxes',
    python_requires='>=3.7',
    install_requires=['numpy']
 )