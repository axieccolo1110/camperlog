# A refueling becomes an expense in the category Fuel instead of an object of its own

With the realignment a trip should show its total costs ("what did this journey really cost"), and besides fuel there are further categories such as campsite fee, repair and groceries. Instead of keeping `FuelEntry` next to a new expense, a refueling becomes an expense in the category Fuel with the additional data liters, price per liter and odometer reading. That leaves exactly one summing logic; the consumption (L/100km) is still calculated from the expenses of the category Fuel. Existing fuel entries are migrated into expenses.

## Considered Options

- Keep `FuelEntry` and expense separate — rejected, because every cost sum (trip, period) would have to add two sources and the logic for that would be duplicated in several places.
