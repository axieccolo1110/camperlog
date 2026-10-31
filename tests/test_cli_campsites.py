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


# --- stops tied to a campsite -------------------------------------------------

import datetime as dt  # noqa: E402


def _days(offset: int) -> str:
    return (dt.date.today() + dt.timedelta(days=offset)).isoformat()


@pytest.fixture
def trip_and_campsite(runner, test_db):
    runner.invoke(cli, ["trip", "add", "--start", _days(-30), "--end", _days(30)])
    runner.invoke(cli, ADD)
    return "1", "1"


def test_stop_add_with_a_campsite_takes_over_its_place(runner, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite

    result = runner.invoke(
        cli,
        [
            "trip",
            "stop",
            "add",
            trip_id,
            "--date",
            _days(-5),
            "--campsite",
            campsite_id,
        ],
    )

    assert result.exit_code == 0
    assert "Wiese am See" in result.output
    shown = runner.invoke(cli, ["trip", "show", trip_id]).output
    assert "Wiese am See" in shown
    assert "46.668, 11.159" in shown
    assert "Stellplatz 1" in shown


def test_campsite_and_own_place_exclude_each_other(runner, trip_and_campsite):
    trip_id, campsite_id = trip_and_campsite

    result = runner.invoke(
        cli,
        ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite",
         campsite_id, "--place", "Verona"],
    )  # fmt: skip

    assert result.exit_code != 0
    assert "übernimmt dessen Ort" in result.output


def test_stop_add_with_unknown_campsite(runner, trip_and_campsite):
    trip_id, _ = trip_and_campsite

    result = runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite", "99"]
    )

    assert result.exit_code != 0
    assert "Stellplatz 99" in result.output


def test_status_in_the_list_follows_the_stops(runner, trip_and_campsite):
    """Bookmarked, then used as a stop: visited once the day has come."""
    trip_id, campsite_id = trip_and_campsite
    assert "vorgemerkt" in runner.invoke(cli, ["campsite", "list"]).output

    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(10), "--campsite", "1"]
    )
    assert "vorgemerkt" in runner.invoke(cli, ["campsite", "list"]).output  # future

    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite", "1"]
    )
    listing = runner.invoke(cli, ["campsite", "list"]).output
    assert "besucht" in listing and "vorgemerkt" not in listing


def test_stop_edit_ties_a_stop_to_a_campsite(runner, trip_and_campsite):
    trip_id, _ = trip_and_campsite
    runner.invoke(
        cli,
        ["trip", "stop", "add", trip_id, "--date", _days(-5), "--place", "Verona",
         "--lat", "45.4", "--lon", "10.9"],
    )  # fmt: skip

    result = runner.invoke(cli, ["trip", "stop", "edit", "1", "--campsite", "1"])

    assert result.exit_code == 0
    shown = runner.invoke(cli, ["trip", "show", trip_id]).output
    assert "Wiese am See" in shown and "Verona" not in shown


def test_stop_edit_keeps_the_campsite_when_only_the_date_changes(
    runner, trip_and_campsite
):
    trip_id, _ = trip_and_campsite
    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite", "1"]
    )

    result = runner.invoke(cli, ["trip", "stop", "edit", "1", "--date", _days(-4)])

    assert result.exit_code == 0
    assert "Wiese am See" in runner.invoke(cli, ["trip", "show", trip_id]).output


def test_stop_edit_refuses_an_own_place_while_tied_to_a_campsite(
    runner, trip_and_campsite
):
    trip_id, _ = trip_and_campsite
    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite", "1"]
    )

    result = runner.invoke(cli, ["trip", "stop", "edit", "1", "--place", "Verona"])

    assert result.exit_code != 0
    assert "--clear-campsite" in result.output


def test_stop_edit_clear_campsite_gives_an_own_place(runner, trip_and_campsite):
    trip_id, _ = trip_and_campsite
    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--campsite", "1"]
    )

    result = runner.invoke(
        cli, ["trip", "stop", "edit", "1", "--clear-campsite", "--place", "Verona"]
    )

    assert result.exit_code == 0
    shown = runner.invoke(cli, ["trip", "show", trip_id]).output
    assert "Verona" in shown and "Wiese am See" not in shown


@pytest.mark.parametrize(
    "args",
    [
        ["--campsite", "1", "--clear-campsite"],
        ["--campsite", "1", "--place", "X"],
        ["--campsite", "1", "--lat", "1"],
        ["--campsite", "1", "--clear-coordinates"],
    ],
)
def test_stop_edit_rejects_contradicting_options(runner, trip_and_campsite, args):
    trip_id, _ = trip_and_campsite
    runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", _days(-5), "--place", "V"]
    )

    assert runner.invoke(cli, ["trip", "stop", "edit", "1", *args]).exit_code != 0
