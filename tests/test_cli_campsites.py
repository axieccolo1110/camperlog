import pytest
from click.testing import CliRunner

from camperlog.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


ADD = [
    "campsite",
    "add",
    "--name",
    "Wiese am See",
    "--lat",
    "46.668",
    "--lon",
    "11.159",
]


def test_campsite_add_and_list(runner, test_db):
    result = runner.invoke(cli, ADD)

    assert result.exit_code == 0
    assert "Stellplatz gespeichert" in result.output
    listing = runner.invoke(cli, ["campsite", "list"])
    assert "Wiese am See" in listing.output
    assert "46.668, 11.159" in listing.output
    assert "vorgemerkt" in listing.output


def test_campsite_add_with_everything(runner, test_db):
    result = runner.invoke(
        cli,
        [*ADD, "--status", "besucht", "--notes", "Ruhig", "--playground", "--pets",
         "--url", "https://park4night.com/place/1"],
    )  # fmt: skip

    assert result.exit_code == 0
    listing = runner.invoke(cli, ["campsite", "list"]).output
    assert "besucht" in listing
    assert listing.count("✓") == 2


def test_campsite_list_empty(runner, test_db):
    result = runner.invoke(cli, ["campsite", "list"])

    assert result.exit_code == 0
    assert "Keine Stellplätze" in result.output


@pytest.mark.parametrize("missing", ["--name", "--lat", "--lon"])
def test_campsite_add_needs_name_and_coordinates(runner, test_db, missing):
    index = ADD.index(missing)
    args = [a for i, a in enumerate(ADD) if i not in (index, index + 1)]

    result = runner.invoke(cli, args)

    assert result.exit_code != 0
    assert missing in result.output


def test_campsite_add_rejects_invalid_values(runner, test_db):
    assert runner.invoke(cli, [*ADD[:-1], "181"]).exit_code != 0
    assert runner.invoke(cli, [*ADD, "--url", "javascript:alert(1)"]).exit_code != 0
    assert runner.invoke(cli, [*ADD, "--status", "geplant"]).exit_code != 0
    assert "Keine Stellplätze" in runner.invoke(cli, ["campsite", "list"]).output
