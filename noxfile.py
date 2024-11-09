import nox

# Define the Python versions to test
python_versions = [ "3.11"]

@nox.session(python=python_versions)
def tests(session):
    """Run the test suite using pytest."""
    session.install('pytest')  # Install pytest
    session.install('pytest-cov')  # Optional: for coverage reports
    session.install('-r', 'requirements.txt')  # Install your dependencies
    session.run('pytest', '--tb=short', '-q', '--cov=src1', '--cov=src2', '--cov-report=xml:coverage.xml', '--cov-report=term')

@nox.session
def lint(session):
    """Run pylint on the source code and tests."""
    session.install("pylint")
    
    # Run pylint on the source and test directories
    session.run("pylint", "my_toolbox", "tests")

@nox.session
def build(session):
    """Build the package."""
    session.install("build")
    session.run("python", "-m", "build")
