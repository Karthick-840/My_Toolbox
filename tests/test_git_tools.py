
from my_toolbox.git_tools import GitTools


def test_create_local_repo_runs_git(monkeypatch, tmp_path, dummy_logger):
    g = GitTools(dummy_logger)
    calls = []

    def fake_run(cmd):
        calls.append(cmd)

    monkeypatch.setattr("my_toolbox.git_tools.subprocess.run", fake_run)
    g.create_local_repo("repo1", folder_path=str(tmp_path), remote_url="https://x")

    repo_path = tmp_path / "repo1"
    assert repo_path.exists()
    assert ["git", "init"] in calls
    assert ["git", "remote", "add", "origin", "https://x"] in calls
    assert ["git", "pull", "origin", "main"] in calls


def test_create_requirements_invokes_pipreqs(monkeypatch, tmp_path, dummy_logger):
    g = GitTools(dummy_logger)
    calls = []

    def fake_check_call(cmd):
        calls.append(cmd)

    monkeypatch.setattr("my_toolbox.git_tools.subprocess.check_call", fake_check_call)
    g.create_requirements(str(tmp_path))
    assert calls
    assert "--force" in calls[0]


def test_create_repos_from_file_noop_when_file_exists(tmp_path, dummy_logger):
    g = GitTools(dummy_logger)
    repos = tmp_path / "repos.txt"
    repos.write_text("a,https://x\n", encoding="utf-8")
    # Current implementation only enters branch when file does NOT exist.
    # This test documents existing behavior.
    g.create_repos_from_file(str(repos))
    assert repos.exists()
