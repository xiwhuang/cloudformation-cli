from unittest.mock import Mock, patch

import pytest
from jsonschema.exceptions import ValidationError

from rpdk.cli import EXIT_UNHANDLED_EXCEPTION, main
from rpdk.project import Project


@pytest.mark.parametrize(
    "command", ["init", "generate", "package", "validate", "submit"]
)
def test_command_help(capsys, command):
    with patch("rpdk.{0}.{0}".format(command), autospec=True) as mock_func:
        with pytest.raises(SystemExit) as excinfo:
            main(args_in=[command, "--help"])  # has no required params
    assert excinfo.value.code != EXIT_UNHANDLED_EXCEPTION
    out, _ = capsys.readouterr()
    assert "--help" in out
    mock_func.assert_not_called()


@pytest.mark.parametrize("command", ["generate", "package", "validate", "submit"])
def test_command_project_not_found(capsys, command):
    mock_project = Mock(spec=Project)
    mock_project.load_settings.side_effect = FileNotFoundError

    with patch(
        "rpdk.{0}.Project".format(command), autospec=True, return_value=mock_project
    ):
        with pytest.raises(SystemExit) as excinfo:
            main(args_in=[command])

    assert excinfo.value.code != EXIT_UNHANDLED_EXCEPTION
    mock_project.load_settings.assert_called_once_with()
    mock_project.load_schema.assert_not_called()
    try:
        getattr(mock_project, command).assert_not_called()
    except AttributeError:
        pass
    out, err = capsys.readouterr()
    assert not err
    assert "not found" in out
    assert "init" in out


@pytest.mark.parametrize("command", ["generate", "validate"])
def test_command_invalid_schema(capsys, command):
    mock_project = Mock(spec=Project)
    mock_project.load_schema.side_effect = ValidationError("")

    with patch(
        "rpdk.{0}.Project".format(command), autospec=True, return_value=mock_project
    ):
        with pytest.raises(SystemExit):
            main(args_in=[command])
    mock_project.load_settings.assert_called_once_with()
    mock_project.load_schema.assert_called_once_with()
    try:
        getattr(mock_project, command).assert_not_called()
    except AttributeError:
        pass

    out, err = capsys.readouterr()
    assert not err
    assert "invalid" in out


@pytest.mark.parametrize("command", ["package", "submit"])
def test_command_default(command):
    mock_project = Mock(spec=Project)
    with patch(
        "rpdk.{0}.Project".format(command), autospec=True, return_value=mock_project
    ):
        main(args_in=[command])
    try:
        getattr(mock_project, command).assert_called_once()
    except AttributeError:
        pass