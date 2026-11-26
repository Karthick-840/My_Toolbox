import runpy


def test_project_ops_main_executes(monkeypatch, tmp_path):
    class Args:
        repo_name = "demo"
        folder_path = str(tmp_path)
        remote_url = None
        kaggle_dataset = None

    class Parser:
        def __init__(self, *args, **kwargs):
            pass

        def add_argument(self, *args, **kwargs):
            return None

        def parse_args(self):
            return Args()

    class FakeLogger:
        def info(self, _msg):
            return None

        def getChild(self, _name):
            return self

    class FakeLoggerClass:
        def __init__(self, *args, **kwargs):
            self.logger = FakeLogger()

    class FakeGitTools:
        def __init__(self, logger):
            self.logger = logger

        def create_local_repo(self, *args, **kwargs):
            return None

    monkeypatch.setattr("argparse.ArgumentParser", Parser)
    monkeypatch.setattr("my_toolbox.devops.project_ops.Logger", FakeLoggerClass)
    monkeypatch.setattr("my_toolbox.devops.project_ops.GitTools", FakeGitTools)

    runpy.run_module("my_toolbox.devops.project_ops", run_name="__main__")
    assert (tmp_path / "demo").exists()
