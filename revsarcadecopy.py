"""Rev's Creamery - Python Arcade edition (built for arcade 3.x).

Install:  pip install arcade
Run:      python revs_creamery_arcade.py

Click ingredients to build the order on your tray, then press SERVE under
the right customer. Timers tick in real time.
"""
import math
import random
from collections import Counter

import arcade

# ---------- Window ----------
WIDTH, HEIGHT = 1100, 720
TITLE = "Rev's Creamery"

# ---------- Game settings (tweak these!) ----------
ORDER_TIME_LIMIT = 90     # seconds before a customer storms out (1.5 min)
FAST_TIME = 60            # finish within this for 3 stars
MAX_CUSTOMERS = 3         # customers in the shop at once
ORDERS_PER_ROUND = 5
ARRIVAL_GAP = 15          # seconds between new customers
WIN_AVERAGE = 2.5         # average stars needed to pass a level
MAX_TRAY_ITEMS = 8

FLAVORS = ["vanilla", "chocolate", "strawberry", "mint", "cookie dough"]
TOPPINGS = ["sprinkles", "caramel drizzle", "cherry", "whipped cream",
            "chocolate chips", "crushed oreos"]
VESSELS = ["cone", "cup"]
NAMES = ["Alex", "Bailey", "Casey", "Dana", "Eli", "Fran", "Gus", "Hana",
         "Ivy", "Jo", "Kai", "Luz", "Milo", "Nia", "Omar", "Pia"]

# Harder levels = more complex recipes
LEVELS = [
    {"name": "Easy",   "scoops": 1, "toppings": 1, "vessel": False},
    {"name": "Medium", "scoops": 1, "toppings": 2, "vessel": True},
    {"name": "Hard",   "scoops": 2, "toppings": 3, "vessel": True},
]

# ---------- Colors ----------
BG = (38, 34, 52)
PANEL = (58, 52, 78)
PANEL_DARK = (46, 41, 62)
WHITE = (255, 255, 255)
GRAY = (150, 148, 165)
GOLD = (255, 205, 60)
GREEN = (90, 200, 110)
ORANGE = (240, 160, 60)
RED = (225, 80, 80)

ITEM_COLORS = {
    "vanilla": (250, 235, 190), "chocolate": (110, 70, 45),
    "strawberry": (250, 160, 185), "mint": (165, 235, 200),
    "cookie dough": (225, 195, 150),
    "sprinkles": (255, 140, 200), "caramel drizzle": (225, 160, 70),
    "cherry": (215, 50, 70), "whipped cream": (250, 250, 250),
    "chocolate chips": (140, 95, 65), "crushed oreos": (120, 120, 135),
    "cone": (220, 180, 110), "cup": (200, 215, 235),
}


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def make_recipe(level):
    recipe = Counter()
    for flavor in random.choices(FLAVORS, k=level["scoops"]):
        recipe[flavor] += 1
    for topping in random.sample(TOPPINGS, level["toppings"]):
        recipe[topping] += 1
    if level["vessel"]:
        recipe[random.choice(VESSELS)] += 1
    return recipe


class Customer:
    def __init__(self, level, now):
        self.name = random.choice(NAMES)
        self.recipe = make_recipe(level)
        self.arrived = now

    def elapsed(self, now):
        return now - self.arrived

    def lines(self):
        scoops = [n for n in FLAVORS for _ in range(self.recipe[n])]
        tops = [n for n in TOPPINGS if self.recipe[n]]
        vessel = [n for n in VESSELS if self.recipe[n]]
        out = [f"{'Scoop' if len(scoops) == 1 else 'Scoops'}: {' + '.join(scoops)}"]
        if vessel:
            out.append(f"Vessel: {vessel[0]}")
        out += [f"Topping: {t}" for t in tops]
        return out


class Button:
    def __init__(self, cx, cy, w, h, label, color, action, font_size=14):
        self.cx, self.cy, self.w, self.h = cx, cy, w, h
        self.color = color
        self.action = action
        self.visible = True
        text_color = (20, 20, 20) if luminance(color) > 140 else WHITE
        self.text = arcade.Text(text=label, x=cx, y=cy, color=text_color,
                                font_size=font_size, anchor_x="center",
                                anchor_y="center", bold=True)

    def hit(self, x, y):
        return abs(x - self.cx) <= self.w / 2 and abs(y - self.cy) <= self.h / 2

    def draw(self, hover):
        fill = tuple(min(255, c + 30) for c in self.color) if hover else self.color
        rect = arcade.XYWH(self.cx, self.cy, self.w, self.h)
        arcade.draw_rect_filled(rect, fill)
        arcade.draw_rect_outline(rect, (25, 22, 35), 2)
        self.text.draw()


class Creamery(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        self.background_color = BG
        self.mouse = (0, 0)
        self._texts = {}              # cache of arcade.Text objects

        self.state = "title"          # title | playing | round_over | trophy
        self.level_idx = 0
        self.clock = 0.0
        self.slots = [None] * MAX_CUSTOMERS
        self.tray = Counter()
        self.ratings = []
        self.spawned = 0
        self.next_spawn = 0.0
        self.toast_text = ""
        self.toast_stars = None
        self.toast_timer = 0.0
        self.avg = 0.0

        self.card_x = [190, 550, 910]
        self.card_y = 500

        self.title_buttons = [
            Button(550, 190, 220, 56, "START", GREEN, self.start_round, 20)]
        self.over_buttons = []
        self.trophy_buttons = []
        self.build_play_buttons()

    # ---------- setup helpers ----------
    def build_play_buttons(self):
        self.ingredient_buttons = []
        rows = [(FLAVORS, 285), (TOPPINGS, 207), (VESSELS, 129)]
        for names, y in rows:
            for i, name in enumerate(names):
                self.ingredient_buttons.append(Button(
                    90 + i * 130, y, 120, 44, name, ITEM_COLORS[name],
                    lambda n=name: self.add_ingredient(n), 13))
        self.clear_button = Button(955, 70, 200, 40, "CLEAR TRAY", RED,
                                   self.clear_tray, 14)
        self.serve_buttons = [
            Button(x, self.card_y - 115, 200, 36, "SERVE", GREEN,
                   lambda s=i: self.serve(s), 14)
            for i, x in enumerate(self.card_x)]

    def text(self, key, s, x, y, size=16, color=WHITE, anchor_x="left",
             anchor_y="baseline", bold=False):
        """Draw text using cached arcade.Text objects (fast)."""
        t = self._texts.get(key)
        if t is None:
            t = arcade.Text(text=s, x=x, y=y, color=color, font_size=size,
                            anchor_x=anchor_x, anchor_y=anchor_y, bold=bold)
            self._texts[key] = t
        else:
            t.text = s
            t.x, t.y = x, y
            t.color = color
        t.draw()

    # ---------- game logic ----------
    def start_round(self):
        self.state = "playing"
        self.clock = 0.0
        self.slots = [None] * MAX_CUSTOMERS
        self.tray = Counter()
        self.ratings = []
        self.spawned = 0
        self.next_spawn = 0.0
        self.toast_timer = 0.0

    def add_ingredient(self, name):
        if self.state != "playing":
            return
        if sum(self.tray.values()) >= MAX_TRAY_ITEMS:
            self.show_toast("Your tray is full!")
            return
        self.tray[name] += 1

    def clear_tray(self):
        self.tray = Counter()

    def show_toast(self, message, stars=None):
        self.toast_text = message
        self.toast_stars = stars
        self.toast_timer = 2.5

    def finish_customer(self, slot, stars, message):
        self.ratings.append(stars)
        self.slots[slot] = None
        self.show_toast(message, stars)

    def serve(self, slot):
        customer = self.slots[slot]
        if self.state != "playing" or customer is None:
            return
        if not self.tray:
            self.show_toast("Your tray is empty!")
            return
        correct = self.tray == customer.recipe
        took = customer.elapsed(self.clock)
        if correct and took <= FAST_TIME:
            stars, mood = 3, "is happy!"
        elif correct:
            stars, mood = 2, "is satisfied."
        else:
            stars, mood = 1, "is unhappy... wrong order!"
        self.tray = Counter()
        self.finish_customer(slot, stars, f"{customer.name} {mood}")

    def end_round(self):
        self.avg = sum(self.ratings) / len(self.ratings)
        passed = self.avg >= WIN_AVERAGE
        last_level = self.level_idx == len(LEVELS) - 1

        if passed and last_level:
            self.state = "trophy"
            self.trophy_buttons = [
                Button(430, 150, 220, 52, "PLAY AGAIN", GREEN, self.restart_all, 16),
                Button(670, 150, 220, 52, "QUIT", RED, self.close, 16)]
            return

        self.state = "round_over"
        self.over_buttons = [Button(0, 150, 220, 52, "TRY AGAIN", ORANGE,
                                    self.start_round, 16)]
        if passed and not last_level:
            self.over_buttons.append(Button(0, 150, 260, 52, "UPGRADE DIFFICULTY",
                                            GREEN, self.upgrade, 16))
        self.over_buttons.append(Button(0, 150, 160, 52, "QUIT", RED, self.close, 16))
        # spread the buttons out evenly
        total = len(self.over_buttons)
        for i, b in enumerate(self.over_buttons):
            b.cx = WIDTH / 2 + (i - (total - 1) / 2) * 290
            b.text.x = b.cx

    def upgrade(self):
        self.level_idx += 1
        self.start_round()

    def restart_all(self):
        self.level_idx = 0
        self.start_round()

    def on_update(self, delta_time):
        if self.state != "playing":
            return
        self.clock += delta_time
        self.toast_timer = max(0.0, self.toast_timer - delta_time)

        # customers who waited too long storm out
        for i, c in enumerate(self.slots):
            if c and c.elapsed(self.clock) > ORDER_TIME_LIMIT:
                self.finish_customer(i, 1, f"{c.name} got tired of waiting and left!")

        # new customer arrives
        empty = [i for i, c in enumerate(self.slots) if c is None]
        shop_empty = len(empty) == MAX_CUSTOMERS
        if (self.spawned < ORDERS_PER_ROUND and empty
                and (self.clock >= self.next_spawn or shop_empty)):
            self.slots[empty[0]] = Customer(LEVELS[self.level_idx], self.clock)
            self.spawned += 1
            self.next_spawn = self.clock + ARRIVAL_GAP

        if len(self.ratings) >= ORDERS_PER_ROUND:
            self.end_round()

    # ---------- input ----------
    def active_buttons(self):
        if self.state == "title":
            return self.title_buttons
        if self.state == "round_over":
            return self.over_buttons
        if self.state == "trophy":
            return self.trophy_buttons
        buttons = list(self.ingredient_buttons) + [self.clear_button]
        buttons += [b for i, b in enumerate(self.serve_buttons) if self.slots[i]]
        return buttons

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse = (x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "playing" and button == arcade.MOUSE_BUTTON_RIGHT:
            self.clear_tray()
            return
        for b in self.active_buttons():
            if b.hit(x, y):
                b.action()
                break

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.ESCAPE:
            self.close()
        elif symbol == arcade.key.C and self.state == "playing":
            self.clear_tray()
        elif symbol in (arcade.key.ENTER, arcade.key.SPACE) and self.state == "title":
            self.start_round()

    # ---------- drawing helpers ----------
    def draw_star(self, cx, cy, r, color):
        points = []
        for i in range(10):
            radius = r if i % 2 == 0 else r * 0.45
            angle = math.radians(90 + i * 36)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        arcade.draw_polygon_filled(points, color)

    def draw_stars(self, cx, cy, count, r=14, spacing=34):
        for i in range(3):
            x = cx + (i - 1) * spacing
            self.draw_star(x, cy, r, GOLD if i < count else (95, 90, 110))

    def draw_face(self, cx, cy, r, elapsed):
        if elapsed <= FAST_TIME:
            mood, color = "happy", (255, 214, 90)
        elif elapsed <= ORDER_TIME_LIMIT - 15:
            mood, color = "neutral", (255, 190, 100)
        else:
            mood, color = "sad", (240, 130, 110)
        arcade.draw_circle_filled(cx, cy, r, color)
        for dx in (-0.35, 0.35):
            arcade.draw_circle_filled(cx + dx * r, cy + 0.25 * r, r * 0.1, (30, 30, 30))
        if mood == "happy":
            pts = [(-0.4, -0.15), (-0.2, -0.4), (0.2, -0.4), (0.4, -0.15)]
        elif mood == "neutral":
            pts = [(-0.35, -0.35), (0.35, -0.35)]
        else:
            pts = [(-0.4, -0.5), (-0.2, -0.3), (0.2, -0.3), (0.4, -0.5)]
        for a, b in zip(pts, pts[1:]):
            arcade.draw_line(cx + a[0] * r, cy + a[1] * r,
                             cx + b[0] * r, cy + b[1] * r, (30, 30, 30), 3)

    def draw_cone(self, cx, cy, scoop_color):
        arcade.draw_triangle_filled(cx - 40, cy, cx + 40, cy, cx, cy - 90, (220, 180, 110))
        arcade.draw_circle_filled(cx, cy + 22, 44, scoop_color)
        arcade.draw_circle_filled(cx, cy + 62, 34, (250, 235, 190))
        arcade.draw_circle_filled(cx, cy + 96, 9, (215, 50, 70))

    # ---------- drawing ----------
    def on_draw(self):
        self.clear()
        if self.state == "title":
            self.draw_title()
        elif self.state == "playing":
            self.draw_playing()
        elif self.state == "round_over":
            self.draw_round_over()
        elif self.state == "trophy":
            self.draw_trophy()
        for b in self.active_buttons():
            b.draw(b.hit(*self.mouse))

    def draw_title(self):
        self.draw_cone(190, 400, (250, 160, 185))
        self.draw_cone(910, 400, (165, 235, 200))
        self.text("t_title", "Rev's Creamery", 550, 560, 56, GOLD, "center", bold=True)
        self.text("t_sub", "Welcome! Serve 5 customers as fast and accurately as you can.",
                  550, 505, 18, WHITE, "center")
        rules = [
            "Click ingredients to build the order on your tray, then press SERVE.",
            "Correct + under 60s = 3 stars   |   Correct but slow = 2 stars",
            "Wrong order or out of time (90s) = 1 star.",
            "Max 3 customers at a time. Beat the level with 2.5+ average to upgrade!",
            "Shortcuts: C or right-click clears your tray, ESC quits.",
        ]
        for i, line in enumerate(rules):
            self.text(f"t_rule{i}", line, 550, 440 - i * 30, 16, GRAY, "center")

    def draw_playing(self):
        # top bar
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, 695, WIDTH, 50), PANEL_DARK)
        self.text("bar_title", "Rev's Creamery", 20, 695, 22, GOLD, anchor_y="center", bold=True)
        self.text("bar_level", f"Level: {LEVELS[self.level_idx]['name']}", 450, 695, 18,
                  WHITE, anchor_y="center")
        self.text("bar_orders", f"Orders done: {len(self.ratings)} / {ORDERS_PER_ROUND}",
                  WIDTH - 20, 695, 18, WHITE, "right", "center")

        # customer cards
        for i, cx in enumerate(self.card_x):
            c = self.slots[i]
            rect = arcade.XYWH(cx, self.card_y, 340, 290)
            arcade.draw_rect_filled(rect, PANEL if c else PANEL_DARK)
            arcade.draw_rect_outline(rect, (25, 22, 35), 3)
            if c is None:
                self.text(f"card{i}_wait", "Waiting for customers...", cx, self.card_y,
                          16, GRAY, "center", "center")
                continue
            elapsed = c.elapsed(self.clock)
            self.draw_face(cx - 120, self.card_y + 100, 30, elapsed)
            self.text(f"card{i}_name", c.name, cx - 75, self.card_y + 100, 24, WHITE,
                      anchor_y="center", bold=True)
            for j, line in enumerate(c.lines()):
                self.text(f"card{i}_l{j}", line, cx - 150, self.card_y + 50 - j * 22, 15, WHITE)

            # timer bar
            frac = max(0.0, 1 - elapsed / ORDER_TIME_LIMIT)
            if elapsed <= FAST_TIME:
                bar_color = GREEN
            elif elapsed <= ORDER_TIME_LIMIT - 15:
                bar_color = ORANGE
            else:
                bar_color = RED
            bar_w = 250
            arcade.draw_rect_filled(arcade.XYWH(cx - 30, self.card_y - 65, bar_w, 14), (30, 28, 42))
            if frac > 0:
                arcade.draw_rect_filled(
                    arcade.LBWH(cx - 30 - bar_w / 2, self.card_y - 72, bar_w * frac, 14),
                    bar_color)
            secs = max(0, math.ceil(ORDER_TIME_LIMIT - elapsed))
            self.text(f"card{i}_time", f"{secs}s", cx + 110, self.card_y - 65, 14, WHITE,
                      anchor_y="center", bold=True)

        # kitchen
        for label, y, key in (("FLAVORS", 318, "k_f"), ("TOPPINGS", 240, "k_t"),
                              ("VESSELS", 162, "k_v")):
            self.text(key, label, 30, y, 14, GRAY, bold=True)

        # tray panel
        arcade.draw_rect_filled(arcade.XYWH(955, 185, 250, 290), PANEL)
        arcade.draw_rect_outline(arcade.XYWH(955, 185, 250, 290), (25, 22, 35), 3)
        self.text("tray_title", "YOUR TRAY", 955, 300, 18, GOLD, "center", bold=True)
        if not self.tray:
            self.text("tray_empty", "(empty)", 955, 215, 15, GRAY, "center")
        for i, (name, count) in enumerate(self.tray.items()):
            y = 268 - i * 21
            arcade.draw_rect_filled(arcade.XYWH(850, y + 5, 14, 14), ITEM_COLORS[name])
            label = f"{name} x{count}" if count > 1 else name
            self.text(f"tray_l{i}", label, 865, y, 14, WHITE)

        self.text("footer", "Build the order, then SERVE the right customer.   "
                  "C / right-click = clear tray", 20, 15, 12, GRAY)

        # toast popup
        if self.toast_timer > 0:
            arcade.draw_rect_filled(arcade.XYWH(550, 360, 620, 90), (20, 18, 30, 235))
            arcade.draw_rect_outline(arcade.XYWH(550, 360, 620, 90), GOLD, 3)
            y = 378 if self.toast_stars is not None else 360
            self.text("toast", self.toast_text, 550, y, 20, WHITE, "center", "center", True)
            if self.toast_stars is not None:
                self.draw_stars(550, 336, self.toast_stars, 14)

    def draw_round_over(self):
        self.text("o_title", "Round Complete!", 550, 620, 44, GOLD, "center", bold=True)
        self.text("o_level", f"Level: {LEVELS[self.level_idx]['name']}", 550, 580, 18,
                  GRAY, "center")
        for i, stars in enumerate(self.ratings):
            self.text(f"o_cust{i}", f"Order {i + 1}", 380, 520 - i * 42, 18, WHITE,
                      anchor_y="center")
            self.draw_stars(620, 520 - i * 42, stars, 13, 32)
        self.text("o_avg", f"Average: {self.avg:.2f} / 3.00", 550, 285, 30, WHITE,
                  "center", bold=True)
        passed = self.avg >= WIN_AVERAGE
        msg = ("Customers loved it!" if passed
               else "Customers weren't thrilled... try again!")
        self.text("o_msg", msg, 550, 235, 20, GREEN if passed else ORANGE, "center")

    def draw_trophy(self):
        self.text("w_title", "YOU WIN THE GOLDEN SCOOP TROPHY!", 550, 640, 36, GOLD,
                  "center", bold=True)
        arcade.draw_circle_outline(468, 430, 30, GOLD, 8)
        arcade.draw_circle_outline(632, 430, 30, GOLD, 8)
        arcade.draw_polygon_filled(
            [(480, 490), (620, 490), (600, 390), (560, 355), (540, 355), (500, 390)], GOLD)
        arcade.draw_rect_filled(arcade.XYWH(550, 340, 24, 34), GOLD)
        arcade.draw_rect_filled(arcade.XYWH(550, 315, 110, 18), GOLD)
        self.draw_star(550, 435, 28, WHITE)
        self.text("w_avg", f"Final average: {self.avg:.2f} / 3.00", 550, 245, 26, WHITE,
                  "center", bold=True)


def main():
    Creamery()
    arcade.run()


if __name__ == "__main__":
    main()
