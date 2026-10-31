import pytest
from click.testing import CliRunner
from camperlog.cli import cli


@pytest.fixture
def runner():
    """CLI Test Runner."""
    return CliRunner()


def test_trip_add_valid(runner, test_db):
    """trip add with valid parameters."""
    result = runner.invoke(
        cli,
        [
            "trip",
            "add",
            "--from",
            "München",
            "--to",
            "Berlin",
            "--km",
            "600",
            "--date",
            "2026-08-01",
        ],
    )

    assert result.exit_code == 0
    assert "Reise gespeichert" in result.output


def test_trip_add_invalid_date(runner, test_db):
    """trip add with an invalid date."""
    result = runner.invoke(
        cli,
        [
            "trip",
            "add",
            "--from",
            "München",
            "--to",
            "Berlin",
            "--km",
            "600",
            "--date",
            "invalid-date",
        ],
    )

    assert result.exit_code != 0
    assert "Fehler" in result.output or "Format" in result.output


def test_trip_list_empty(runner, test_db):
    """trip list when no trips exist."""
    result = runner.invoke(cli, ["trip", "list"])

    assert result.exit_code == 0
    assert "Keine Reisen" in result.output


def test_trip_list_with_data(runner, test_db):
    """trip list with data."""
    runner.invoke(
        cli,
        [
            "trip",
            "add",
            "--from",
            "München",
            "--to",
            "Berlin",
            "--km",
            "600",
            "--date",
            "2026-08-01",
        ],
    )

    result = runner.invoke(cli, ["trip", "list"])

    assert result.exit_code == 0
    assert "München" in result.output
    assert "Berlin" in result.output


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
    result = runner.invoke(
        cli,
        [
            "trip",
            "add",
            "--from",
            "München",
            "--to",
            "Berlin",
            "--km",
            km,
            "--date",
            "2026-08-01",
        ],
    )

    assert result.exit_code != 0
    assert "Reise gespeichert" not in result.output


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
    # neuester Eintrag (11000km, 48L seit 10500km): 48/500*100 = 9.6
    assert "9.6" in result.output
    # mittlerer Eintrag (10500km, 45L seit 10000km): 45/500*100 = 9.0
    assert "9.0" in result.output
    # aeltester Eintrag hat keinen Vorgaenger-km-Stand
    assert "?" not in result.output
