from typer.testing import CliRunner

from scriba.main import app

runner = CliRunner()


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "scriba" in result.output


def test_help_lists_three_command_groups():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "auth" in result.output
    assert "mail" in result.output
    assert "cal" in result.output
