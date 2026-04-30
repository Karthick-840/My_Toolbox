from my_toolbox.log_tools import Logger


def test_logger_creates_file_and_sets_level(tmp_path):
    log_file = tmp_path / "app.log"
    logger_obj = Logger("x", "INFO", filename=str(log_file), filemode="w")
    assert log_file.exists()
    assert logger_obj.logger.name == "x"


def test_logger_without_file_works():
    logger_obj = Logger("y", "DEBUG")
    assert logger_obj.logger.name == "y"
