import subprocess

def run_tests():
    """Run all pytest test files in the current directory."""
    # Run pytest on all test files
    result = subprocess.run(['pytest'], capture_output=True, text=True)

    # Print the output from pytest
    print(result.stdout)
    print(result.stderr)

if __name__ == "__main__":
    run_tests()

# Try using setup and teardown method to run tests. could be auseful addition
# You can do DocTests. Use Import Doctest

"""
Create a Github Page and release in twine for PyPi
setup.py nopt working
5 Dev Ops for Github actions.
Protect teh main branch

Mark and Parameters - new thing
@pytest.mark.slow -> way to mention a test will take time and is slow.
TODO: @pytest.mark.skip(reason = "This feature is currnetly broken") ofr sunctions in git.
@pytest.mark.xfail(reason="we know we cant divide by zero ") - TODO: which I need to learn.
TODO: combine API toodl in Git and Kaggle
TODO:  @pytest,kark,parameterize (give thigns as area like  ("length, area",[(2,4),(3,9),(5,25)])) esentially giving multiple parameter for the same function.

Best thign is mocking.

when using Mock, use the decorator. like @mock.pathc("source.service.get_user_from_db")
"""