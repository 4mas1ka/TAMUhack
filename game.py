import math
import random


import arcade


from customer import Customer
from order import Order, generate_order
from ingredients import FLAVORS, TOPPINGS, VESSELS, SIDES




SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Rev's Creamery"


MAX_CUSTOMERS = 3
ORDERS_PER_ROUND = 5
FAST_TIME = 60
ARRIVAL_GAP = 8
WIN_AVERAGE = 2.5


# How many scoops you may stack at each difficulty.
MAX_SCOOPS = {1: 1, 2: 2, 3: 2}
# You can add several of the same flavor / topping, up to these limits.
MAX_EACH_FLAVOR = 2
MAX_EACH_TOPPING = 3


CUSTOMER_NAMES = ["Maya", "Tobi", "Akari", "Jordan", "Noor", "Rev", "Kai", "Avery"]


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
        self.background_color = arcade.color.LIGHT_BLUE


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


        # The order being built, plus the order things were added in. The
        # stacks drive the live picture so scoops pile up in the order you
        # add them (the Counters in player_order are what gets scored).
        self.player_order = Order()
        self.scoop_stack = []
        self.topping_stack = []


        self.create_buttons()


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
            600, 250, 220, 70, "START", arcade.color.LIGHT_GREEN, font_size=20
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


    def start_round(self):
        self.customers = []
        self.customers_created = 0
        self.orders_completed = 0
        self.scores = []
        self.selected_customer = None
        self.reset_build()
        self.building_order = False
        self.message = ""
        self.game_state = "PLAYING"
        self.add_customer()
        self.spawn_timer = ARRIVAL_GAP


    def active_customers(self):
        return [customer for customer in self.customers if customer.is_active]


    def add_customer(self):
        if self.customers_created >= ORDERS_PER_ROUND:
            return
        active = self.active_customers()
        if len(active) >= MAX_CUSTOMERS:
            return


        positions = [200, 400, 600]
        used_positions = [customer.target_x for customer in active]
        available_positions = [p for p in positions if p not in used_positions]
        if not available_positions:
            return


        taken_names = [customer.name for customer in active]
        free_names = [name for name in CUSTOMER_NAMES if name not in taken_names]


        customer = Customer(
            name=random.choice(free_names or CUSTOMER_NAMES),
            order=generate_order(self.difficulty),
            target_x=available_positions[0],
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


    def add_flavor(self, flavor):
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
        self.scores.append(stars)
        self.orders_completed += 1


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
        self.check_round_finished()


    def customer_timed_out(self, customer):
        customer.stars = 0
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
        if self.orders_completed >= ORDERS_PER_ROUND:
            self.game_state = "RESULTS"
            return
        self.spawn_timer = 1


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


        for customer in self.customers:
            customer.walk_to_counter(delta_time)
            customer.leave_shop(delta_time)
            customer.update_timer(delta_time)
            if customer.has_timed_out:
                self.customer_timed_out(customer)


        if self.customers_created < ORDERS_PER_ROUND and len(self.active_customers()) < MAX_CUSTOMERS:
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
        arcade.draw_text("REV'S CREAMERY", 600, 500, arcade.color.WHITE, 55, anchor_x="center")
        arcade.draw_text("Beachside Ice Cream Shop", 600, 430, arcade.color.WHITE, 24, anchor_x="center")
        self.start_button.draw()


    def draw_shop(self):
        arcade.draw_rect_filled(arcade.XYWH(600, 550, 1200, 300), arcade.color.SKY_BLUE)
        arcade.draw_rect_filled(arcade.XYWH(600, 390, 1200, 120), arcade.color.BLUE_GREEN)
        arcade.draw_rect_filled(arcade.XYWH(600, 250, 1200, 180), arcade.color.TAN)


        if self.building_order:
            self.draw_split_screen()
        else:
            self.draw_customers()
            if self.selected_customer and self.selected_customer.order_taken:
                self.draw_ticket(self.selected_customer, 600, 560, 650, 170, 13, 19)
                self.build_button.draw()


        # Header goes last so it always sits on top and is never covered.
        arcade.draw_text("REV'S CREAMERY", 25, 658, arcade.color.WHITE, 26, bold=True)
        arcade.draw_text(
            f"Difficulty: {self.difficulty}     Orders: {self.orders_completed}/{ORDERS_PER_ROUND}",
            1175,
            664,
            arcade.color.WHITE,
            16,
            anchor_x="right",
            bold=True,
        )


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


    def draw_customers(self):
        arcade.draw_rect_filled(arcade.XYWH(600, 240, 1200, 120), arcade.color.LIGHT_BROWN)


        for customer in self.active_customers():
            if customer is self.selected_customer:
                arcade.draw_circle_outline(customer.x, customer.y, 58, arcade.color.YELLOW, 5)


            arcade.draw_circle_filled(customer.x, customer.y, 45, arcade.color.PINK)
            arcade.draw_text(customer.name, customer.x, customer.y + 60, arcade.color.WHITE, 15, anchor_x="center")


            if customer.is_waiting_to_order:
                arcade.draw_text("ORDER?", customer.x, customer.y - 70, arcade.color.YELLOW, 14, anchor_x="center")
            elif customer.is_waiting_for_food:
                self.draw_timer_bar(customer, customer.x, customer.y - 75)


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


        arcade.draw_circle_filled(65, 605, 30, arcade.color.PINK)
        arcade.draw_circle_outline(65, 605, 30, arcade.color.BLACK, 2)
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
            "Left-click = add     Right-click or [ - ] = remove",
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


        self.cancel_button.draw()
        self.clear_button.draw()
        self.serve_button.draw()


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


    def draw_timer_bar(self, customer, x, y, width=170):
        arcade.draw_rect_filled(arcade.XYWH(x, y, width, 15), arcade.color.DARK_GRAY)


        if customer.patience_level == "good":
            color = arcade.color.GREEN
        elif customer.patience_level == "warning":
            color = arcade.color.ORANGE
        else:
            color = arcade.color.RED


        if customer.timer_fraction > 0:
            arcade.draw_rect_filled(
                arcade.LBWH(x - width / 2, y - 7.5, width * customer.timer_fraction, 15),
                color,
            )


        arcade.draw_text(f"{int(customer.time_left)} sec", x, y - 30, arcade.color.BLACK, 12, anchor_x="center")


    # ---------------- RESULTS ----------------
    def draw_results(self):
        average = self.average_score()
        arcade.draw_text("ROUND COMPLETE!", 600, 530, arcade.color.WHITE, 45, anchor_x="center")
        arcade.draw_text(f"Average: {average:.2f} / 3.00", 600, 430, arcade.color.WHITE, 28, anchor_x="center")
        arcade.draw_text(f"Total Stars: {sum(self.scores)} / 15", 600, 380, arcade.color.WHITE, 20, anchor_x="center")
        self.retry_button.draw()
        if average >= WIN_AVERAGE:
            self.upgrade_button.draw()


    def draw_trophy(self):
        arcade.draw_text("GOLDEN SCOOP TROPHY!", 600, 450, arcade.color.GOLD, 40, anchor_x="center")
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
            for customer in self.active_customers():
                # Customers who are walking in or out can't be picked.
                if not (customer.is_waiting_to_order or customer.is_waiting_for_food):
                    continue
                distance = (x - customer.x) ** 2 + (y - customer.y) ** 2
                if distance <= 65 ** 2:
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
