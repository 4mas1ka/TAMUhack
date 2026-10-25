from collections import Counter
from dataclasses import dataclass

from order import Order


ORDER_TIME = 90
PATIENCE_WARN = 30
PATIENCE_CRITICAL = 15
WALK_IN_SPEED = 220
WALK_OUT_SPEED = 250
OFFSCREEN_MARGIN = 100


def format_counts(items, keep_order=False):
    if isinstance(items, dict):
        counts = items
    else:
        counts = Counter(items or [])

    pairs = counts.items()
    if not keep_order:
        pairs = sorted(pairs)

    parts = []
    for name, count in pairs:
        if count <= 0:
            continue
        parts.append(f"{name} x{count}" if count > 1 else name)

    return ", ".join(parts)


@dataclass
class Customer:
    name: str
    order: Order

    time_left: float = ORDER_TIME
    total_time: float = ORDER_TIME

    stars: int = 0

    state: str = "ENTERING"

    x: float = 1300
    y: float = 390
    target_x: float = 600

    order_taken: bool = False

    # Controls which character PNG is displayed.
    # neutral = normal face
    # happy = correct order
    # sad = incorrect order / timeout
    reaction: str = "neutral"

    @property
    def is_active(self):
        return self.state != "GONE"

    @property
    def is_waiting_to_order(self):
        return self.state == "WAITING_TO_ORDER"

    @property
    def is_waiting_for_food(self):
        return self.state == "WAITING_FOR_FOOD"

    @property
    def has_timed_out(self):
        return (
            self.order_taken
            and self.is_waiting_for_food
            and self.time_left <= 0
        )

    @property
    def time_used(self):
        return max(
            0.0,
            self.total_time - self.time_left
        )

    @property
    def timer_fraction(self):
        if self.total_time <= 0:
            return 0.0

        return max(
            0.0,
            min(
                1.0,
                self.time_left / self.total_time
            )
        )

    @property
    def patience_level(self):
        if self.time_left > PATIENCE_WARN:
            return "good"

        if self.time_left > PATIENCE_CRITICAL:
            return "warning"

        return "critical"

    def start_order_timer(self):
        self.order_taken = True
        self.time_left = self.total_time
        self.state = "WAITING_FOR_FOOD"

    def update_timer(self, delta_time):
        if (
            not self.order_taken
            or not self.is_waiting_for_food
        ):
            return

        self.time_left = max(
            0.0,
            self.time_left - delta_time
        )

    def walk_to_counter(self, delta_time):
        if self.state != "ENTERING":
            return

        self.x -= WALK_IN_SPEED * delta_time

        if self.x <= self.target_x:
            self.x = self.target_x
            self.state = "WAITING_TO_ORDER"

    def leave_shop(self, delta_time):
        if self.state != "LEAVING":
            return

        self.x += WALK_OUT_SPEED * delta_time

        if self.x > 1200 + OFFSCREEN_MARGIN:
            self.state = "GONE"