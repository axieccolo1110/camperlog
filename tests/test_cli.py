import pytest
from click.testing import CliRunner
from camperlog.cli import cli


@pytest.fixture
def runner():
    """CLI Test Runner."""
    return CliRunner()


def test_trip_add_valid(runner, test_db):
    """Test: trip-add mit gültigen Parametern."""
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
    """Test: trip-add mit ungültigem Datum."""
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
    """Test: trip-list wenn keine Reisen existieren."""
    result = runner.invoke(cli, ["trip", "list"])

    assert result.exit_code == 0
    assert "Keine Reisen" in result.output


def test_trip_list_with_data(runner, test_db):
    """Test: trip-list mit Daten."""
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
    """Test: fuel-add mit gültigen Parametern."""
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
    """Test: fuel-add mit ungültigem Datum."""
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

    assert "Fehler" in result.output or "Format" in result.output


def test_fuel_list_empty(runner, test_db):
    """Test: fuel-list wenn keine Tankfüllungen existieren."""
    result = runner.invoke(cli, ["fuel", "list"])

    assert result.exit_code == 0
    assert "Keine Tankfüllungen" in result.output


def test_fuel_list_with_data(runner, test_db):
    """Test: fuel-list mit Daten."""
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
