from dataclasses import dataclass
from order import Order

ORDER_TIME: float = 90
@dataclass
class Customer:
    name: str
    order: Order
    time_left: float = ORDER_TIME
    stars: int = 0
    finished: bool = False
    x: float = 1300
    y: float = 350