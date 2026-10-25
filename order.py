import random
from collections import Counter
from dataclasses import dataclass, field

from ingredients import FLAVORS, TOPPINGS, VESSELS, SIDES


@dataclass
class Order:
    # Counters let one order contain repeated flavors/toppings.
    flavors: Counter = field(default_factory=Counter)
    toppings: Counter = field(default_factory=Counter)
    vessel: str | None = None
    side: str | None = None

    def matches(self, other):
        return (
            self.flavors == other.flavors
            and self.toppings == other.toppings
            and self.vessel == other.vessel
            and self.side == other.side
        )

    def total_scoops(self):
        return sum(self.flavors.values())


def _random_counter(options, total):
    return Counter(random.choices(options, k=total))


def generate_order(difficulty):
    if difficulty == 1:
        flavors = _random_counter(FLAVORS, 1)
        toppings = _random_counter(TOPPINGS, 1)
        vessel = "Cup"
        side = None

    elif difficulty == 2:
        flavors = _random_counter(FLAVORS, random.choice([1, 2]))
        toppings = _random_counter(TOPPINGS, 2)
        vessel = random.choice(VESSELS)
        side = random.choice(SIDES)

    else:
        # Hard mode can intentionally request duplicates.
        flavors = _random_counter(FLAVORS, 2)
        toppings = _random_counter(TOPPINGS, 3)
        vessel = random.choice(VESSELS)
        side = random.choice(SIDES)

    return Order(
        flavors=flavors,
        toppings=toppings,
        vessel=vessel,
        side=side,
    )
