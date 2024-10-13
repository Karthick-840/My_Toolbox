from setuptools import setup, find_packages

# Function to read requirements.txt and return a list of dependencies
def parse_requirements(filename):
    with open(filename, 'r') as file:
        return file.read().splitlines()

setup(
    name="Office_toolbox",
    version="1.02",
    author="Karthick Jayaraman",
    description="A useful set of tools for office productivity",
    url="https://github.com/Karthick-840/Office_Toolbox",
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),  # Read from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
