import random
from dataclasses import dataclass, field

from ingredients import FLAVORS, TOPPINGS, SIDES


@dataclass
class Order:
    flavor: str
    toppings: set[str] = field(default_factory=set)
    side: str | None = None

    def matches(self, other):
            return (
                self.flavor == other.flavor
                and self.toppings == other.toppings
                and self.side == other.side
            )

def generate_order(difficulty):
    flavor = random.choice(FLAVORS)

    if difficulty == 1:
        number_of_toppings = 2

    elif difficulty == 2:
        number_of_toppings = 3

    else:
        number_of_toppings = 4

    toppings = set(
        random.sample(TOPPINGS, number_of_toppings)
    )

    side = random.choice(SIDES)

    return Order(
        flavor = flavor,
        toppings = toppings,
        side = side
    )