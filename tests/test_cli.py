import pytest
from click.testing import CliRunner
from camperlog.cli import cli


@pytest.fixture
def runner():
    """CLI Test Runner."""
    return CliRunner()


TRIP_ARGS = ["trip", "add", "--start", "2026-08-01", "--end", "2026-08-22"]


def test_trip_add_valid(runner, test_db):
    """trip add with a period and a distance."""
    result = runner.invoke(cli, [*TRIP_ARGS, "--km", "600"])

    assert result.exit_code == 0
    assert "Reise gespeichert" in result.output
    assert "2026-08-01" in result.output and "2026-08-22" in result.output


def test_trip_add_without_distance(runner, test_db):
    """The distance is optional."""
    result = runner.invoke(cli, TRIP_ARGS)

    assert result.exit_code == 0
    assert "Reise gespeichert" in result.output


def test_trip_add_invalid_date(runner, test_db):
    """trip add with an invalid date."""
    result = runner.invoke(
        cli, ["trip", "add", "--start", "invalid-date", "--end", "2026-08-22"]
    )

    assert result.exit_code != 0
    assert "Fehler" in result.output or "Format" in result.output


def test_trip_add_rejects_end_before_start(runner, test_db):
    """The end must not lie before the start."""
    result = runner.invoke(
        cli, ["trip", "add", "--start", "2026-08-22", "--end", "2026-08-01"]
    )

    assert result.exit_code != 0
    assert "Enddatum" in result.output
    assert "Keine Reisen" in runner.invoke(cli, ["trip", "list"]).output


def test_trip_add_accepts_a_one_day_trip(runner, test_db):
    result = runner.invoke(
        cli, ["trip", "add", "--start", "2026-08-01", "--end", "2026-08-01"]
    )

    assert result.exit_code == 0


def test_trip_add_accepts_date_without_leading_zeros(runner, test_db):
    """strptime accepts 2026-8-1, so the stored date must not crash on it."""
    result = runner.invoke(
        cli, ["trip", "add", "--start", "2026-8-1", "--end", "2026-8-22"]
    )

    assert result.exit_code == 0
    listing = runner.invoke(cli, ["trip", "list"])
    assert "2026-08-01" in listing.output


def test_trip_list_empty(runner, test_db):
    """trip list when no trips exist."""
    result = runner.invoke(cli, ["trip", "list"])

    assert result.exit_code == 0
    assert "Keine Reisen" in result.output


def test_trip_list_shows_period_stop_count_and_distance(runner, test_db):
    """trip list with data."""
    runner.invoke(cli, [*TRIP_ARGS, "--km", "600"])

    result = runner.invoke(cli, ["trip", "list"])

    assert result.exit_code == 0
    assert "2026-08-01" in result.output
    assert "2026-08-22" in result.output
    assert "600" in result.output
    assert "Stopps" in result.output


def test_fuel_add_valid(runner, test_db):
    """fuel add with valid parameters."""
    result = runner.invoke(
        cli,
        [
            "fuel",
            "add",
            "--liters",
            "50.5",
            "--price-per-liter",
            "1.85",
            "--odometer",
            "45000",
            "--date",
            "2026-08-01",
        ],
    )

    assert result.exit_code == 0
    assert "Tankfüllung gespeichert" in result.output


def test_fuel_add_invalid_date(runner, test_db):
    """fuel add with an invalid date."""
    result = runner.invoke(
        cli,
        [
            "fuel",
            "add",
            "--liters",
            "50.5",
            "--price-per-liter",
            "1.85",
            "--odometer",
            "45000",
            "--date",
            "invalid-date",
        ],
    )

    assert result.exit_code != 0
    assert "Format" in result.output
    assert "Tankfüllung gespeichert" not in result.output


@pytest.mark.parametrize("km", ["0", "-5"])
def test_trip_add_rejects_non_positive_km(runner, test_db, km):
    """trip add rejects km < 1."""
    result = runner.invoke(cli, [*TRIP_ARGS, "--km", km])

    assert result.exit_code != 0
    assert "--km" in result.output
    assert "Reise gespeichert" not in result.output
    assert "Keine Reisen" in runner.invoke(cli, ["trip", "list"]).output


@pytest.mark.parametrize(
    "option, value",
    [
        ("--liters", "0"),
        ("--liters", "-10"),
        ("--price-per-liter", "0"),
        ("--price-per-liter", "-1.5"),
        ("--odometer", "-1"),
    ],
)
def test_fuel_add_rejects_invalid_numbers(runner, test_db, option, value):
    """fuel add rejects non-positive amounts/prices and negative km."""
    args = {
        "--liters": "50.5",
        "--price-per-liter": "1.85",
        "--odometer": "45000",
        "--date": "2026-08-01",
    }
    args[option] = value
    result = runner.invoke(
        cli, ["fuel", "add", *[x for kv in args.items() for x in kv]]
    )

    assert result.exit_code != 0
    assert "Tankfüllung gespeichert" not in result.output


def test_fuel_add_accepts_zero_odometer(runner, test_db):
    """An odometer reading of 0 is valid (brand-new vehicle)."""
    result = runner.invoke(
        cli,
        [
            "fuel",
            "add",
            "--liters",
            "50.5",
            "--price-per-liter",
            "1.85",
            "--odometer",
            "0",
            "--date",
            "2026-08-01",
        ],
    )

    assert result.exit_code == 0


def test_fuel_list_empty(runner, test_db):
    """fuel list when no fuel entries exist."""
    result = runner.invoke(cli, ["fuel", "list"])

    assert result.exit_code == 0
    assert "Keine Tankfüllungen" in result.output


def test_fuel_list_with_data(runner, test_db):
    """fuel list with data."""
    runner.invoke(
        cli,
        [
            "fuel",
            "add",
            "--liters",
            "50.5",
            "--price-per-liter",
            "1.85",
            "--odometer",
            "45000",
            "--date",
            "2026-08-01",
        ],
    )

    result = runner.invoke(cli, ["fuel", "list"])

    assert result.exit_code == 0
    assert "45000" in result.output


def test_fuel_list_consumption_calculation(runner, test_db):
    """L/100km is calculated correctly, also with several entries."""
    for liters, odometer, date in [
        (50.0, 10000, "2026-07-01"),
        (45.0, 10500, "2026-07-15"),
        (48.0, 11000, "2026-07-26"),
    ]:
        runner.invoke(
            cli,
            [
                "fuel",
                "add",
                "--liters",
                str(liters),
                "--price-per-liter",
                "1.80",
                "--odometer",
                str(odometer),
                "--date",
                date,
            ],
        )

    result = runner.invoke(cli, ["fuel", "list"])

    assert result.exit_code == 0
    # newest entry (11000km, 48L since 10500km): 48/500*100 = 9.6
    assert "9.6" in result.output
    # middle entry (10500km, 45L since 10000km): 45/500*100 = 9.0
    assert "9.0" in result.output
    # the oldest entry has no previous odometer reading
    assert "?" not in result.output


# --- stops -------------------------------------------------------------------


@pytest.fixture
def trip_id(runner, test_db):
    runner.invoke(cli, [*TRIP_ARGS, "--km", "2500"])
    return "1"


def test_stop_add_with_place_and_coordinates(runner, trip_id):
    result = runner.invoke(
        cli,
        [
            "trip", "stop", "add", trip_id,
            "--date", "2026-08-10",
            "--place", "Verona",
            "--lat", "45.438",
            "--lon", "10.992",
        ],
    )  # fmt: skip

    assert result.exit_code == 0
    assert "Stopp gespeichert" in result.output
    shown = runner.invoke(cli, ["trip", "show", trip_id])
    assert "Verona" in shown.output
    assert "45.438" in shown.output


def test_stop_add_needs_only_a_date(runner, trip_id):
    result = runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", "2026-08-10"]
    )

    assert result.exit_code == 0


def test_stop_add_outside_the_period_is_rejected(runner, trip_id):
    result = runner.invoke(
        cli, ["trip", "stop", "add", trip_id, "--date", "2026-09-01"]
    )

    assert result.exit_code != 0
    assert "Zeitraum der Reise" in result.output
    assert "Keine Stopps" in runner.invoke(cli, ["trip", "show", trip_id]).output


def test_stop_add_unknown_trip(runner, test_db):
    result = runner.invoke(cli, ["trip", "stop", "add", "42", "--date", "2026-08-10"])

    assert result.exit_code != 0
    assert "42" in result.output


def test_stop_add_needs_both_coordinates(runner, trip_id):
    result = runner.invoke(
        cli,
        ["trip", "stop", "add", trip_id, "--date", "2026-08-10", "--lat", "45.4"],
    )

    assert result.exit_code != 0
    assert "Breite und Länge" in result.output


def test_trip_show_unknown_trip(runner, test_db):
    result = runner.invoke(cli, ["trip", "show", "42"])

    assert result.exit_code != 0


def test_trip_list_counts_the_stops(runner, trip_id):
    runner.invoke(cli, ["trip", "stop", "add", trip_id, "--date", "2026-08-10"])
    runner.invoke(cli, ["trip", "stop", "add", trip_id, "--date", "2026-08-11"])

    result = runner.invoke(cli, ["trip", "list"])

    assert " 2 " in result.output


def test_three_week_trip_with_six_stops_via_the_cli(runner, test_db):
    """The scenario from the issue, recorded with the CLI."""
    runner.invoke(cli, ["trip", "add", "--start", "2026-08-01", "--end", "2026-08-21"])
    days = ["2026-08-01", "2026-08-04", "2026-08-08", "2026-08-12", "2026-08-16"]
    for day in [*days, "2026-08-21"]:
        result = runner.invoke(cli, ["trip", "stop", "add", "1", "--date", day])
        assert result.exit_code == 0

    shown = runner.invoke(cli, ["trip", "show", "1"])

    assert shown.exit_code == 0
    for day in [*days, "2026-08-21"]:
        assert day in shown.output


# --- editing and deleting ----------------------------------------------------


@pytest.fixture
def trip_with_stop(runner, trip_id):
    runner.invoke(
        cli,
        ["trip", "stop", "add", trip_id, "--date", "2026-08-05", "--place", "Verona",
         "--lat", "45.4", "--lon", "10.9"],
    )  # fmt: skip
    return trip_id


def test_trip_edit_changes_only_the_given_fields(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "edit", "1", "--end", "2026-08-30"])

    assert result.exit_code == 0
    shown = runner.invoke(cli, ["trip", "show", "1"])
    assert "2026-08-01" in shown.output and "2026-08-30" in shown.output
    assert "2500 km" in shown.output


def test_trip_edit_distance_and_clear_it(runner, trip_with_stop):
    runner.invoke(cli, ["trip", "edit", "1", "--km", "3000"])
    assert "3000 km" in runner.invoke(cli, ["trip", "show", "1"]).output

    runner.invoke(cli, ["trip", "edit", "1", "--clear-km"])

    assert " km" not in runner.invoke(cli, ["trip", "show", "1"]).output


def test_trip_edit_rejects_a_period_that_excludes_stops(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "edit", "1", "--end", "2026-08-03"])

    assert result.exit_code != 0
    assert "Stopps einschließen" in result.output
    assert "2026-08-05" in result.output
    assert "2026-08-22" in runner.invoke(cli, ["trip", "show", "1"]).output


def test_trip_edit_needs_something_to_change(runner, trip_id):
    result = runner.invoke(cli, ["trip", "edit", "1"])

    assert result.exit_code != 0
    assert "Nichts zu ändern" in result.output


def test_trip_edit_km_and_clear_km_exclude_each_other(runner, trip_id):
    result = runner.invoke(cli, ["trip", "edit", "1", "--km", "5", "--clear-km"])

    assert result.exit_code != 0


def test_trip_edit_unknown_trip(runner, test_db):
    result = runner.invoke(cli, ["trip", "edit", "42", "--km", "5"])

    assert result.exit_code != 0
    assert "42" in result.output


def test_trip_delete_with_yes_removes_trip_and_stops(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "delete", "1", "--yes"])

    assert result.exit_code == 0
    assert "gelöscht" in result.output
    assert "Keine Reisen" in runner.invoke(cli, ["trip", "list"]).output


def test_trip_delete_asks_and_deletes_on_yes(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "delete", "1"], input="y\n")

    assert result.exit_code == 0
    assert "1 Stopp wirklich löschen" in result.output
    assert "Keine Reisen" in runner.invoke(cli, ["trip", "list"]).output


@pytest.mark.parametrize("answer", ["n\n", "\n"])
def test_trip_delete_keeps_everything_unless_confirmed(runner, trip_with_stop, answer):
    result = runner.invoke(cli, ["trip", "delete", "1"], input=answer)

    assert result.exit_code != 0
    assert "Nichts wurde gelöscht" in result.output
    assert "Verona" in runner.invoke(cli, ["trip", "show", "1"]).output


def test_trip_delete_unknown_trip(runner, test_db):
    assert runner.invoke(cli, ["trip", "delete", "42", "--yes"]).exit_code != 0


def test_trip_show_lists_stop_numbers(runner, trip_with_stop):
    shown = runner.invoke(cli, ["trip", "show", "1"])

    assert "Nr." in shown.output


def test_stop_edit_changes_only_the_given_fields(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "stop", "edit", "1", "--place", "Rimini"])

    assert result.exit_code == 0
    shown = runner.invoke(cli, ["trip", "show", "1"])
    assert "Rimini" in shown.output
    assert "2026-08-05" in shown.output
    assert "45.4" in shown.output


def test_stop_edit_date_and_one_coordinate(runner, trip_with_stop):
    result = runner.invoke(
        cli, ["trip", "stop", "edit", "1", "--date", "2026-08-07", "--lat", "46.0"]
    )

    assert result.exit_code == 0
    shown = runner.invoke(cli, ["trip", "show", "1"]).output
    assert "2026-08-07" in shown and "46.0, 10.9" in shown


def test_stop_edit_removes_place_and_coordinates(runner, trip_with_stop):
    runner.invoke(
        cli, ["trip", "stop", "edit", "1", "--place", "", "--clear-coordinates"]
    )

    shown = runner.invoke(cli, ["trip", "show", "1"]).output
    assert "Verona" not in shown and "45.4" not in shown


def test_stop_edit_rejects_a_date_outside_the_trip(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "stop", "edit", "1", "--date", "2026-09-30"])

    assert result.exit_code != 0
    assert "Zeitraum der Reise" in result.output


def test_stop_edit_needs_something_to_change(runner, trip_with_stop):
    assert runner.invoke(cli, ["trip", "stop", "edit", "1"]).exit_code != 0


def test_stop_edit_unknown_stop(runner, test_db):
    assert (
        runner.invoke(cli, ["trip", "stop", "edit", "42", "--place", "x"]).exit_code
        != 0
    )


def test_stop_delete_asks_first(runner, trip_with_stop):
    declined = runner.invoke(cli, ["trip", "stop", "delete", "1"], input="n\n")
    assert declined.exit_code != 0
    assert "Verona" in runner.invoke(cli, ["trip", "show", "1"]).output

    confirmed = runner.invoke(cli, ["trip", "stop", "delete", "1"], input="y\n")

    assert confirmed.exit_code == 0
    assert "Keine Stopps" in runner.invoke(cli, ["trip", "show", "1"]).output


def test_stop_delete_with_yes(runner, trip_with_stop):
    result = runner.invoke(cli, ["trip", "stop", "delete", "1", "--yes"])

    assert result.exit_code == 0
    assert "Keine Stopps" in runner.invoke(cli, ["trip", "show", "1"]).output


def test_stop_delete_unknown_stop(runner, test_db):
    assert runner.invoke(cli, ["trip", "stop", "delete", "42", "--yes"]).exit_code != 0
