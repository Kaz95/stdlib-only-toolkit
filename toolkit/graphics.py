"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.

TODO:
    * Consider using factory pattern for creating bitmaps in the expected form. Would allow input validation to be a
        type check and remove need for complex custom type.
    * Considering using new and old circle methods as a way to learn a how to benchmark and profile exactly where the
        gains come from.

"""
import collections
import json
import msvcrt
import sys
import time
import urllib.request
from math import sqrt
from typing import Final

type RGB = tuple[int, int, int]
type BITMAP = list[list[RGB]]


class GKS:
    """A class for drawing vector and bitmapped graphics to the terminal.

    Will provide constants, drawing primitives, animation pre-rendering, and custom color palettes. The name GKS is
    a homage to the Graphical Kernel System, the first international standard for low-level 2D computer graphics.
    """
    RESET: Final[str] = "\033[0m"
    CURSOR_TO_TOP: Final[str] = "\x1b[H"
    CLEAR_SCREEN: Final[str] = "\x1b[2J"
    HIDE_CURSOR: Final[str] = "\x1b[?25l"
    SHOW_CURSOR: Final[str] = "\x1b[?25h"
    ENTER_ALT_SCREEN = "\x1b[?1049h"
    EXIT_ALT_SCREEN = "\x1b[?1049l"

    UPPER_BLOCK: Final[str] = '\u2580'  # ▀
    LOWER_BLOCK: Final[str] = '\u2584'  # ▄
    FULL_BLOCK: Final[str] = '\u2588'  # █

    BLACK: Final[RGB] = (0, 0, 0)
    WHITE: Final[RGB] = (255, 255, 255)
    WIDTH: Final[int] = 134
    HEIGHT: Final[int] = 100
    COLOR_PALETTE_1 = {0: (0, 255, 0), 1: WHITE}
    COLOR_PALETTE_2 = {0: (0, 255, 255), 1: (255, 0, 0)}
    COLOR_PALETTE_3 = {0: (0, 0, 255), 1: (255, 255, 0)}
    CURRENT_PALETTE = COLOR_PALETTE_1

    REMOTE_FONT_URL: Final[str] = (r'https://raw.githubusercontent.com/Kaz95/stdlib-only-toolkit/refs/heads/dev/assets'
                                   r'/fonts/font8x8.json')

    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        """Initialize video buffer to a blank screen and cast custom height and width(if applicable) to attributes."""
        if width <= 0 or height <= 0:
            raise ValueError(f'Width and height must be positive, got {width} and {height}')
        self.width: int = width
        self.height: int = height
        self.buffer_updated: bool = False
        self.rendering: bool = False
        self.font = self.load_font()
        self.video_buffer: list[list[RGB | int]] = [[(0, 0, 0)] * self.width for _ in range(self.height)]

    def clear(self) -> None:
        """Clear video buffer in place."""
        for y in range(len(self.video_buffer)):
            for x in range(len(self.video_buffer[y])):
                self.video_buffer[y][x] = self.BLACK

    def set_pixel(self, x: int, y: int, color: int | RGB = WHITE) -> None:
        """Set a single pixels color."""
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            raise ValueError(f'Point: ({x}, {y}) is no within video buffer dimensions: {self.width}x{self.height}')

        self.video_buffer[y][x] = color
        self.buffer_updated = True

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: int | RGB = WHITE) -> None:
        """Draw a line between two points, using a given color."""
        delta_of_x = x2 - x1
        delta_of_y = y2 - y1

        # If vertical line
        if delta_of_x == 0:
            step = 1 if y2 >= y1 else -1
            for y in range(y1, y2 + step, step):
                self.set_pixel(x1, y, color)
            return

        m = delta_of_y / delta_of_x
        b = y1 - m * x1

        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            y = round(m * x + b)
            self.set_pixel(x, y, color)

    def draw_bresenhams_line(self, x1: int, y1: int, x2: int, y2: int, color: int | RGB = WHITE) -> None:
        """Draw a line between two points, using a given color.

        Somehow harder to understand than circle midpoint. This wasn't too hard to implement, but hard to really
        understand it. There's a lot going on for such a compact algorithm. This one was really easy for me to
        conceptualize from a programming point of view, but the math made it seem much more confusing than it really is.
        Cool algorithm. Thank you, Mr. Bresenham.
        """
        # Compute deltas
        # Use absolute values of the deltas. Only care about offset. Step direction handles rest.
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        # Determine step directions for x, y
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1

        # Set initial midpoint/decision value
        # This could be: param = dy - dx, and I'd just change the direction of the threshold tests.
        # This messed with me for a while, but I'm pretty sure I could do < dy and > -dx if the param were reversed.
        running_decision_parameter = dx - dy

        while True:
            self.set_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break

            temp_decision_parameter = 2 * running_decision_parameter

            # Understanding why -dy and dx act as decision thresholds took longer to understand than circle midpoint.
            # Not to self: It's because the deltas(slope) represent the ratio of movement on an ideal line.
            # The values can be anything as long as the ratio is maintained.
            # We use -dy as the lower bound because we know it is less than dx.
            # Both dx and dy are absolute values so we can be sure -dy is <= 0, and thus < dx which must be positive.
            # When the decision param crosses a threshold, it's saying the ratio is off, correct in the other direction.
            if temp_decision_parameter > -dy:
                running_decision_parameter -= dy
                x1 += sx

            if temp_decision_parameter < dx:
                running_decision_parameter += dx
                y1 += sy

    def draw_rect(self, x: int, y: int, width: int, height: int, color: int | RGB = WHITE) -> None:
        """Draw a four sided object, of a given color and size, starting at point (x,y)."""
        # Have to subtract one to avoid over running.  Width represents how wide rect is, points included.
        x2 = x + width - 1
        y2 = y + height - 1

        self.draw_line(x, y, x2, y, color)  # Top
        self.draw_line(x, y2, x2, y2, color)  # Bottom
        self.draw_line(x, y, x, y2, color)  # Left
        self.draw_line(x2, y, x2, y2, color)  # Right

    def draw_filled_rect(self, x: int, y: int, width: int, height: int, color: int | RGB = WHITE) -> None:
        """Draw a filled four sided object, of a given color and size, starting at point (x,y).

        Just iterate through every pixel and set it to the given color.
        """
        for row in range(y, y + height):
            for col in range(x, x + width):
                self.set_pixel(col, row, color)

    def old_draw_circle(self, center_x: int, center_y: int, radius: int, color: int | RGB = WHITE) -> None:
        """Draw a circle around center point, starting at point (x,y).

        This is currently using cartesian method based on relationship between x and y. Improvements Soon™.
        """
        for x in range(center_x - radius, center_x + radius + 1):
            delta_of_x = x - center_x

            y_offset = sqrt(radius ** 2 - delta_of_x ** 2)

            y1 = round(center_y - y_offset)
            y2 = round(center_y + y_offset)

            self.set_pixel(x, y1, color)
            self.set_pixel(x, y2, color)

    def new_draw_circle(self, center_x: int, center_y: int, radius: int, color: int | RGB = WHITE) -> None:
        """Draw a circle around the center point, starting at point (x,y).

        Implements classic circle midpoint algorithm. Finds points using trig instead of algebraic method.
        Uses integer arithmetic to calculate difference of squares and keeps a running tab to avoid recalculating at
        each step. Only calculates one octant between 90° and 45°, then takes advantage of the symmetry of a circle to
        find the coordinates of the other seven octants. The entire algo uses normal cartesian coordinates for depicting
        (x,y) and is converted to screen coordinates before drawing the pixel.

        Implementing this almost feels like cheating. This is so much better than anything I'd ever come up with alone.
        I spent most of my time understanding the math behind it, so I could understand the efficiency gains. I've never
        implemented a well known algorithm like this and that seemed like the most important thing to understand.
        Bresenham is a genius, and we are all standing on the backs of giants.
        """
        # start at 90°
        x = 0
        y = radius

        # Keeps track of running midpoint. Starts at 1-raidus instead of exact midpoint to stick to integer arithmetic.
        running_decision_parameter = 1 - radius

        while x <= y:
            # 8-way symmetry
            # It took me forever to wrap my head around the final conversion to screen coordinates
            self.set_pixel(center_x + x, center_y + y, color)
            self.set_pixel(center_x - x, center_y + y, color)
            self.set_pixel(center_x + x, center_y - y, color)
            self.set_pixel(center_x - x, center_y - y, color)

            self.set_pixel(center_x + y, center_y + x, color)
            self.set_pixel(center_x - y, center_y + x, color)
            self.set_pixel(center_x + y, center_y - x, color)
            self.set_pixel(center_x - y, center_y - x, color)

            if running_decision_parameter < 0:
                # Choose East
                running_decision_parameter += 2 * x + 3
            else:
                # Choose South-East
                y -= 1
                running_decision_parameter += 2 * (x - y) + 5

            x += 1

    def draw_filled_circle(self, center_x: int, center_y: int, radius: int, color: int | RGB = WHITE) -> None:
        """Draw a filled circle around center point, starting at point (x,y).

        Decided to start with the most obvious version. I know I can do better based on what I learned with circle
        midpoint.
        """
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius, center_x + radius + 1):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    self.set_pixel(x, y, color)

    def draw_filled_circle_span(self, center_x: int, center_y: int, radius: int, color: int | RGB = WHITE) -> None:
        """Draw a filled circle around center point, starting at point (x,y).

        Another pretty easy one. Just isolate x. I'll learn the blended circle midpoint/span method eventually, but
        I need to focus on other parts of the project. I've got plenty of CPU, can't waste time on this sadly.
        """
        for y in range(center_y - radius, center_y + radius + 1):
            dy = y - center_y
            x_offset = sqrt(radius ** 2 - dy ** 2)
            left = round(center_x - x_offset)
            right = round(center_x + x_offset)

            for x in range(left, right + 1):
                self.set_pixel(x, y, color)

    def draw_sprite(self, x: int, y: int, sprite_data):
        """Draw sprite from given data, starting at point (x,y)."""
        pass

    def blit(self, bitmap: BITMAP , x_start: int = 0, y_start: int = 0) -> None:
        """Replace the frame buffer with given bitmap using slice replacement(memmove)."""

        bitmap_height = len(bitmap)
        bitmap_width = len(bitmap[0])

        if (
                x_start < 0
                or y_start < 0
                or x_start + bitmap_width > self.width
                or y_start + bitmap_height > self.height
        ):
            raise ValueError('Bitmap does not fit')

        for row_index, row in enumerate(bitmap):
            self.video_buffer[y_start + row_index][x_start:x_start + bitmap_width] = row

    def draw_frame(self) -> None:
        """Draw a single frame to the terminal."""
        sys.stdout.write(self.CURSOR_TO_TOP)
        for y in range(0, self.height, 2):
            line_buffer = []
            for x in range(self.width):
                top = self.video_buffer[y][x]
                bottom = self.video_buffer[y + 1][x] if y + 1 < self.height else self.BLACK
                if isinstance(top, int):
                    top = self.CURRENT_PALETTE[top]
                if isinstance(bottom, int):
                    bottom = self.CURRENT_PALETTE[bottom]

                bg_ansi = f"\x1b[48;2;{top[0]};{top[1]};{top[2]}m"
                fg_ansi = f"\x1b[38;2;{bottom[0]};{bottom[1]};{bottom[2]}m"

                line_buffer.append(f"{bg_ansi}{fg_ansi}{self.LOWER_BLOCK}")

            sys.stdout.write(''.join(line_buffer) + self.RESET + '\n')
            sys.stdout.flush()

    class CommandHandler:
        """Command Handler Factory.

        I've never written anything quite like this, and I'm not really sure where I want to put it yet.
        """
        def __init__(self):
            pass

        def handle(self, key):
            """Handle a keypress."""
            pass

    def start_render_loop(self, frame_rate: int, command_handler=None) -> None:
        """Initiate the main render loop.

        This controls frame pacing, user input listening, and rendering. New frame is only rendered if update flag is
        set. A command handler may be omitted for graphics-only render loops.
        """
        try:
            sys.stdout.write(self.HIDE_CURSOR)
            sys.stdout.write(self.CLEAR_SCREEN)
            frame_duration = 1 / frame_rate
            self.rendering = True
            while self.rendering:
                start_time = time.perf_counter()
                if command_handler is not None and msvcrt.kbhit():
                    key = msvcrt.getwch()
                    command_handler.handle(key)

                if self.buffer_updated:
                    self.draw_frame()
                    self.buffer_updated = False

                elapsed_time = time.perf_counter() - start_time
                sleep_time = frame_duration - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        finally:
            sys.stdout.write(self.SHOW_CURSOR)


    def load_font(self) -> dict[str, list[int]]:
        """Load remote font and cast hex strings to int."""
        with urllib.request.urlopen(self.REMOTE_FONT_URL) as response:
            font_set_as_hex_str = json.load(response)
            font_set_as_hex_int = {char: [int(hex_str, 16) for hex_str in rows] for char, rows in
                                   font_set_as_hex_str.items()}
            return font_set_as_hex_int

    @staticmethod
    def get_pixel(row: int, bit_index: int, width: int = 8) -> int:
        """Isolate a single bit from a given integer, use an AND mask to capture it, and return it.

        Bit index must be valid.
        """
        if bit_index >= width or bit_index < 0:
            raise ValueError('Bit index out of range')

        return (row >> (width - 1 - bit_index)) & 1

    def draw_chars(self, word: str, x_start: int, y_start: int, color: RGB = WHITE):
        """Draw chars from given word, using built-in font, starting at point (x,y)."""
        word = word.upper()
        unsupported_characters = [char for char in word if char not in self.font]
        if unsupported_characters:
            raise ValueError(f'Character not available in font: {unsupported_characters[0]!r}')

        glyph_data = [self.font[char] for char in word]

        for _ in range(len(glyph_data)):
            a_glyph = glyph_data.pop(0)

            for y in range(0, len(a_glyph), 2):
                for x in range(8):

                    top = self.get_pixel(a_glyph[y], x)
                    bottom = self.get_pixel(a_glyph[y + 1], x)

                    if top:
                        self.set_pixel(x_start + x, y_start + y, color)
                    if bottom:
                        self.set_pixel(x_start + x, y_start + y + 1, color)

            x_start += 8

    def draw_centered_chars(self, word: str, y: int, color: RGB = WHITE):
        """Draw center aligned characters. Centered within canvas total width."""
        x_offset = (self.width - (len(word) * 8)) // 2

        self.draw_chars(word, x_offset, y, color)


if __name__ == '__main__':
    gks = GKS()
    sys.stdout.write(gks.ENTER_ALT_SCREEN)
    sys.stdout.write(gks.HIDE_CURSOR)
    palettes = collections.deque([gks.COLOR_PALETTE_1, gks.COLOR_PALETTE_2, gks.COLOR_PALETTE_3])
    # for x in range(20, 41):
    #     for y in range(20, 41):
    #         gks.set_pixel(x, y, 1)
    #
    # for x in range(50, 71):
    #     for y in range(50, 71):
    #         gks.set_pixel(x, y, 0)
    gks.draw_rect(50, 50, 20, 20, 1)
    gks.draw_filled_rect(55, 55, 10, 10, 0)
    gks.draw_frame()
    try:
        while True:
            time.sleep(1.5)
            palettes.rotate(1)
            gks.CURRENT_PALETTE = palettes[0]
            gks.draw_frame()
    finally:
        sys.stdout.write(gks.SHOW_CURSOR)
        sys.stdout.write(gks.EXIT_ALT_SCREEN)
    # gks.set_pixel(-2, 4)
    # gks.draw_filled_rect(40, 40, 20, 20, 1)

