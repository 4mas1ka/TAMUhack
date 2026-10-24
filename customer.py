from dataclasses import dataclass

from order import Order


ORDER_TIME = 90


@dataclass
class Customer:
    name: str
    order: Order

    time_left: float = ORDER_TIME
    stars: int = 0
    finished: bool = False

    # Customer starts off-screen
    x: float = 1300
    y: float = 360

    # Where the customer will stop
    target_x: float = 600