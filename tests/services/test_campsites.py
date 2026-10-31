import pytest

from camperlog.db import session_scope
from camperlog.services.campsites import add_campsite, get_campsite, list_campsites
from camperlog.services.errors import NotFoundError, ValidationError


def test_add_campsite_with_all_fields(session):
    campsite = add_campsite(
        session,
        "Wiese am See",
        46.668,
        11.159,
        "visited",
        "Ruhig, Bäcker um die Ecke",
        playground=True,
        pets_allowed=True,
        external_url="https://park4night.com/place/1",
    )

    assert campsite.id is not None
    assert (campsite.name, campsite.lat, campsite.lon) == (
        "Wiese am See",
        46.668,
        11.159,
    )
    assert campsite.status == "visited"
    assert campsite.notes == "Ruhig, Bäcker um die Ecke"
    assert campsite.playground and campsite.pets_allowed
    assert campsite.external_url == "https://park4night.com/place/1"


def test_defaults_are_bookmarked_without_flags(session):
    campsite = add_campsite(session, "Neu", 45.0, 10.0)

    assert campsite.status == "bookmarked"
    assert (campsite.notes, campsite.external_url) == (None, None)
    assert (campsite.playground, campsite.pets_allowed) == (False, False)


def test_campsite_exists_without_any_trip(session):
    add_campsite(session, "Einzelgänger", 45.0, 10.0)

    with session_scope() as other:
        assert [c.name for c in list_campsites(other)] == ["Einzelgänger"]


def test_name_is_trimmed_and_required(session):
    assert add_campsite(session, "  Seeblick  ", 45.0, 10.0).name == "Seeblick"
    with pytest.raises(ValidationError, match="Name"):
        add_campsite(session, "   ", 45.0, 10.0)


@pytest.mark.parametrize(
    "lat, lon, message",
    [(91, 10, "Breite"), (-91, 10, "Breite"), (45, 181, "Länge"), (45, -181, "Länge")],
)
def test_coordinates_must_be_valid(session, lat, lon, message):
    with pytest.raises(ValidationError, match=message):
        add_campsite(session, "X", lat, lon)
    assert list_campsites(session) == []


def test_coordinate_extremes_are_allowed(session):
    assert add_campsite(session, "Pol", 90, 180).lat == 90
    assert add_campsite(session, "Pol2", -90, -180).lon == -180


def test_status_must_be_known(session):
    with pytest.raises(ValidationError, match="Status"):
        add_campsite(session, "X", 45.0, 10.0, "planned")


@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "ftp://example.com", "park4night.com", "data:text/html,x"],
)
def test_only_http_links_are_accepted(session, url):
    with pytest.raises(ValidationError, match="http"):
        add_campsite(session, "X", 45.0, 10.0, external_url=url)


def test_link_with_spaces_is_rejected(session):
    with pytest.raises(ValidationError, match="Link"):
        add_campsite(session, "X", 45.0, 10.0, external_url="https://a.b/ c")


def test_blank_link_and_notes_become_none(session):
    campsite = add_campsite(session, "X", 45.0, 10.0, notes="  ", external_url="  ")

    assert (campsite.notes, campsite.external_url) == (None, None)


def test_http_and_uppercase_scheme_are_fine(session):
    assert add_campsite(session, "A", 45.0, 10.0, external_url="http://a.b").id
    assert add_campsite(session, "B", 45.0, 10.0, external_url="HTTPS://a.b").id


def test_list_is_sorted_by_name_ignoring_case(session):
    for name in ["bergblick", "Almwiese", "Zeltplatz"]:
        add_campsite(session, name, 45.0, 10.0)

    assert [c.name for c in list_campsites(session)] == [
        "Almwiese",
        "bergblick",
        "Zeltplatz",
    ]


def test_same_name_twice_is_allowed(session):
    add_campsite(session, "Am See", 45.0, 10.0)
    add_campsite(session, "Am See", 47.0, 11.0)

    assert len(list_campsites(session)) == 2


def test_get_campsite(session):
    campsite = add_campsite(session, "X", 45.0, 10.0)

    assert get_campsite(session, campsite.id).name == "X"
    with pytest.raises(NotFoundError, match="999"):
        get_campsite(session, 999)


# --- effective status ---------------------------------------------------------

import datetime as dt  # noqa: E402

from camperlog.services.campsites import effective_statuses  # noqa: E402
from camperlog.services.trips import add_stop, add_trip  # noqa: E402

TODAY = dt.date(2026, 10, 31)


def _stop_on(session, campsite, day, trip_start=dt.date(2026, 1, 1)):
    trip = add_trip(session, trip_start, dt.date(2026, 12, 31))
    return add_stop(session, trip.id, day, campsite_id=campsite.id)


def test_bookmarked_without_stops_stays_bookmarked(session):
    campsite = add_campsite(session, "Neu", 45.0, 10.0)

    assert effective_statuses(session, TODAY) == {campsite.id: "bookmarked"}


def test_manual_visited_stays_visited_without_stops(session):
    campsite = add_campsite(session, "Alt", 45.0, 10.0, "visited")

    assert effective_statuses(session, TODAY) == {campsite.id: "visited"}


def test_a_past_stop_makes_the_campsite_visited(session):
    """The scenario: bookmarked in February, used as a stop in August, then visited."""
    campsite = add_campsite(session, "Wiese", 45.0, 10.0)  # bookmarked in February
    assert effective_statuses(session, dt.date(2026, 2, 15))[campsite.id] == (
        "bookmarked"
    )

    _stop_on(session, campsite, dt.date(2026, 8, 10))  # planned as a stop in August

    assert effective_statuses(session, dt.date(2026, 6, 1))[campsite.id] == "bookmarked"
    assert effective_statuses(session, dt.date(2026, 8, 11))[campsite.id] == "visited"
    assert effective_statuses(session, dt.date(2026, 12, 1))[campsite.id] == "visited"


def test_a_stop_in_the_future_changes_nothing(session):
    campsite = add_campsite(session, "Wiese", 45.0, 10.0)
    _stop_on(session, campsite, dt.date(2026, 11, 1))

    assert effective_statuses(session, TODAY)[campsite.id] == "bookmarked"


def test_a_stop_today_counts_as_visited(session):
    campsite = add_campsite(session, "Wiese", 45.0, 10.0)
    _stop_on(session, campsite, TODAY)

    assert effective_statuses(session, TODAY)[campsite.id] == "visited"
    assert effective_statuses(session, TODAY - dt.timedelta(days=1))[campsite.id] == (
        "bookmarked"
    )


def test_only_the_referenced_campsite_changes(session):
    visited = add_campsite(session, "Besucht", 45.0, 10.0)
    other = add_campsite(session, "Anderer", 46.0, 11.0)
    _stop_on(session, visited, dt.date(2026, 8, 10))

    statuses = effective_statuses(session, TODAY)

    assert statuses == {visited.id: "visited", other.id: "bookmarked"}


def test_several_stops_on_one_campsite_are_fine(session):
    campsite = add_campsite(session, "Lieblingsplatz", 45.0, 10.0)
    _stop_on(session, campsite, dt.date(2026, 5, 1))
    _stop_on(session, campsite, dt.date(2026, 8, 1))

    assert effective_statuses(session, TODAY) == {campsite.id: "visited"}


def test_the_status_is_computed_not_stored(session):
    """Deleting the only past stop makes the campsite bookmarked again."""
    from camperlog.services.trips import delete_stop

    campsite = add_campsite(session, "Wiese", 45.0, 10.0)
    stop = _stop_on(session, campsite, dt.date(2026, 8, 10))
    assert effective_statuses(session, TODAY)[campsite.id] == "visited"

    delete_stop(session, stop.id)

    assert effective_statuses(session, TODAY)[campsite.id] == "bookmarked"
    assert get_campsite(session, campsite.id).status == "bookmarked"


def test_default_today_is_the_real_today(session):
    campsite = add_campsite(session, "Wiese", 45.0, 10.0)
    _stop_on(session, campsite, dt.date.today())

    assert effective_statuses(session)[campsite.id] == "visited"
