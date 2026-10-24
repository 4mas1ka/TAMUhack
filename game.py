import random
import arcade

from customer import Customer
from order import Order, generate_order
from ingredients import FLAVORS, TOPPINGS, SIDES


# ========================================
# GAME SETTINGS
# ========================================

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Rev's Creamery"

MAX_CUSTOMERS = 3
ORDERS_PER_ROUND = 5

ORDER_TIME = 90
FAST_TIME = 60

CUSTOMER_SPEED = 250


CUSTOMER_NAMES = [
    "Maya",
    "Tobi",
    "Akari",
    "Jordan",
    "Noor",
    "Rev",
    "Kai",
    "Avery"
]


# ========================================
# BUTTON
# ========================================

class Button:

    def __init__(self, x, y, width, height, text):

        self.x = x
        self.y = y

        self.width = width
        self.height = height

        self.text = text


    def contains(self, mouse_x, mouse_y):

        return (
            self.x - self.width / 2
            <= mouse_x
            <= self.x + self.width / 2
            and
            self.y - self.height / 2
            <= mouse_y
            <= self.y + self.height / 2
        )


    def draw(self, selected=False):

        if selected:
            color = arcade.color.LIGHT_GREEN
        else:
            color = arcade.color.LIGHT_GRAY

        arcade.draw_rect_filled(
            arcade.XYWH(
                self.x,
                self.y,
                self.width,
                self.height
            ),
            color
        )

        arcade.draw_text(
            self.text,
            self.x,
            self.y,
            arcade.color.BLACK,
            14,
            anchor_x="center",
            anchor_y="center"
        )


# ========================================
# MAIN GAME
# ========================================

class CreameryGame(arcade.Window):

    def __init__(self):

        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE
        )

        self.background_color = arcade.color.LIGHT_BLUE

        # Current screen
        self.game_state = "START"

        # Difficulty starts at easy
        self.difficulty = 1

        # Customer information
        self.customers = []
        self.customers_created = 0

        # Score information
        self.scores = []
        self.orders_completed = 0

        # Currently selected customer
        self.selected_customer = None

        # What the player has built
        self.player_order = Order()

        # Message displayed after serving
        self.message = ""

        # Delay before another customer appears
        self.spawn_timer = 0

        # Create buttons
        self.create_buttons()


    # ========================================
    # BUTTON SETUP
    # ========================================

    def create_buttons(self):

        self.start_button = Button(
            600,
            250,
            220,
            70,
            "START"
        )

        self.build_button = Button(
            1050,
            80,
            180,
            60,
            "BUILD ORDER"
        )

        self.back_button = Button(
            100,
            650,
            140,
            50,
            "BACK"
        )

        self.serve_button = Button(
            1050,
            80,
            180,
            60,
            "SERVE"
        )

        self.retry_button = Button(
            450,
            220,
            180,
            60,
            "TRY AGAIN"
        )

        self.upgrade_button = Button(
            750,
            220,
            220,
            60,
            "NEXT DIFFICULTY"
        )

        # -------------------------
        # Flavor buttons
        # -------------------------

        self.flavor_buttons = []

        for i, flavor in enumerate(FLAVORS):

            button = Button(
                170 + i * 280,
                500,
                220,
                55,
                flavor
            )

            self.flavor_buttons.append(button)

        # -------------------------
        # Topping buttons
        # -------------------------

        self.topping_buttons = []

        for i, topping in enumerate(TOPPINGS):

            button = Button(
                130 + i * 235,
                350,
                205,
                55,
                topping
            )

            self.topping_buttons.append(button)

        # -------------------------
        # Side buttons
        # -------------------------

        self.side_buttons = []

        for i, side in enumerate(SIDES):

            button = Button(
                300 + i * 300,
                200,
                200,
                55,
                side
            )

            self.side_buttons.append(button)


    # ========================================
    # START A ROUND
    # ========================================

    def start_round(self):

        self.customers = []
        self.customers_created = 0

        self.scores = []
        self.orders_completed = 0

        self.selected_customer = None

        self.player_order = Order()

        self.message = ""

        self.spawn_timer = 0

        self.game_state = "ORDER"

        # Immediately add the first customer
        self.add_customer()


    # ========================================
    # CUSTOMERS
    # ========================================

    def get_active_customers(self):

        return [
            customer
            for customer in self.customers
            if not customer.finished
        ]


    def add_customer(self):

        # We only want five customers per round
        if self.customers_created >= ORDERS_PER_ROUND:
            return

        active = self.get_active_customers()

        # Never have more than three at once
        if len(active) >= MAX_CUSTOMERS:
            return

        # Determine where this customer should stand
        target_positions = [
            300,
            600,
            900
        ]

        used_positions = [
            customer.target_x
            for customer in active
        ]

        available_positions = [
            position
            for position in target_positions
            if position not in used_positions
        ]

        if not available_positions:
            return

        target_x = available_positions[0]

        customer = Customer(
            name=random.choice(CUSTOMER_NAMES),
            order=generate_order(self.difficulty),
            target_x=target_x
        )

        self.customers.append(customer)

        self.customers_created += 1


    # ========================================
    # TIMER
    # ========================================

    def update_customer_timers(self, delta_time):

        for customer in self.get_active_customers():

            customer.time_left -= delta_time

            if customer.time_left <= 0:

                customer.time_left = 0

                customer.stars = 1

                customer.finished = True

                self.scores.append(1)

                self.orders_completed += 1

                self.message = (
                    f"{customer.name} ran out of time! 1 star"
                )

                if self.selected_customer == customer:
                    self.selected_customer = None

                self.check_round_finished()


    # ========================================
    # CUSTOMER MOVEMENT
    # ========================================

    def move_customers(self, delta_time):

        for customer in self.get_active_customers():

            if customer.x > customer.target_x:

                customer.x -= CUSTOMER_SPEED * delta_time

                if customer.x < customer.target_x:
                    customer.x = customer.target_x


    # ========================================
    # ORDER CHECKING
    # ========================================

    def order_is_correct(self, customer):

        return customer.order.matches(
            self.player_order
        )


    # ========================================
    # SCORING
    # ========================================

    def calculate_score(self, customer, correct):

        if not correct:
            return 1

        time_used = (
            ORDER_TIME - customer.time_left
        )

        # Correct and completed within first minute
        if time_used <= FAST_TIME:
            return 3

        # Correct but took longer than one minute
        return 2


    # ========================================
    # SERVING
    # ========================================

    def serve_customer(self):

        if self.selected_customer is None:

            self.message = (
                "Select a customer first!"
            )

            return

        customer = self.selected_customer

        correct = self.order_is_correct(
            customer
        )

        stars = self.calculate_score(
            customer,
            correct
        )

        customer.stars = stars
        customer.finished = True

        self.scores.append(stars)

        self.orders_completed += 1

        if correct:

            if stars == 3:
                mood = "Happy!"

            else:
                mood = "Satisfied!"

        else:
            mood = "Wrong order!"

        self.message = (
            f"{customer.name}: "
            f"{mood} "
            f"{stars} star(s)"
        )

        # Reset player's food
        self.player_order = Order()

        self.selected_customer = None

        self.game_state = "ORDER"

        self.check_round_finished()


    # ========================================
    # CHECK ROUND
    # ========================================

    def check_round_finished(self):

        if self.orders_completed >= ORDERS_PER_ROUND:

            self.game_state = "RESULTS"

            return

        # If there's room, another customer can enter
        self.spawn_timer = 1


    # ========================================
    # AVERAGE
    # ========================================

    def get_average_score(self):

        if not self.scores:
            return 0

        return (
            sum(self.scores)
            / len(self.scores)
        )


    # ========================================
    # DIFFICULTY
    # ========================================

    def upgrade_difficulty(self):

        if self.difficulty < 3:

            self.difficulty += 1

            self.start_round()

        else:

            self.game_state = "TROPHY"


    # ========================================
    # DRAW
    # ========================================

    def on_draw(self):

        self.clear()

        if self.game_state == "START":

            self.draw_start_screen()

        elif self.game_state == "ORDER":

            self.draw_order_station()

        elif self.game_state == "BUILD":

            self.draw_build_station()

        elif self.game_state == "RESULTS":

            self.draw_results_screen()

        elif self.game_state == "TROPHY":

            self.draw_trophy_screen()


    # ========================================
    # START SCREEN
    # ========================================

    def draw_start_screen(self):

        arcade.draw_text(
            "REV'S CREAMERY",
            SCREEN_WIDTH / 2,
            500,
            arcade.color.WHITE,
            55,
            anchor_x="center"
        )

        arcade.draw_text(
            "Beachside Ice Cream Shop",
            SCREEN_WIDTH / 2,
            430,
            arcade.color.WHITE,
            24,
            anchor_x="center"
        )

        arcade.draw_text(
            "Serve 5 customers and earn as many stars as possible!",
            SCREEN_WIDTH / 2,
            360,
            arcade.color.WHITE,
            18,
            anchor_x="center"
        )

        self.start_button.draw()


    # ========================================
    # ORDER STATION
    # ========================================

    def draw_order_station(self):

        arcade.draw_text(
            "ORDER STATION",
            40,
            650,
            arcade.color.WHITE,
            28
        )

        arcade.draw_text(
            f"Difficulty: {self.difficulty}",
            1000,
            655,
            arcade.color.WHITE,
            18
        )

        arcade.draw_text(
            f"Orders: {self.orders_completed}/{ORDERS_PER_ROUND}",
            1000,
            620,
            arcade.color.WHITE,
            16
        )

        # Draw a temporary counter
        arcade.draw_rect_filled(
            arcade.XYWH(
                600,
                170,
                1200,
                180
            ),
            arcade.color.LIGHT_BROWN
        )

        # Draw customers
        for customer in self.get_active_customers():

            # Selected customer gets a yellow ring
            if customer == self.selected_customer:

                arcade.draw_circle_outline(
                    customer.x,
                    customer.y,
                    65,
                    arcade.color.YELLOW,
                    5
                )

            # Temporary customer head/body
            arcade.draw_circle_filled(
                customer.x,
                customer.y,
                48,
                arcade.color.PINK
            )

            arcade.draw_text(
                customer.name,
                customer.x,
                customer.y + 65,
                arcade.color.WHITE,
                17,
                anchor_x="center"
            )

            arcade.draw_text(
                f"{int(customer.time_left)} sec",
                customer.x,
                customer.y - 80,
                arcade.color.WHITE,
                14,
                anchor_x="center"
            )

        # Draw order ticket if customer selected
        if self.selected_customer is not None:

            customer = self.selected_customer

            arcade.draw_rect_filled(
                arcade.XYWH(
                    600,
                    555,
                    620,
                    145
                ),
                arcade.color.WHITE
            )

            arcade.draw_text(
                f"{customer.name}'s Order",
                320,
                590,
                arcade.color.BLACK,
                18
            )

            arcade.draw_text(
                f"Flavor: {customer.order.flavor}",
                320,
                555,
                arcade.color.BLACK,
                15
            )

            topping_text = ", ".join(
                sorted(customer.order.toppings)
            )

            arcade.draw_text(
                f"Toppings: {topping_text}",
                320,
                525,
                arcade.color.BLACK,
                15
            )

            arcade.draw_text(
                f"Side: {customer.order.side}",
                320,
                495,
                arcade.color.BLACK,
                15
            )

            self.build_button.draw()

        if self.message:

            arcade.draw_text(
                self.message,
                SCREEN_WIDTH / 2,
                40,
                arcade.color.WHITE,
                18,
                anchor_x="center"
            )


    # ========================================
    # BUILD STATION
    # ========================================

    def draw_build_station(self):

        arcade.draw_text(
            "BUILD STATION",
            SCREEN_WIDTH / 2,
            650,
            arcade.color.WHITE,
            30,
            anchor_x="center"
        )

        self.back_button.draw()

        # -------------------------
        # FLAVORS
        # -------------------------

        arcade.draw_text(
            "1. Choose a flavor",
            40,
            555,
            arcade.color.WHITE,
            20
        )

        for button in self.flavor_buttons:

            selected = (
                self.player_order.flavor
                == button.text
            )

            button.draw(selected)


        # -------------------------
        # TOPPINGS
        # -------------------------

        arcade.draw_text(
            "2. Choose toppings",
            40,
            405,
            arcade.color.WHITE,
            20
        )

        for button in self.topping_buttons:

            selected = (
                button.text
                in self.player_order.toppings
            )

            button.draw(selected)


        # -------------------------
        # SIDES
        # -------------------------

        arcade.draw_text(
            "3. Choose a side",
            40,
            255,
            arcade.color.WHITE,
            20
        )

        for button in self.side_buttons:

            selected = (
                self.player_order.side
                == button.text
            )

            button.draw(selected)


        # -------------------------
        # CURRENT BUILD
        # -------------------------

        flavor = (
            self.player_order.flavor
            or "None"
        )

        toppings = ", ".join(
            sorted(self.player_order.toppings)
        )

        if not toppings:
            toppings = "None"

        side = (
            self.player_order.side
            or "None"
        )

        arcade.draw_text(
            f"Current order: {flavor} | {toppings} | {side}",
            40,
            100,
            arcade.color.WHITE,
            15
        )

        self.serve_button.draw()


    # ========================================
    # RESULTS
    # ========================================

    def draw_results_screen(self):

        average = self.get_average_score()

        arcade.draw_text(
            "ROUND COMPLETE!",
            SCREEN_WIDTH / 2,
            520,
            arcade.color.WHITE,
            45,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Difficulty {self.difficulty}",
            SCREEN_WIDTH / 2,
            455,
            arcade.color.WHITE,
            22,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Average Score: {average:.1f} / 3",
            SCREEN_WIDTH / 2,
            400,
            arcade.color.WHITE,
            26,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Total Stars: {sum(self.scores)} / 15",
            SCREEN_WIDTH / 2,
            350,
            arcade.color.WHITE,
            20,
            anchor_x="center"
        )

        self.retry_button.draw()

        if self.difficulty < 3:

            self.upgrade_button.draw()

        else:

            trophy_button_text = "GET TROPHY"

            self.upgrade_button.text = trophy_button_text

            self.upgrade_button.draw()


    # ========================================
    # TROPHY SCREEN
    # ========================================

    def draw_trophy_screen(self):

        arcade.draw_text(
            "REV'S CREAMERY",
            SCREEN_WIDTH / 2,
            530,
            arcade.color.WHITE,
            50,
            anchor_x="center"
        )

        arcade.draw_text(
            "TROPHY UNLOCKED!",
            SCREEN_WIDTH / 2,
            430,
            arcade.color.GOLD,
            38,
            anchor_x="center"
        )

        arcade.draw_text(
            "You completed every difficulty!",
            SCREEN_WIDTH / 2,
            350,
            arcade.color.WHITE,
            22,
            anchor_x="center"
        )

        # Temporary trophy
        arcade.draw_circle_filled(
            SCREEN_WIDTH / 2,
            230,
            70,
            arcade.color.GOLD
        )


    # ========================================
    # UPDATE
    # ========================================

    def on_update(self, delta_time):

        if self.game_state not in [
            "ORDER",
            "BUILD"
        ]:
            return

        # Timers continue while building
        self.update_customer_timers(
            delta_time
        )

        self.move_customers(
            delta_time
        )

        # Spawn customers over time
        if self.game_state == "ORDER":

            if (
                self.customers_created
                < ORDERS_PER_ROUND
            ):

                if (
                    len(self.get_active_customers())
                    < MAX_CUSTOMERS
                ):

                    self.spawn_timer -= delta_time

                    if self.spawn_timer <= 0:

                        self.add_customer()

                        self.spawn_timer = 5


    # ========================================
    # MOUSE CLICKS
    # ========================================

    def on_mouse_press(
        self,
        x,
        y,
        button,
        modifiers
    ):

        # -------------------------
        # START
        # -------------------------

        if self.game_state == "START":

            if self.start_button.contains(x, y):

                self.start_round()

            return


        # -------------------------
        # ORDER STATION
        # -------------------------

        if self.game_state == "ORDER":

            # Check if player clicked customer
            for customer in self.get_active_customers():

                distance_x = x - customer.x
                distance_y = y - customer.y

                distance_squared = (
                    distance_x ** 2
                    + distance_y ** 2
                )

                if distance_squared <= 65 ** 2:

                    self.selected_customer = customer

                    self.message = (
                        f"Selected {customer.name}"
                    )

                    return

            # Go to build station
            if (
                self.selected_customer is not None
                and self.build_button.contains(x, y)
            ):

                self.player_order = Order()

                self.game_state = "BUILD"

                return


        # -------------------------
        # BUILD STATION
        # -------------------------

        elif self.game_state == "BUILD":

            # Back button
            if self.back_button.contains(x, y):

                self.game_state = "ORDER"

                return


            # Flavor buttons
            for button_object in self.flavor_buttons:

                if button_object.contains(x, y):

                    self.player_order.flavor = (
                        button_object.text
                    )

                    return


            # Topping buttons
            for button_object in self.topping_buttons:

                if button_object.contains(x, y):

                    topping = button_object.text

                    if (
                        topping
                        in self.player_order.toppings
                    ):

                        self.player_order.toppings.remove(
                            topping
                        )

                    else:

                        self.player_order.toppings.add(
                            topping
                        )

                    return


            # Side buttons
            for button_object in self.side_buttons:

                if button_object.contains(x, y):

                    self.player_order.side = (
                        button_object.text
                    )

                    return


            # Serve button
            if self.serve_button.contains(x, y):

                self.serve_customer()

                return


        # -------------------------
        # RESULTS
        # -------------------------

        elif self.game_state == "RESULTS":

            if self.retry_button.contains(x, y):

                self.start_round()

                return

            if self.upgrade_button.contains(x, y):

                self.upgrade_difficulty()

                return