"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.

TODO:
    * Consider using factory pattern for creating bitmaps in the expected form. Would allow input validation to be a
        type check and remove need for complex custom type.
    * Decide how the UI model will trigger UI view updates. Maybe I can use observer pattern here. Maybe on vbuffer update
        check too.
    * Considering using new and old circle methods as a way to learn a how to benchmark and profile exactly where the
        gains come from.

"""
import json
import time
import urllib.request
from enum import Enum, auto
from typing import Final
from collections.abc import Callable
from dataclasses import dataclass
import sys
from math import sqrt
from pprint import pp, pprint

import msvcrt

type RGB = tuple[int, int, int]

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

    UPPER_BLOCK: Final[str] = '\u2580'  # ▀
    LOWER_BLOCK: Final[str] = '\u2584'  # ▄
    FULL_BLOCK: Final[str] = '\u2588'  # █
    BLACK: Final[RGB] = (0, 0, 0)
    WHITE: Final[RGB] = (255, 255, 255)
    WIDTH: Final[int] = 132
    HEIGHT: Final[int] = 100

    # PRE_RENDERED_FRAMES = []

    # BUFFER_ROW = [BLACK] * WIDTH
    # video_buffer = []

    def __init__(self, width: int=WIDTH, height: int=HEIGHT) -> None:
        """Initialize video buffer to a blank screen and cast custom height and width(if applicable) to attributes."""
        self.width: int = width
        self.height: int = height
        self.buffer_updated: bool = False
        self.rendering: bool = False
        self.font = self.load_font()
        self.video_buffer: list[list[RGB]] = [[(0, 0, 0)] * self.width for _ in range(self.height)]

    def clear(self) -> None:
        """Clear video buffer in place."""
        for y in range(len(self.video_buffer)):
            for x in range(len(self.video_buffer[y])):
                self.video_buffer[y][x] = self.BLACK

    def set_pixel(self, x: int, y: int, color: RGB=WHITE) -> None:
        """Set a single pixels color."""
        self.video_buffer[y][x] = color
        self.buffer_updated = True

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: RGB=WHITE) -> None:
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

    def draw_bresenhams_line(self, x1: int, y1: int, x2: int, y2: int, color: RGB=WHITE) -> None:
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

    def draw_rect(self, x: int, y: int, width: int, height: int, color: RGB=WHITE) -> None:
        """Draw a four sided object, of a given color and size, starting at point (x,y)."""
        # Have to subtract one to avoid over running.  Width represents how wide rect is, points included.
        x2 = x + width - 1
        y2 = y + height - 1

        self.draw_line(x, y, x2, y, color)  # Top
        self.draw_line(x, y2, x2, y2, color)  # Bottom
        self.draw_line(x, y, x, y2, color)  # Left
        self.draw_line(x2, y, x2, y2, color)  # Right

    def draw_filled_rect(self, x: int, y: int, width: int, height: int, color: RGB=WHITE) -> None:
        """Draw a filled four sided object, of a given color and size, starting at point (x,y).

        Just iterate through every pixel and set it to the given color.
        """
        for row in range(y, y + height):
            for col in range(x, x + width):
                self.set_pixel(col, row, color)

    def old_draw_circle(self, center_x: int, center_y: int, radius: int, color: RGB=WHITE) -> None:
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

    def new_draw_circle(self, center_x: int, center_y: int, radius: int, color: RGB=WHITE) -> None:
        """Draw a circle around the center point, starting at point (x,y).

        Implements classic circle midpoint algorithm. Finds points using trig instead of algebraic method.
        Uses integer arithmetic to calculate difference of squares and keeps a running tab to avoid recalculating at
        each step. Only calculates one octant between 90° and 45°, then takes advantage of the symmetry of a circle to
        find the coordinates of the other seven octants. The entire algo uses normal cartesian coordinates for depicting
        (x,y) and is converted to screen coordinates before painting the pixel.

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

    def draw_filled_circle(self, center_x: int, center_y: int, radius: int, color: RGB=WHITE) -> None:
        """Draw a filled circle around center point, starting at point (x,y).

        Decided to start with the most obvious version. I know I can do better based on what I learned with circle
        midpoint.
        """
        for y in range(center_y - radius, center_y + radius + 1):
            for x in range(center_x - radius, center_x + radius + 1):
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    self.set_pixel(x, y, color)

    def draw_filled_circle_span(self, center_x: int, center_y: int, radius: int, color: RGB=WHITE) -> None:
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

    def draw_sprite(self, x, y, sprite_data):
        """Draw sprite from given data, starting at point (x,y)."""
        pass

    def blit(self, bitmap, x_start: int=0, y_start:int=0):
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


    def paint_frame(self) -> None:
        """Paint a single frame to the terminal."""
        sys.stdout.write(self.CURSOR_TO_TOP)
        for y in range(0, self.height, 2):
            line_buffer = []
            for x in range(self.width):
                top = self.video_buffer[y][x]
                bottom = self.video_buffer[y + 1][x] if y + 1 < self.height else self.BLACK

                bg_ansi = f"\x1b[48;2;{top[0]};{top[1]};{top[2]}m"
                fg_ansi = f"\x1b[38;2;{bottom[0]};{bottom[1]};{bottom[2]}m"

                line_buffer.append(f"{bg_ansi}{fg_ansi}{self.LOWER_BLOCK}")

            sys.stdout.write(''.join(line_buffer) + self.RESET + '\n')
            sys.stdout.flush()

    def start_render_loop(self, frame_rate: int) -> None:
        """Initiate the main render loop.

        This controls frame pacing, user input listening, and rendering. New frame is only rendered if update flag is
        set.
        """
        sys.stdout.write(self.HIDE_CURSOR)
        sys.stdout.write(self.CLEAR_SCREEN)
        frame_duration = 1 / frame_rate
        self.rendering = True
        while self.rendering:
            start_time = time.perf_counter()
            if msvcrt.kbhit():
                pass
            if self.buffer_updated:
                self.paint_frame()
                self.buffer_updated = False
            elapsed_time = time.perf_counter() - start_time
            sleep_time = frame_duration - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)

    @staticmethod
    def load_font():
        """Load remote font and cast hex strings to int."""
        with urllib.request.urlopen(r'https://raw.githubusercontent.com/Kaz95/stdlib-only-toolkit/refs/heads/dev/assets/fonts/font8x8.json') as response:
            font_set_as_hex_str = json.load(response)
            font_set_as_hex_int = {char: [int(hex_str, 16) for hex_str in rows] for char, rows in font_set_as_hex_str.items()}
            return font_set_as_hex_int

    @staticmethod
    def get_pixel(row: int, bit_index: int, width: int = 8) -> int:
        """Isolate a single bit from a given integer, use an AND mask to capture it, and return it.

        Bit index must be valid.
        """
        if bit_index >= width or bit_index < 0:
            raise ValueError('Bit index out of range')

        return (row >> (width - 1 - bit_index)) & 1

    def paint_chars(self, word: str, x_start: int, y_start: int, color: RGB=WHITE):
        """Paint chars from given word, using built-in font, starting at point (x,y)."""
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


if __name__ == '__main__':
    CENTER_X = 99
    CENTER_Y = 75


    def center_header(header: str, engine: GKS):
        # 7 chars max. Can push to 8 by changing staring x to 2, otherwise first char will touch left boarder.
        # Pushing starting x to 2 results is slightly misaligned glyphs on all lengths < 8
        if len(header) > 7:
            raise ValueError('Header too long')

        starting_x = 1
        starting_y = 3
        usable_width = 64

        length_of_glyphs = len(header) * 8
        centering_offset = (usable_width - length_of_glyphs) // 2

        starting_x += centering_offset

        engine.paint_chars(header, starting_x, starting_y)

    def draw_static_ui(engine):
        # Boarder
        engine.draw_rect(0, 0, 132, 100)

        # Center divider
        engine.draw_line(65, 0, 65, 99)
        engine.draw_line(66, 0, 66, 99)

        # Horizontal midpoint on the right half
        engine.draw_line(66, 49, 131, 49)
        engine.draw_line(66, 50, 131, 50)

        # Header for options section
        engine.draw_line(0, 11, 64, 11)

        # Center HEADER in the top-left header area
        # engine.paint_chars('HEADER', 8, 3)

        center_header('Size', engine)

        # Static selection elements
        engine.draw_rect(47, 22, 16, 15)  # x=47..64, y=22..36
        engine.draw_filled_rect(47, 47, 16, 15)  # x=47..64, y=47..61
        engine.draw_rect(47, 73, 16, 15)  # x=47..64, y=73..87








    def draw_sm_pizza(engine):
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 16, (198, 124, 56))
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 14, (244, 196, 48))

    def draw_md_pizza(engine):
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 19, (198, 124, 56))
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 17, (244, 196, 48))

    def draw_lg_pizza(engine):
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 23, (198, 124, 56))
        engine.draw_filled_circle_span(CENTER_X, CENTER_Y, 20, (244, 196, 48))

    def draw_bpepper(x, y, engine):
        engine.draw_rect(x, y, 4, 1, (34, 136, 0))

    def draw_rpepper(x, y, engine):
        engine.draw_rect(x, y, 4, 1, (205, 28, 24))

    def draw_tofu(x, y, engine):
        engine.draw_filled_rect(x, y, 3, 3, (238, 220, 130))

    def draw_pepperoni(x, y, engine):
        engine.draw_filled_circle(x, y, 2, (255, 0, 0))

    def draw_sausage(x, y, engine):
        engine.draw_filled_circle(x, y, 2, (101, 67, 33))

    def draw_olive(x, y, engine):
        engine.new_draw_circle(x, y, 1, (0, 0, 0))


    class SizeOptions(Enum):
        SMALL = auto()
        MEDIUM = auto()
        LARGE = auto()

    class ProteinOptions(Enum):
        PEPPERONI = auto()
        SAUSAGE = auto()
        TOFU = auto()

    class VegetableOptions(Enum):
        BELL_PEPPERS = auto()
        RED_PEPPERS = auto()
        BLACK_OLIVES = auto()

    @dataclass(frozen=True, slots=True)
    class SizeOption:
        cost: int
        description: str
        draw: Callable[[GKS], None]
        topping_offset: int


    @dataclass(frozen=True, slots=True)
    class ToppingOption:
        cost: float
        draw: Callable[[int, int, GKS], None]


    sizes = {
        SizeOptions.SMALL: SizeOption(
            cost=10,
            description="10-inch pizza",
            draw=draw_sm_pizza,
            topping_offset=7,
        ),
        SizeOptions.MEDIUM: SizeOption(
            cost=15,
            description="14-inch pizza",
            draw=draw_md_pizza,
            topping_offset=9,
        ),
        SizeOptions.LARGE: SizeOption(
            cost=20,
            description="18-inch pizza",
            draw=draw_lg_pizza,
            topping_offset=11,
        ),
    }

    proteins = {
        ProteinOptions.PEPPERONI: ToppingOption(2, draw_pepperoni),
        ProteinOptions.SAUSAGE: ToppingOption(2, draw_sausage),
        ProteinOptions.TOFU: ToppingOption(5, draw_tofu)
    }

    vegetables = {
        VegetableOptions.BELL_PEPPERS: ToppingOption(0.50, draw_bpepper),
        VegetableOptions.RED_PEPPERS: ToppingOption(0.50, draw_rpepper),
        VegetableOptions.BLACK_OLIVES: ToppingOption(0.75, draw_olive),
    }


    gks = GKS()

    draw_static_ui(gks)

    # Blit a red square into top right section
    gks.blit(
        [
            [(255, 0, 0)] * 5,
            [(255, 0, 0)] * 5,
            [(255, 0, 0)] * 5,
            [(255, 0, 0)] * 5,
            [(255, 0, 0)] * 5,
        ],
        97,
        23,
    )

    cur_size = SizeOptions.SMALL
    cur_protein = ProteinOptions.PEPPERONI
    cur_vegetable = VegetableOptions.BELL_PEPPERS

    size = sizes[cur_size]
    protein = proteins[cur_protein]
    vegetable = vegetables[cur_vegetable]

    size.draw(gks)

    for x, y in (
            (CENTER_X + size.topping_offset, CENTER_Y + size.topping_offset),
            (CENTER_X - size.topping_offset, CENTER_Y - size.topping_offset),

    ):
        protein.draw(x, y, gks)

    for x, y in (
            (CENTER_X + size.topping_offset, CENTER_Y - size.topping_offset),
            (CENTER_X - size.topping_offset, CENTER_Y + size.topping_offset)
    ):
        vegetable.draw(x, y, gks)

    gks.start_render_loop(60)
