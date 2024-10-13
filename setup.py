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
    py_modules=["Directory_Tools","Git_Tools.py","Kaggle_Tools.py","PDF_Tools.py","API_Tools.py","String_Ops.py","Time_Ops.py"],  # List the module directly
    install_requires=[
        "Flask",
        "geopandas",
        # Add other dependencies from requirements.txt as needed
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)