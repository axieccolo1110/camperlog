# CamperLog

Personal tool for logging camper/van trips, refuelings and visited places.

English is the leading language of this repository. The German term in parentheses is what users see in the UI.

## Language

**Trip** (Reise):
A complete journey over a period (start to end date), consisting of an ordered list of stops.
_Avoid_: Drive, ride (when a single leg is meant, see Stop)

**Stop** (Stopp):
A station within a trip with its own date. It can optionally reference a campsite and then takes over its location. A free-standing stop without a campsite reference is allowed (e.g. a spontaneous overnight stay without an entry) and has an optional place name of its own and optional coordinates.
_Avoid_: Station, waypoint, layover

**Campsite** (Stellplatz):
A standalone place, independent of any specific trip, with a name, coordinates, a status (visited/bookmarked), free-text notes, a few fixed flags (e.g. playground available, pets allowed) and an optional external link (e.g. Park4Night). It can be referenced by zero, one or several stops. The status is set manually but becomes "visited" automatically as soon as a past stop references the campsite. Covers both the German _Stellplatz_ (parking spot for campers) and _Campingplatz_ (full campground).
_Avoid_: Campground, pitch, spot (as separate concepts)

**Expense** (Ausgabe):
An amount of money with a date and a category. There are predefined categories (e.g. Fuel, Campsite fee, Ferry/Toll, Repair/Maintenance, Groceries, Leisure, Other); the user can add and rename further ones. Fuel is fixed and can be neither renamed nor deleted. An expense optionally belongs to a trip. If its date falls within a trip's period, that trip is suggested, but the assignment can be changed (e.g. a ferry booked in advance belongs to the trip, an insurance fee debited during the trip does not). A refueling is an expense in the category Fuel with additionally liters, price per liter and odometer reading; the consumption is calculated from these.
_Avoid_: Cost (as an object), FuelEntry (as a standalone concept)

**Refueling** (Tankvorgang):
An expense in the category Fuel (see Expense).
_Avoid_: Fuel entry, fill-up (as a separate object)

**Share link** (Share-Link):
A link through which a single trip or campsite is visible to third parties, read-only. Expenses are never visible through it. The user can deactivate a share link at any time; it does not expire on its own.
_Avoid_: Sharing, invitation (when access for further users is meant; CamperLog has exactly one user)
