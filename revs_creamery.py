import arcade

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
SCREEN_TITLE = "Rev's Creamery"


class CreameryGame(arcade.Window):

    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE
        )

        self.background_color = arcade.color.LIGHT_PINK

    def on_draw(self):
        self.clear()

        arcade.draw_text(
            "REV'S CREAMERY",
            SCREEN_WIDTH / 2,
            600,
            arcade.color.WHITE,
            40,
            anchor_x="center"
        )


def main():
    game = CreameryGame()
    arcade.run()


if __name__ == "__main__":
    main()