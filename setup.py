from setuptools import setup, find_packages

# Function to read requirements.txt and return a list of dependencies
def read_requirements(file_path):
    """Reads a requirements file and returns a list of requirements."""
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="My_Toolbox",
    version="1.0.3",  # Update this version as needed
    author="Karthick Jayaraman",
    description="A useful set of tools for productivity",
    url="https://github.com/Karthick-840/My_Toolbox",
    packages=find_packages(),  # Automatically find packages in the Tools directory
    install_requires=read_requirements("requirements.txt"),  # Read requirements from requirements.txt
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Minimum Python version requirement
)
