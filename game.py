import math
import random


import arcade


import assets
from customer import Customer, WAITING_STATES
from order import Order, generate_order
from ingredients import FLAVORS, TOPPINGS, VESSELS, SIDES




SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Rev's Creamery"


# Both the number of customers per round and how many can be in the shop at once
# grow with difficulty. The time each customer will wait (ORDER_TIME in customer.py)
# is the same at every difficulty.
ORDERS_PER_ROUND = {1: 5, 2: 7, 3: 9}
MAX_CUSTOMERS = {1: 2, 2: 3, 3: 4}
FAST_TIME = 60          # seconds after arriving: serve a correct order this fast for 3 stars
ARRIVAL_GAP = 8
WIN_AVERAGE = 2.5

# One clock for the whole round (seconds). Same at every difficulty.
ROUND_TIME = 300

# Ice cream supply: this many scoops until the freezer is empty, then RESTOCK_TIME seconds
# of refilling during which no new scoops can be added.
ICE_CREAM_STOCK = 8
RESTOCK_TIME = 6

# Shop layout: customers stand behind a wooden counter that spans the screen.
COUNTER_BOTTOM = 115
COUNTER_TOP = 280
CUSTOMER_FEET_Y = 272        # a few pixels behind the counter's top edge
CUSTOMER_MAX_HEIGHT = 198    # height of the tallest character; the others scale with it
CUSTOMER_SLOTS = [150, 340, 530, 720]   # where customers stand at the counter

# Image files (looked up next to game.py, then in an "assets" folder).
START_BG_FILES = ("beach1.png",)         # sunset beach: start, trophy screens
SHOP_BG_FILES = ("beach2.png",)          # daytime beach: the shop and results screens
COUNTER_FILES = ("wood.png",)
TROPHY_FILES = ("trophy.png",)

# One entry per customer PNG. "names" are the names that character can be given.
CHARACTERS = [
    {   # pink sweatshirt student
        "key": "sweatshirt_girl",
        "files": ("female_student__2_.png", "female_student.png"),
        "names": ["Maya", "Akari", "Noor"],
    },
    {   # corps cadet
        "key": "cadet",
        "files": ("queen_rev__2_.png", "queen_rev.png"),
        "names": ["Jordan", "Kai"],
    },
    {   # maroon hoodie student
        "key": "hoodie_student",
        "files": ("sorority_girl__2_.png", "sorority_girl.png"),
        "names": ["Tobi", "Avery"],
    },
    {   # the collie in the crown
        "key": "rev",
        "files": ("stinky_student__2_.png", "stinky_student.png"),
        "names": ["Rev"],
    },
]

# Gold, top row to bottom row, for the pixel-font title.
TITLE_GRADIENT = [
    (255, 246, 170), (255, 236, 120), (255, 220, 70), (255, 200, 40),
    (245, 170, 20), (225, 140, 15), (200, 110, 10),
]


# How many scoops you may stack at each difficulty.
MAX_SCOOPS = {1: 1, 2: 2, 3: 2}
# You can add several of the same flavor / topping, up to these limits.
MAX_EACH_FLAVOR = 2
MAX_EACH_TOPPING = 3


FLAVOR_COLORS = {
    "Vanilla": (250, 235, 190),
    "Chocolate": (110, 70, 45),
    "Strawberry": (250, 150, 175),
    "Mint": (160, 230, 190),
    "Cookie Dough": (215, 185, 135),
}


TOPPING_COLORS = {
    "Sprinkles": (255, 105, 180),
    "Caramel Drizzle": (210, 140, 60),
    "Chocolate Drizzle": (80, 45, 30),
    "Cherries": (210, 40, 60),
    "Strawberries": (240, 70, 90),
    "Whipped Cream": (250, 250, 245),
    "Chocolate Chips": (90, 55, 40),
    "Crushed Oreos": (70, 65, 70),
}


# ---------------- BUILD-SCREEN LAYOUT ----------------
# Everything in the build menu is placed from these numbers so nothing overlaps.
MENU_LEFT = 515          # left edge of the menu content (right-hand panel)
MENU_RIGHT = 1175        # right edge of the menu content
ITEMS_PER_ROW = 3        # flavor / topping grid columns
ITEM_W = 184             # width of an ingredient button
MINUS_W = 28             # width of the small "-" button beside it
CELL_W = ITEM_W + 4 + MINUS_W
CELL_GAP = 6
ROW_H = 40
ROW_STEP = 48


ITEM_BG = (250, 250, 250)
SELECTED_BG = (255, 241, 190)
DISABLED_BG = (222, 222, 222)
INK = (40, 40, 40)
MUTED = (110, 110, 110)


CONE_COLOR = (222, 176, 100)
CONE_LINES = (170, 120, 60)
CUP_COLOR = (245, 245, 250)
CUP_STRIPE = (235, 90, 110)
SPRINKLE_COLORS = [
    (255, 80, 150),
    (255, 220, 60),
    (80, 170, 255),
    (120, 220, 120),
    (255, 150, 50),
]


CROWN_TOPPINGS = ("Whipped Cream", "Cherries", "Strawberries")




def lighten(color, amount=45):
    return (
        min(255, color[0] + amount),
        min(255, color[1] + amount),
        min(255, color[2] + amount),
    )




def count_lines(counter, keep_order=False):
    """Turn a Counter into ['Vanilla x2', 'Mint'] style lines."""
    pairs = [(name, count) for name, count in counter.items() if count > 0]
    if not keep_order:
        pairs.sort()
    return [f"{name} x{count}" if count > 1 else name for name, count in pairs]




def topping_kind(name):
    if "Drizzle" in name:
        return "drizzle"
    if name in CROWN_TOPPINGS:
        return "crown"
    return "scatter"




def scatter_points(name, how_many, radius):
    """Stable random spots on a scoop. Adding more never moves the old ones."""
    rng = random.Random(name)
    points = []
    for _ in range(how_many):
        dx = rng.uniform(-0.8, 0.8) * radius
        fraction = rng.random()
        angle = rng.uniform(0, math.pi)
        y_max = math.sqrt(max(0.0, radius * radius - dx * dx)) - 4
        y_min = -0.15 * radius
        dy = y_min + fraction * (y_max - y_min) if y_max > y_min else 0.0
        points.append((dx, dy, angle))
    return points




class Button:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        color=arcade.color.LIGHT_GRAY,
        swatch=None,
        font_size=11,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.color = color
        self.swatch = swatch
        self.font_size = font_size


    def contains(self, mouse_x, mouse_y):
        return (
            self.x - self.width / 2 <= mouse_x <= self.x + self.width / 2
            and self.y - self.height / 2 <= mouse_y <= self.y + self.height / 2
        )


    def draw(self, selected=False, count=0, disabled=False):
        if disabled:
            fill = DISABLED_BG
        elif selected:
            fill = SELECTED_BG
        else:
            fill = self.color


        outline = arcade.color.ORANGE if selected else arcade.color.DARK_GRAY
        outline_width = 3 if selected else 2
        text_color = (150, 150, 150) if disabled else arcade.color.BLACK


        rect = arcade.XYWH(self.x, self.y, self.width, self.height)
        arcade.draw_rect_filled(rect, fill)
        arcade.draw_rect_outline(rect, outline, outline_width)


        if self.swatch is not None:
            # Menu item: colored dot + name on the left, count on the right.
            dot_x = self.x - self.width / 2 + 16
            arcade.draw_circle_filled(dot_x, self.y, 8, self.swatch)
            arcade.draw_circle_outline(dot_x, self.y, 8, arcade.color.DARK_GRAY, 1)
            arcade.draw_text(
                self.text,
                dot_x + 14,
                self.y,
                text_color,
                self.font_size,
                anchor_x="left",
                anchor_y="center",
            )
            if count > 0:
                arcade.draw_text(
                    f"x{count}",
                    self.x + self.width / 2 - 10,
                    self.y,
                    arcade.color.BLACK,
                    self.font_size + 2,
                    anchor_x="right",
                    anchor_y="center",
                    bold=True,
                )
        else:
            arcade.draw_text(
                self.text,
                self.x,
                self.y,
                text_color,
                self.font_size,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )




class CreameryGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        # Only visible if a background image is missing.
        self.background_color = arcade.color.LIGHT_BLUE

        self.load_art()

        self.game_state = "START"
        self.difficulty = 1
        self.customers = []
        self.customers_created = 0
        self.orders_completed = 0
        self.scores = []
        self.selected_customer = None
        self.message = ""
        self.spawn_timer = 0
        self.building_order = False

        # Overall round clock.
        self.round_time_left = ROUND_TIME
        self.time_up = False

        # Ice cream supply: scoops already served since the last refill, and the
        # restock cooldown (restocking is True while the freezer refills).
        self.scoops_used = 0
        self.restocking = False
        self.restock_left = 0.0


        # The order being built, plus the order things were added in. The
        # stacks drive the live picture so scoops pile up in the order you
        # add them (the Counters in player_order are what gets scored).
        self.player_order = Order()
        self.scoop_stack = []
        self.topping_stack = []


        self.create_buttons()


    # ---------------- ART ----------------
    def load_art(self):
        """Load and prepare every image once. Anything missing falls back to plain shapes."""
        screen = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.start_bg = assets.load_background(START_BG_FILES, screen, anchor_y=0.7)
        self.shop_bg = assets.load_background(SHOP_BG_FILES, screen)
        self.counter_art = assets.load_counter(
            COUNTER_FILES, (SCREEN_WIDTH, COUNTER_TOP - COUNTER_BOTTOM)
        )
        self.characters = assets.load_characters(CHARACTERS, CUSTOMER_MAX_HEIGHT)
        self.trophy_art = assets.load_trophy(TROPHY_FILES, 260)
        self.title_art = assets.pixel_text_art(
            "REV'S CREAMERY", 11, TITLE_GRADIENT, outline=(70, 25, 60)
        )
        self.subtitle_art = assets.pixel_text_art(
            "BEACHSIDE ICE CREAM SHOP", 5, (255, 255, 255), outline=(60, 30, 70)
        )

    @staticmethod
    def draw_art(art, center_x, center_y):
        # Snap to whole pixels so pixel art stays crisp instead of getting blurry.
        left = round(center_x - art.width / 2)
        bottom = round(center_y - art.height / 2)
        arcade.draw_texture_rect(
            art.texture, arcade.LBWH(left, bottom, art.width, art.height)
        )

    def draw_backdrop(self, art):
        if art is not None:
            self.draw_art(art, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    # ---------------- BUTTONS ----------------
    def make_item_buttons(self, names, colors, first_row_y):
        """A grid of ingredient buttons, each with a small '-' button beside it."""
        buttons = []
        minus_buttons = []
        for i, name in enumerate(names):
            row, col = divmod(i, ITEMS_PER_ROW)
            left = MENU_LEFT + col * (CELL_W + CELL_GAP)
            y = first_row_y - row * ROW_STEP
            buttons.append(
                Button(
                    left + ITEM_W / 2,
                    y,
                    ITEM_W,
                    ROW_H,
                    name,
                    ITEM_BG,
                    swatch=colors.get(name, (200, 200, 200)),
                    font_size=10,
                )
            )
            minus_buttons.append(
                Button(
                    left + ITEM_W + 4 + MINUS_W / 2,
                    y,
                    MINUS_W,
                    ROW_H,
                    "-",
                    ITEM_BG,
                    font_size=16,
                )
            )
        return buttons, minus_buttons


    def create_buttons(self):
        self.start_button = Button(
            600, 160, 220, 70, "START", arcade.color.LIGHT_GREEN, font_size=20
        )
        self.build_button = Button(
            600, 80, 190, 55, "MAKE ORDER", arcade.color.LIGHT_GREEN, font_size=15
        )


        self.retry_button = Button(430, 200, 180, 60, "TRY AGAIN", font_size=14)
        self.upgrade_button = Button(
            730, 200, 240, 60, "NEXT DIFFICULTY", arcade.color.LIGHT_GREEN, font_size=14
        )


        # Bottom action row of the build screen.
        self.cancel_button = Button(590, 165, 130, 52, "CANCEL", font_size=13)
        self.clear_button = Button(
            735, 165, 130, 52, "CLEAR", arcade.color.LIGHT_CORAL, font_size=13
        )
        self.serve_button = Button(
            1050, 165, 220, 52, "SERVE", arcade.color.LIGHT_GREEN, font_size=16
        )


        # Ingredient grids (3 columns) with a "-" button next to each item.
        self.flavor_buttons, self.flavor_minus_buttons = self.make_item_buttons(
            FLAVORS, FLAVOR_COLORS, 476
        )
        self.topping_buttons, self.topping_minus_buttons = self.make_item_buttons(
            TOPPINGS, TOPPING_COLORS, 356
        )


        # Container + side share one row at the top of the menu.
        self.vessel_buttons = [
            Button(570 + i * 120, 555, 110, 40, vessel, ITEM_BG, font_size=12)
            for i, vessel in enumerate(VESSELS)
        ]
        self.side_buttons = [
            Button(828 + i * 112, 555, 106, 40, side, ITEM_BG, font_size=12)
            for i, side in enumerate(SIDES)
        ]


    # ---------------- ROUND / CUSTOMERS ----------------
    def reset_build(self):
        self.player_order = Order()
        self.scoop_stack = []
        self.topping_stack = []


    @property
    def orders_per_round(self):
        return ORDERS_PER_ROUND[self.difficulty]

    @property
    def max_customers(self):
        return MAX_CUSTOMERS[self.difficulty]

    def start_round(self):
        self.customers = []
        self.customers_created = 0
        self.orders_completed = 0
        self.scores = []
        self.selected_customer = None
        self.reset_build()
        self.building_order = False
        self.message = ""
        self.round_time_left = ROUND_TIME
        self.time_up = False
        self.scoops_used = 0
        self.restocking = False
        self.restock_left = 0.0
        self.game_state = "PLAYING"
        self.add_customer()
        self.spawn_timer = ARRIVAL_GAP


    def active_customers(self):
        return [customer for customer in self.customers if customer.is_active]


    def add_customer(self):
        if self.customers_created >= self.orders_per_round:
            return
        active = self.active_customers()
        if len(active) >= self.max_customers:
            return


        used_positions = [customer.target_x for customer in active]
        available_positions = [p for p in CUSTOMER_SLOTS if p not in used_positions]
        if not available_positions:
            return


        # Prefer a character nobody in the shop is using right now.
        taken_characters = [customer.character for customer in active]
        free_characters = [c for c in CHARACTERS if c["key"] not in taken_characters]
        character = random.choice(free_characters or CHARACTERS)

        taken_names = [customer.name for customer in active]
        free_names = [name for name in character["names"] if name not in taken_names]


        customer = Customer(
            name=random.choice(free_names or character["names"]),
            order=generate_order(self.difficulty),
            target_x=available_positions[0],
            y=CUSTOMER_FEET_Y,
            character=character["key"],
        )
        self.customers.append(customer)
        self.customers_created += 1


    def take_order(self, customer):
        if not customer.is_waiting_to_order:
            return
        customer.start_order_timer()
        self.selected_customer = customer
        self.message = f"{customer.name}'s order taken!"


    # ---------------- BUILDING ----------------
    def start_building(self):
        if self.selected_customer is None or not self.selected_customer.order_taken:
            return
        self.reset_build()
        self.building_order = True
        self.message = f"Making {self.selected_customer.name}'s order"


    def clear_order(self):
        self.reset_build()
        self.message = "Order cleared."


    def stop_building(self):
        self.building_order = False
        self.reset_build()
        self.message = "Order cancelled."


    @staticmethod
    def remove_last(stack, name):
        """Remove the most recently added copy of `name` (top of the pile)."""
        for i in range(len(stack) - 1, -1, -1):
            if stack[i] == name:
                del stack[i]
                return


    def ice_cream_left(self):
        """Scoops still in the freezer (scoops sitting in the order being built count as taken)."""
        return max(0, ICE_CREAM_STOCK - self.scoops_used - len(self.scoop_stack))

    def check_restock(self):
        if not self.restocking and self.ice_cream_left() <= 0:
            self.restocking = True
            self.restock_left = RESTOCK_TIME
            self.message = f"Out of ice cream! Restocking for {RESTOCK_TIME} seconds..."

    def update_restock(self, delta_time):
        if not self.restocking:
            return
        self.restock_left -= delta_time
        if self.restock_left <= 0:
            self.restocking = False
            self.restock_left = 0.0
            self.scoops_used = 0
            self.message = "Ice cream restocked!"

    def add_flavor(self, flavor):
        if self.restocking:
            self.message = f"Out of ice cream! Restocking... {math.ceil(self.restock_left)}s"
            return
        max_scoops = MAX_SCOOPS[self.difficulty]
        if len(self.scoop_stack) >= max_scoops:
            self.message = f"Maximum {max_scoops} scoop(s) at this difficulty."
            return
        if self.player_order.flavors[flavor] >= MAX_EACH_FLAVOR:
            self.message = f"Maximum {MAX_EACH_FLAVOR} scoops of the same flavor."
            return
        self.scoop_stack.append(flavor)
        self.player_order.flavors[flavor] += 1
        self.message = f"Added a scoop of {flavor}"
        self.check_restock()


    def remove_flavor(self, flavor):
        if self.player_order.flavors[flavor] <= 0:
            return
        self.remove_last(self.scoop_stack, flavor)
        self.player_order.flavors[flavor] -= 1
        if self.player_order.flavors[flavor] <= 0:
            del self.player_order.flavors[flavor]
        self.message = f"Removed a scoop of {flavor}"


    def add_topping(self, topping):
        if self.player_order.toppings[topping] >= MAX_EACH_TOPPING:
            self.message = f"Maximum {MAX_EACH_TOPPING} of the same topping."
            return
        self.topping_stack.append(topping)
        self.player_order.toppings[topping] += 1
        self.message = f"Added {topping}"


    def remove_topping(self, topping):
        if self.player_order.toppings[topping] <= 0:
            return
        self.remove_last(self.topping_stack, topping)
        self.player_order.toppings[topping] -= 1
        if self.player_order.toppings[topping] <= 0:
            del self.player_order.toppings[topping]
        self.message = f"Removed {topping}"


    # ---------------- SCORING ----------------
    def calculate_score(self, customer):
        if not customer.order.matches(self.player_order):
            return 1
        return 3 if customer.time_used <= FAST_TIME else 2


    def serve_customer(self):
        customer = self.selected_customer
        if customer is None:
            return
        if self.player_order.total_scoops() == 0:
            self.message = "Add at least one scoop first."
            return
        if self.player_order.vessel is None:
            self.message = "Choose a cup or cone first."
            return
        if self.difficulty >= 2 and self.player_order.side is None:
            self.message = "Choose a side first."
            return


        stars = self.calculate_score(customer)
        customer.stars = stars
        customer.reaction = "happy" if stars >= 2 else "sad"
        self.scores.append(stars)
        self.orders_completed += 1

        # The scoops in this order are used up (they only come back if you cancel/clear).
        self.scoops_used += len(self.scoop_stack)


        if stars == 3:
            self.message = f"{customer.name} loved it! 3 stars!"
        elif stars == 2:
            self.message = f"{customer.name} liked it! 2 stars!"
        else:
            self.message = f"Wrong order! {customer.name} gave 1 star."


        customer.state = "LEAVING"
        self.selected_customer = None
        self.reset_build()
        self.building_order = False
        self.check_restock()
        self.check_round_finished()


    def customer_timed_out(self, customer):
        customer.stars = 0
        customer.reaction = "sad"
        self.scores.append(0)
        self.orders_completed += 1
        customer.state = "LEAVING"
        self.message = f"{customer.name} left! 0 stars."


        if self.selected_customer is customer:
            self.selected_customer = None
            self.reset_build()
            self.building_order = False


        self.check_round_finished()


    def check_round_finished(self):
        if self.orders_completed >= self.orders_per_round:
            self.game_state = "RESULTS"
            return
        self.spawn_timer = 1

    def end_round_time_up(self):
        """The round clock hit zero: every customer not served yet counts as 0 stars."""
        missing = self.orders_per_round - len(self.scores)
        self.scores.extend([0] * max(0, missing))
        self.orders_completed = len(self.scores)
        self.time_up = True
        self.round_time_left = 0.0
        self.selected_customer = None
        self.building_order = False
        self.reset_build()
        self.game_state = "RESULTS"


    def average_score(self):
        return sum(self.scores) / len(self.scores) if self.scores else 0


    def upgrade_difficulty(self):
        if self.average_score() < WIN_AVERAGE:
            return
        if self.difficulty < 3:
            self.difficulty += 1
            self.start_round()
        else:
            self.game_state = "TROPHY"


    # ---------------- UPDATE ----------------
    def on_update(self, delta_time):
        if self.game_state != "PLAYING":
            return


        # Overall round clock and the ice cream freezer keep running even while
        # you are busy building an order.
        self.round_time_left = max(0.0, self.round_time_left - delta_time)
        self.update_restock(delta_time)


        for customer in self.customers:
            customer.walk_to_counter(delta_time)
            customer.leave_shop(delta_time)
            # Patience runs from the moment a customer reaches the counter.
            customer.update_timer(delta_time)
            if customer.has_timed_out:
                self.customer_timed_out(customer)
            if self.game_state != "PLAYING":
                return


        if self.round_time_left <= 0:
            self.end_round_time_up()
            return


        if self.customers_created < self.orders_per_round and len(self.active_customers()) < self.max_customers:
            self.spawn_timer -= delta_time
            if self.spawn_timer <= 0:
                self.add_customer()
                self.spawn_timer = ARRIVAL_GAP


    # ---------------- DRAW ----------------
    def on_draw(self):
        self.clear()
        if self.game_state == "START":
            self.draw_start()
        elif self.game_state == "PLAYING":
            self.draw_shop()
        elif self.game_state == "RESULTS":
            self.draw_results()
        elif self.game_state == "TROPHY":
            self.draw_trophy()


    def draw_start(self):
        self.draw_backdrop(self.start_bg)

        # Pixel-font title (drawn from a pre-rendered image, so no font install needed).
        self.draw_art(self.title_art, 600, 598)
        self.draw_art(self.subtitle_art, 600, 505)

        lines = [
            "1.  Customers walk up to the counter - their patience timer starts right away!",
            "2.  Click a customer to take their order, then press MAKE ORDER.",
            "3.  Pick the container, scoops, toppings and side. Right-click removes.",
            "4.  Press SERVE: right + fast = 3 stars, right = 2, wrong = 1, walked out = 0.",
            f"5.  Beat the round clock and average {WIN_AVERAGE} stars to unlock the next level.",
            f"6.  Empty freezer? Restocking the ice cream takes {RESTOCK_TIME} seconds!",
        ]
        panel = arcade.XYWH(600, 335, 900, 220)
        arcade.draw_rect_filled(panel, (0, 0, 0, 165))
        arcade.draw_rect_outline(panel, (255, 214, 120), 3)
        arcade.draw_text(
            "HOW TO PLAY", 600, 418, arcade.color.GOLD, 17, anchor_x="center", bold=True
        )
        y = 386
        for line in lines:
            arcade.draw_text(line, 170, y, arcade.color.WHITE, 14, anchor_y="center")
            y -= 27

        self.start_button.draw()


    def draw_shop(self):
        if self.shop_bg is not None:
            self.draw_backdrop(self.shop_bg)
        else:
            # No background image found: fall back to flat colours.
            arcade.draw_rect_filled(arcade.XYWH(600, 550, 1200, 300), arcade.color.SKY_BLUE)
            arcade.draw_rect_filled(arcade.XYWH(600, 390, 1200, 120), arcade.color.BLUE_GREEN)


        if self.building_order:
            self.draw_counter()
            self.draw_split_screen()
            self.draw_waiting_strip()
        else:
            self.draw_customer_sprites()
            self.draw_counter()
            self.draw_customer_plates()
            if self.selected_customer and self.selected_customer.order_taken:
                self.draw_ticket(self.selected_customer, 600, 560, 650, 170, 13, 19)
                self.build_button.draw()


        # Header goes last so it always sits on top and is never covered.
        self.draw_header()


        if self.message:
            arcade.draw_rect_filled(arcade.XYWH(600, 30, 760, 34), (0, 0, 0, 150))
            arcade.draw_text(
                self.message,
                600,
                30,
                arcade.color.WHITE,
                15,
                anchor_x="center",
                anchor_y="center",
            )


    def draw_header(self):
        arcade.draw_rect_filled(arcade.LBWH(0, 652, SCREEN_WIDTH, 48), (0, 0, 0, 140))
        arcade.draw_text("REV'S CREAMERY", 25, 658, arcade.color.WHITE, 26, bold=True)

        # Overall round clock.
        seconds = max(0, math.ceil(self.round_time_left))
        minutes, secs = divmod(seconds, 60)
        if seconds <= 30:
            clock_color = arcade.color.RED
        elif seconds <= 60:
            clock_color = arcade.color.ORANGE
        else:
            clock_color = arcade.color.WHITE
        arcade.draw_text(
            f"TIME LEFT  {minutes}:{secs:02d}",
            600,
            661,
            clock_color,
            20,
            anchor_x="center",
            bold=True,
        )

        arcade.draw_text(
            f"Difficulty: {self.difficulty}     Orders: {self.orders_completed}/{self.orders_per_round}",
            1175,
            664,
            arcade.color.WHITE,
            16,
            anchor_x="right",
            bold=True,
        )


    def draw_counter(self):
        height = COUNTER_TOP - COUNTER_BOTTOM
        center_y = COUNTER_BOTTOM + height / 2
        if self.counter_art is not None:
            self.draw_art(self.counter_art, SCREEN_WIDTH / 2, center_y)
        else:
            arcade.draw_rect_filled(
                arcade.XYWH(SCREEN_WIDTH / 2, center_y, SCREEN_WIDTH, height), arcade.color.LIGHT_BROWN
            )
        # Dark edges give the counter a bit of depth.
        arcade.draw_line(0, COUNTER_TOP, SCREEN_WIDTH, COUNTER_TOP, (55, 28, 10), 5)
        arcade.draw_line(0, COUNTER_BOTTOM, SCREEN_WIDTH, COUNTER_BOTTOM, (55, 28, 10), 5)


    def draw_customer_sprites(self):
        # Customers who are still walking are drawn first, so they pass behind the
        # customers standing at the counter.
        customers = sorted(self.active_customers(), key=lambda c: c.state in WAITING_STATES)
        for customer in customers:
            bob = 0.0
            if customer.state in ("ENTERING", "LEAVING"):
                bob = abs(math.sin(customer.x * 0.06)) * 6   # little walking hop
            art = self.characters.get(customer.character)
            if art is not None:
                self.draw_art(art, customer.x, customer.y + bob + art.height / 2)
            else:
                # Image missing: the original pink circle.
                arcade.draw_circle_filled(customer.x, customer.y + bob + 45, 45, arcade.color.PINK)


    def draw_customer_plates(self):
        """Name, patience bar and status for everyone waiting, on the front of the counter."""
        for customer in self.active_customers():
            if customer.state not in WAITING_STATES:
                continue
            selected = customer is self.selected_customer
            x = customer.x

            if selected:
                art = self.characters.get(customer.character)
                width = art.width if art else 90
                height = art.height if art else 90
                arcade.draw_rect_outline(
                    arcade.XYWH(x, customer.y + height / 2 + 2, width + 20, height + 12),
                    arcade.color.YELLOW,
                    4,
                )

            plate = arcade.XYWH(x, 216, 170, 102)
            arcade.draw_rect_filled(plate, (35, 22, 12, 185))
            arcade.draw_rect_outline(
                plate,
                arcade.color.YELLOW if selected else (235, 200, 140),
                3 if selected else 2,
            )
            arcade.draw_text(
                customer.name, x, 242, arcade.color.WHITE, 14, anchor_x="center", bold=True
            )
            self.draw_timer_bar(
                customer, x, 224, 144, label_dy=-23, label_color=arcade.color.WHITE
            )

            if customer.is_waiting_to_order:
                status, status_color = "CLICK TO ORDER", arcade.color.YELLOW
            elif selected:
                status, status_color = "SELECTED", arcade.color.YELLOW
            else:
                status, status_color = "Order taken", (225, 225, 225)
            arcade.draw_text(
                status, x, 179, status_color, 12, anchor_x="center", bold=True
            )


    def draw_avatar(self, customer, center_x, center_y):
        art = self.characters.get(customer.character)
        frame = arcade.XYWH(center_x, center_y, 68, 68)
        if art is not None and art.avatar is not None:
            arcade.draw_rect_filled(frame, (255, 250, 238))
            arcade.draw_texture_rect(art.avatar, arcade.XYWH(center_x, center_y, 64, 64))
            arcade.draw_rect_outline(frame, arcade.color.BLACK, 2)
        else:
            arcade.draw_circle_filled(center_x, center_y, 30, arcade.color.PINK)
            arcade.draw_circle_outline(center_x, center_y, 30, arcade.color.BLACK, 2)


    def draw_waiting_strip(self):
        """While you build, show everyone else's patience so you can plan your next move."""
        others = [
            customer
            for customer in self.active_customers()
            if customer is not self.selected_customer and customer.state in WAITING_STATES
        ]
        for i, customer in enumerate(others):
            left = 18 + i * 182
            chip = arcade.LBWH(left, 56, 174, 50)
            arcade.draw_rect_filled(chip, (0, 0, 0, 150))
            arcade.draw_rect_outline(chip, (235, 200, 140), 2)

            art = self.characters.get(customer.character)
            if art is not None and art.avatar_small is not None:
                arcade.draw_texture_rect(art.avatar_small, arcade.XYWH(left + 27, 81, 40, 40))
            else:
                arcade.draw_circle_filled(left + 27, 81, 18, arcade.color.PINK)

            arcade.draw_text(
                f"{customer.name}  {int(customer.time_left)}s",
                left + 54,
                87,
                arcade.color.WHITE,
                11,
                bold=True,
            )
            self.draw_timer_bar(
                customer, left + 54 + 57, 74, 114, label=False, bar_height=10
            )


    def draw_section_label(self, text, x, y, line=True):
        arcade.draw_text(text, x, y, MUTED, 12, anchor_y="top", bold=True)
        if line:
            arcade.draw_line(MENU_LEFT, y - 17, MENU_RIGHT, y - 17, (190, 205, 215), 1)


    def draw_split_screen(self):
        customer = self.selected_customer
        if customer is None:
            return


        # ---------- LEFT PANEL: customer, live ice cream, order ticket ----------
        left_panel = arcade.XYWH(250, 380, 480, 540)
        arcade.draw_rect_filled(left_panel, (245, 232, 200))
        arcade.draw_rect_outline(left_panel, (160, 140, 110), 3)


        self.draw_avatar(customer, 65, 605)
        arcade.draw_text(
            customer.name, 110, 620, arcade.color.BLACK, 18, anchor_y="center", bold=True
        )
        self.draw_timer_bar(customer, 280, 590, 340)


        # Live picture: redrawn every frame from what is in the order right now.
        preview = arcade.XYWH(250, 408, 450, 264)
        arcade.draw_rect_filled(preview, (255, 250, 238))
        arcade.draw_rect_outline(preview, (200, 185, 150), 2)
        arcade.draw_text(
            "YOUR BUILD", 250, 536, MUTED, 11, anchor_x="center", anchor_y="top", bold=True
        )
        self.draw_ice_cream(250, 283)
        if self.player_order.side:
            arcade.draw_text(
                f"Side: {self.player_order.side}", 36, 284, INK, 11, bold=True
            )


        self.draw_ticket(customer, 250, 195, 450, 156, 12, 18)


        # ---------- RIGHT PANEL: build menu ----------
        right_panel = arcade.XYWH(845, 380, 690, 540)
        arcade.draw_rect_filled(right_panel, (232, 244, 250))
        arcade.draw_rect_outline(right_panel, (120, 150, 170), 3)


        arcade.draw_text(
            "BUILD STATION", 845, 644, arcade.color.BLACK, 20, anchor_x="center", anchor_y="top", bold=True
        )
        arcade.draw_text(
            "Left-click = add           Right-click [ - ] = remove",
            845,
            618,
            (90, 90, 90),
            11,
            anchor_x="center",
            anchor_y="top",
        )


        # Container (+ side from difficulty 2).
        self.draw_section_label("CONTAINER", MENU_LEFT, 596)
        for button in self.vessel_buttons:
            button.draw(selected=self.player_order.vessel == button.text)


        if self.difficulty >= 2:
            self.draw_section_label("SIDE", 775, 596, line=False)
            for button in self.side_buttons:
                button.draw(selected=self.player_order.side == button.text)


        # Flavors.
        self.draw_section_label("FLAVORS", MENU_LEFT, 518)
        for button, minus in zip(self.flavor_buttons, self.flavor_minus_buttons):
            count = self.player_order.flavors[button.text]
            button.draw(selected=count > 0, count=count)
            minus.draw(disabled=count == 0)


        if self.restocking:
            self.draw_restock_banner()


        # Toppings.
        self.draw_section_label("TOPPINGS", MENU_LEFT, 398)
        for button, minus in zip(self.topping_buttons, self.topping_minus_buttons):
            count = self.player_order.toppings[button.text]
            button.draw(selected=count > 0, count=count)
            minus.draw(disabled=count == 0)


        # Running totals.
        max_scoops = MAX_SCOOPS[self.difficulty]
        total_toppings = sum(self.player_order.toppings.values())
        arcade.draw_text(
            f"Scoops: {len(self.scoop_stack)}/{max_scoops}        Toppings: {total_toppings}",
            MENU_LEFT,
            226,
            INK,
            12,
            anchor_y="top",
            bold=True,
        )


        self.draw_supply_meter()

        self.cancel_button.draw()
        self.clear_button.draw()
        self.serve_button.draw()


    def draw_restock_banner(self):
        center_x = (MENU_LEFT + MENU_RIGHT) / 2
        arcade.draw_rect_filled(
            arcade.XYWH(center_x, 452, MENU_RIGHT - MENU_LEFT + 12, 96), (20, 20, 40, 150)
        )
        banner = arcade.XYWH(center_x, 452, 560, 46)
        arcade.draw_rect_filled(banner, (170, 40, 40))
        arcade.draw_rect_outline(banner, arcade.color.WHITE, 3)
        arcade.draw_text(
            f"OUT OF ICE CREAM!  Restocking... {math.ceil(self.restock_left)}s",
            center_x,
            452,
            arcade.color.WHITE,
            15,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )


    def draw_supply_meter(self):
        label_x = 830
        bar_left = 948
        bar_width = 126
        y = 218

        arcade.draw_text("ICE CREAM:", label_x, y, INK, 12, anchor_y="center", bold=True)
        arcade.draw_rect_filled(
            arcade.XYWH(bar_left + bar_width / 2, y, bar_width, 16), arcade.color.DARK_GRAY
        )

        if self.restocking:
            fraction = 1 - self.restock_left / RESTOCK_TIME
            color = (90, 170, 230)
            text = "REFILLING"
        else:
            left = self.ice_cream_left()
            fraction = left / ICE_CREAM_STOCK
            if fraction > 0.5:
                color = arcade.color.GREEN
            elif fraction > 0.25:
                color = arcade.color.ORANGE
            else:
                color = arcade.color.RED
            text = f"{left}/{ICE_CREAM_STOCK}"

        fraction = max(0.0, min(1.0, fraction))
        if fraction > 0:
            arcade.draw_rect_filled(
                arcade.LBWH(bar_left, y - 8, bar_width * fraction, 16), color
            )
        arcade.draw_text(text, bar_left + bar_width + 10, y, INK, 12, anchor_y="center", bold=True)


    # ---------------- LIVE ICE CREAM ----------------
    @staticmethod
    def fill_triangle(a, b, c, color):
        arcade.draw_triangle_filled(a[0], a[1], b[0], b[1], c[0], c[1], color)


    @staticmethod
    def line_between(a, b, color, width):
        arcade.draw_line(a[0], a[1], b[0], b[1], color, width)


    def draw_vessel(self, cx, base_y, s):
        """Draw the cone/cup and return its height (scoops sit on top of it)."""
        vessel = self.player_order.vessel


        if vessel == "Cone":
            height = 90 * s
            half = 34 * s
            top_left = (cx - half, base_y + height)
            top_right = (cx + half, base_y + height)
            tip = (cx, base_y)
            self.fill_triangle(top_left, top_right, tip, CONE_COLOR)
            # Waffle pattern.
            for t in (0.35, 0.65, 0.95):
                t2 = t - 0.3
                self.line_between(
                    (cx - half * t, base_y + height * t),
                    (cx + half * t2, base_y + height * t2),
                    CONE_LINES,
                    1,
                )
                self.line_between(
                    (cx + half * t, base_y + height * t),
                    (cx - half * t2, base_y + height * t2),
                    CONE_LINES,
                    1,
                )
            self.line_between(top_left, tip, arcade.color.BLACK, 2)
            self.line_between(top_right, tip, arcade.color.BLACK, 2)
            self.line_between(top_left, top_right, arcade.color.BLACK, 2)
            return height


        if vessel == "Cup":
            height = 62 * s
            top_half = 40 * s
            bottom_half = 28 * s


            def point(fraction, side):
                half = bottom_half + (top_half - bottom_half) * fraction
                return (cx + side * half, base_y + height * fraction)


            top_left, top_right = point(1, -1), point(1, 1)
            bottom_left, bottom_right = point(0, -1), point(0, 1)
            self.fill_triangle(top_left, top_right, bottom_right, CUP_COLOR)
            self.fill_triangle(top_left, bottom_right, bottom_left, CUP_COLOR)


            stripe_low_l, stripe_low_r = point(0.25, -1), point(0.25, 1)
            stripe_high_l, stripe_high_r = point(0.55, -1), point(0.55, 1)
            self.fill_triangle(stripe_high_l, stripe_high_r, stripe_low_r, CUP_STRIPE)
            self.fill_triangle(stripe_high_l, stripe_low_r, stripe_low_l, CUP_STRIPE)


            self.line_between(top_left, top_right, arcade.color.BLACK, 2)
            self.line_between(top_right, bottom_right, arcade.color.BLACK, 2)
            self.line_between(bottom_right, bottom_left, arcade.color.BLACK, 2)
            self.line_between(bottom_left, top_left, arcade.color.BLACK, 2)
            return height


        # No container chosen yet.
        arcade.draw_text(
            "Pick a cone or cup", cx, base_y + 18, MUTED, 12, anchor_x="center", anchor_y="center"
        )
        return 76 * s


    def draw_ice_cream(self, cx, base_y):
        order = self.player_order
        scoops = self.scoop_stack
        count = len(scoops)


        # Shrink slightly if someone ever allows more than 2 scoops.
        s = min(1.0, 4.0 / (count + 2))
        radius = 36 * s
        step = 44 * s


        vessel_h = self.draw_vessel(cx, base_y, s)


        if count == 0:
            arcade.draw_text(
                "Add a scoop to start building",
                cx,
                base_y + vessel_h + 40,
                MUTED,
                12,
                anchor_x="center",
                anchor_y="center",
            )
            return


        # Scoops, bottom to top, in the order they were added.
        for i, flavor in enumerate(scoops):
            cy = base_y + vessel_h + 14 * s + i * step
            color = FLAVOR_COLORS.get(flavor, (230, 230, 230))


            # Scalloped "skirt" at the bottom of each scoop.
            for k in range(-2, 3):
                bump_x = cx + k * 0.39 * radius
                bump_y = cy - 0.72 * radius
                arcade.draw_circle_filled(bump_x, bump_y, 0.22 * radius, color)
                arcade.draw_circle_outline(bump_x, bump_y, 0.22 * radius, arcade.color.BLACK, 2)


            arcade.draw_circle_filled(cx, cy, radius, color)
            arcade.draw_circle_outline(cx, cy, radius, arcade.color.BLACK, 2)
            arcade.draw_circle_filled(
                cx - 0.35 * radius, cy + 0.4 * radius, 0.2 * radius, lighten(color)
            )


        top_cy = base_y + vessel_h + 14 * s + (count - 1) * step
        self.draw_toppings(cx, top_cy, radius, s)


    def draw_toppings(self, cx, top_cy, radius, s):
        """Toppings go on the top scoop; each extra copy visibly adds more."""
        order = self.player_order
        stack = self.topping_stack


        # 1) Scattered bits (sprinkles, chips, oreos): 8 more bits per copy.
        seen = []
        for name in stack:
            if name not in seen:
                seen.append(name)


        for name in seen:
            if topping_kind(name) != "scatter":
                continue
            color = TOPPING_COLORS.get(name, (200, 200, 200))
            points = scatter_points(name, 8 * order.toppings[name], radius)
            for k, (dx, dy, angle) in enumerate(points):
                px = cx + dx
                py = top_cy + dy
                if name == "Sprinkles":
                    reach = 4 * s
                    arcade.draw_line(
                        px - math.cos(angle) * reach,
                        py - math.sin(angle) * reach,
                        px + math.cos(angle) * reach,
                        py + math.sin(angle) * reach,
                        SPRINKLE_COLORS[k % len(SPRINKLE_COLORS)],
                        max(2, 3 * s),
                    )
                else:
                    arcade.draw_circle_filled(px, py, 3.2 * s, color)
                    if name == "Crushed Oreos":
                        arcade.draw_circle_filled(px + 1, py + 1, 1.2 * s, (225, 225, 225))


        # 2) Drizzles: one zig-zag line per copy, each lower than the last.
        drizzles = [name for name in stack if topping_kind(name) == "drizzle"]
        for j, name in enumerate(drizzles):
            color = TOPPING_COLORS.get(name, (200, 200, 200))
            offset = (0.55 - 0.2 * j) * radius
            half_width = math.sqrt(max(0.0, radius * radius - offset * offset)) - 3
            if half_width < 6:
                continue
            segments = 8
            points = []
            for k in range(segments + 1):
                px = cx - half_width * 0.95 + (2 * half_width * 0.95) * k / segments
                py = top_cy + offset + (4 * s if k % 2 else -4 * s)
                points.append((px, py))
            for a, b in zip(points, points[1:]):
                self.line_between(a, b, color, max(2, 3.5 * s))


        # 3) Heaped toppings: whipped cream, cherries, strawberries.
        crown = [name for name in stack if topping_kind(name) == "crown"]
        column_offsets = (-0.45, 0.0, 0.45)
        for j, name in enumerate(crown):
            row, col = divmod(j, 3)
            x = cx + (column_offsets[col] + (0.22 if row % 2 else 0.0)) * radius
            y = top_cy + 0.82 * radius + row * 0.3 * radius
            self.draw_crown_item(name, x, y, radius)


    def draw_crown_item(self, name, x, y, radius):
        color = TOPPING_COLORS.get(name, (200, 200, 200))


        if name == "Whipped Cream":
            for dy, size in ((0.0, 0.40), (0.3, 0.30), (0.55, 0.18)):
                arcade.draw_circle_filled(x, y + dy * radius, size * radius, color)
                arcade.draw_circle_outline(x, y + dy * radius, size * radius, (195, 195, 195), 1)


        elif name == "Cherries":
            cherry_y = y + 0.1 * radius
            arcade.draw_line(
                x, cherry_y + 0.2 * radius, x + 0.2 * radius, cherry_y + 0.62 * radius, (90, 60, 30), 2
            )
            arcade.draw_circle_filled(x, cherry_y, 0.24 * radius, color)
            arcade.draw_circle_filled(x - 0.08 * radius, cherry_y + 0.08 * radius, 0.07 * radius, (255, 190, 190))


        elif name == "Strawberries":
            berry_y = y + 0.12 * radius
            arcade.draw_circle_filled(x, berry_y, 0.26 * radius, color)
            for dx, dy in ((-0.1, 0.02), (0.1, 0.0), (0.0, -0.1)):
                arcade.draw_circle_filled(
                    x + dx * radius, berry_y + dy * radius, 0.03 * radius, (255, 230, 120)
                )
            self.fill_triangle(
                (x - 0.14 * radius, berry_y + 0.2 * radius),
                (x + 0.14 * radius, berry_y + 0.2 * radius),
                (x, berry_y + 0.42 * radius),
                (60, 160, 70),
            )


    # ---------------- TICKETS / TIMER ----------------
    def draw_ticket(self, customer, cx, cy, width, height, font, line_height):
        """Order ticket: flavors/container on the left, toppings/side on the right."""
        order = customer.order
        left = cx - width / 2
        top = cy + height / 2


        rect = arcade.XYWH(cx, cy, width, height)
        arcade.draw_rect_filled(rect, arcade.color.WHITE)
        arcade.draw_rect_outline(rect, arcade.color.DARK_GRAY, 2)


        arcade.draw_text(
            f"{customer.name}'s Order",
            cx,
            top - 8,
            arcade.color.BLACK,
            font + 3,
            anchor_x="center",
            anchor_y="top",
            bold=True,
        )


        start_y = top - 8 - (font + 3) * 1.35 - 8
        columns = [
            (
                left + 20,
                [
                    ("FLAVORS", count_lines(order.flavors, keep_order=True) or ["-"]),
                    ("CONTAINER", [order.vessel or "-"]),
                ],
            ),
            (
                left + width * 0.52,
                [
                    ("TOPPINGS", count_lines(order.toppings) or ["None"]),
                    ("SIDE", [order.side or "None"]),
                ],
            ),
        ]


        for x, sections in columns:
            y = start_y
            for header, lines in sections:
                arcade.draw_text(header, x, y, MUTED, font - 1, anchor_y="top", bold=True)
                y -= line_height
                for line in lines:
                    arcade.draw_text(line, x + 8, y, arcade.color.BLACK, font, anchor_y="top")
                    y -= line_height
                y -= 4


    def draw_timer_bar(
        self,
        customer,
        x,
        y,
        width=170,
        label_dy=-30,
        label_color=arcade.color.BLACK,
        label=True,
        bar_height=15,
    ):
        arcade.draw_rect_filled(arcade.XYWH(x, y, width, bar_height), arcade.color.DARK_GRAY)


        if customer.patience_level == "good":
            color = arcade.color.GREEN
        elif customer.patience_level == "warning":
            color = arcade.color.ORANGE
        else:
            color = arcade.color.RED


        if customer.timer_fraction > 0:
            arcade.draw_rect_filled(
                arcade.LBWH(
                    x - width / 2, y - bar_height / 2, width * customer.timer_fraction, bar_height
                ),
                color,
            )


        if label:
            arcade.draw_text(
                f"{int(customer.time_left)} sec", x, y + label_dy, label_color, 12, anchor_x="center"
            )


    # ---------------- RESULTS ----------------
    def draw_results(self):
        self.draw_backdrop(self.shop_bg)

        average = self.average_score()
        total_orders = self.orders_per_round
        panel = arcade.XYWH(600, 440, 760, 290)
        arcade.draw_rect_filled(panel, (0, 0, 0, 160))
        arcade.draw_rect_outline(panel, (255, 214, 120), 3)

        title = "TIME'S UP!" if self.time_up else "ROUND COMPLETE!"
        arcade.draw_text(title, 600, 520, arcade.color.WHITE, 42, anchor_x="center", bold=True)
        arcade.draw_text(f"Average: {average:.2f} / 3.00", 600, 440, arcade.color.WHITE, 28, anchor_x="center")
        arcade.draw_text(
            f"Total Stars: {sum(self.scores)} / {3 * total_orders}",
            600,
            392,
            arcade.color.WHITE,
            20,
            anchor_x="center",
        )

        if self.time_up:
            arcade.draw_text(
                "The clock ran out - customers not served count as 0 stars.",
                600,
                340,
                arcade.color.ORANGE,
                16,
                anchor_x="center",
            )
        else:
            seconds = max(0, math.ceil(self.round_time_left))
            minutes, secs = divmod(seconds, 60)
            arcade.draw_text(
                f"Time left on the clock: {minutes}:{secs:02d}",
                600,
                340,
                arcade.color.WHITE,
                16,
                anchor_x="center",
            )

        self.retry_button.draw()
        if average >= WIN_AVERAGE:
            self.upgrade_button.draw()


    def draw_trophy(self):
        self.draw_backdrop(self.start_bg)

        panel = arcade.XYWH(600, 470, 800, 130)
        arcade.draw_rect_filled(panel, (0, 0, 0, 160))
        arcade.draw_rect_outline(panel, (255, 214, 120), 3)
        arcade.draw_text(
            "GOLDEN SCOOP TROPHY!", 600, 480, arcade.color.GOLD, 40, anchor_x="center", bold=True
        )
        arcade.draw_text(
            "You served every difficulty like a pro!",
            600,
            432,
            arcade.color.WHITE,
            18,
            anchor_x="center",
        )

        if self.trophy_art is not None:
            self.draw_art(self.trophy_art, 600, 255)
        else:
            arcade.draw_circle_filled(600, 300, 80, arcade.color.GOLD)


    # ---------------- INPUT ----------------
    def toggle_choice(self, attribute, value, removing):
        """Cone/cup and sides: click to pick, click again (or right-click) to unpick."""
        if getattr(self.player_order, attribute) == value:
            setattr(self.player_order, attribute, None)
            self.message = f"Removed {value}"
        elif not removing:
            setattr(self.player_order, attribute, value)
            self.message = f"Chose {value}"


    def customer_at(self, x, y):
        """The waiting customer under the mouse (their sprite or the name plate below it)."""
        for customer in self.active_customers():
            # Customers who are walking in or out can't be picked.
            if customer.state not in WAITING_STATES:
                continue
            art = self.characters.get(customer.character)
            top = customer.y + (art.height if art else 90) + 10
            if abs(x - customer.x) <= 85 and 165 <= y <= top:
                return customer
        return None


    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state == "START":
            if self.start_button.contains(x, y):
                self.start_round()
            return


        if self.game_state == "RESULTS":
            if self.retry_button.contains(x, y):
                self.start_round()
                return
            if self.average_score() >= WIN_AVERAGE and self.upgrade_button.contains(x, y):
                self.upgrade_difficulty()
                return


        if self.game_state != "PLAYING":
            return


        if not self.building_order:
            customer = self.customer_at(x, y)
            if customer is not None:
                self.selected_customer = customer
                if customer.is_waiting_to_order:
                    self.take_order(customer)
                else:
                    self.message = f"Selected {customer.name}"
                return


            if self.selected_customer is not None and self.build_button.contains(x, y):
                self.start_building()
            return


        # Build mode: left-click adds; right-click (or the "-" button) removes.
        removing = button == arcade.MOUSE_BUTTON_RIGHT


        for main, minus in zip(self.flavor_buttons, self.flavor_minus_buttons):
            if minus.contains(x, y):
                self.remove_flavor(main.text)
                return
            if main.contains(x, y):
                if removing:
                    self.remove_flavor(main.text)
                else:
                    self.add_flavor(main.text)
                return


        for main, minus in zip(self.topping_buttons, self.topping_minus_buttons):
            if minus.contains(x, y):
                self.remove_topping(main.text)
                return
            if main.contains(x, y):
                if removing:
                    self.remove_topping(main.text)
                else:
                    self.add_topping(main.text)
                return


        for button_object in self.vessel_buttons:
            if button_object.contains(x, y):
                self.toggle_choice("vessel", button_object.text, removing)
                return


        if self.difficulty >= 2:
            for button_object in self.side_buttons:
                if button_object.contains(x, y):
                    self.toggle_choice("side", button_object.text, removing)
                    return


        if self.clear_button.contains(x, y):
            self.clear_order()
            return
        if self.cancel_button.contains(x, y):
            self.stop_building()
            return
        if self.serve_button.contains(x, y):
            self.serve_customer()
            return