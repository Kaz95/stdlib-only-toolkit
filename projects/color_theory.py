"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.
"""
import collections
import json
import msvcrt
import sys
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Final

RGB = tuple[int, int, int]
TRANSLUCENT = None
PIXEL = RGB | int | TRANSLUCENT
BITMAP = list[list[PIXEL]]


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
    TRANSLUCENT = None

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
        self.video_buffer: list[list[PIXEL]] = [[(0, 0, 0)] * self.width for _ in range(self.height)]
        self.sprites = {}
        self.active_sprites = []
        self.animations = {}
        self.active_animations = []
        self.palettes = []

    def clear(self) -> None:
        """Clear video buffer in place."""
        for y in range(len(self.video_buffer)):
            for x in range(len(self.video_buffer[y])):
                self.video_buffer[y][x] = self.BLACK

    def set_pixel(self, x: int, y: int, color: int | RGB = WHITE, canvas: BITMAP | None = None) -> None:
        """Set a single pixels color."""
        if canvas is None:
            canvas = self.video_buffer

        canvas_height = len(canvas)
        canvas_width = len(canvas[0]) if canvas_height else 0

        if not (0 <= x < canvas_width and 0 <= y < canvas_height):
            return

        canvas[y][x] = color
        self.buffer_updated = True

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: int | RGB = WHITE,
                  canvas: BITMAP | None = None) -> None:
        """Draw a line between two points, using a given color."""
        delta_of_x = x2 - x1
        delta_of_y = y2 - y1

        # If vertical line
        if delta_of_x == 0:
            step = 1 if y2 >= y1 else -1
            for y in range(y1, y2 + step, step):
                self.set_pixel(x1, y, color, canvas)
            return

        m = delta_of_y / delta_of_x
        b = y1 - m * x1

        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            y = round(m * x + b)
            self.set_pixel(x, y, color)

    def draw_rect(self, x: int, y: int, width: int, height: int, color: int | RGB = WHITE,
                  canvas: BITMAP | None = None) -> None:
        """Draw a four sided object, of a given color and size, starting at point (x,y)."""
        # Have to subtract one to avoid over running.  Width represents how wide rect is, points included.
        x2 = x + width - 1
        y2 = y + height - 1

        self.draw_line(x, y, x2, y, color, canvas)  # Top
        self.draw_line(x, y2, x2, y2, color, canvas)  # Bottom
        self.draw_line(x, y, x, y2, color, canvas)  # Left
        self.draw_line(x2, y, x2, y2, color, canvas)  # Right

    def draw_filled_rect(self, x: int, y: int, width: int, height: int, color: int | RGB = WHITE,
                         canvas: BITMAP | None = None) -> None:
        """Draw a filled four sided object, of a given color and size, starting at point (x,y).

        Just iterate through every pixel and set it to the given color.
        """
        for row in range(y, y + height):
            for col in range(x, x + width):
                self.set_pixel(col, row, color, canvas)

    def draw_background(self):
        """Generic background drawing method. Customize as needed."""
        pass

    def draw_sprite(self, sprite_bitmap: BITMAP, x_sprite_coordinate: int, y_sprite_coordinate: int) -> None:
        """Draw a sprite while preserving the background beneath translucent pixels."""
        if not sprite_bitmap or not sprite_bitmap[0]:
            raise ValueError("Sprite must not be empty")

        sprite_height = len(sprite_bitmap)
        sprite_width = len(sprite_bitmap[0])

        if any(len(row) != sprite_width for row in sprite_bitmap):
            raise ValueError("Sprite rows must have equal widths")

        # Find the first sprite column visible on screen.
        # If x is negative, its inverse will be positive and that many pixels are clipped from the sprite.
        sprite_left_edge = max(0, -x_sprite_coordinate)
        # Find the first sprite row visible on screen. Same as left edge
        sprite_top_edge = max(0, -y_sprite_coordinate)

        # Min of actual sprite dimension and the number of sprite row/columns that can fit before canvas edges.
        sprite_right_edge = min(sprite_width, self.width - x_sprite_coordinate)
        sprite_bottom_edge = min(sprite_height, self.height - y_sprite_coordinate)

        # If invalid slice range, the entire sprite is outside the video buffer.
        if sprite_left_edge >= sprite_right_edge or sprite_top_edge >= sprite_bottom_edge:
            return

        # Iterate through sprite rows that are visible.
        for sprite_row_index in range(sprite_top_edge, sprite_bottom_edge):
            # Translate visible sprite row into its destination video buffer row.
            buffer_row_index = sprite_row_index + y_sprite_coordinate

            # Grab visible section of sprite row.
            sprite_row = sprite_bitmap[sprite_row_index][sprite_left_edge:sprite_right_edge]

            # Translate the visible sprite columns into buffer columns.
            destination_left = x_sprite_coordinate + sprite_left_edge
            destination_right = x_sprite_coordinate + sprite_right_edge

            # Get the buffer destination row.
            destination_row = self.video_buffer[buffer_row_index]

            # Save the existing pixels so translucent sprite pixels can preserve them.
            existing_row = destination_row[destination_left:destination_right]

            # All translucent
            if all(pixel is TRANSLUCENT for pixel in sprite_row):
                continue

            # None translucent
            if all(pixel is not TRANSLUCENT for pixel in sprite_row):
                destination_row[destination_left:destination_right] = sprite_row
                continue

            # Merge rows, keep old pixel if translucent sprite pixel, else use sprite pixel.
            destination_row[destination_left:destination_right] = [
                old_pixel if sprite_pixel is TRANSLUCENT else sprite_pixel
                for old_pixel, sprite_pixel in zip(existing_row, sprite_row)
            ]

        self.buffer_updated = True

    def draw_frame(self) -> None:
        """Draw a single frame to the terminal."""
        sys.stdout.write(self.CURSOR_TO_TOP)
        for y in range(0, self.height, 2):
            line_buffer = []
            for x in range(self.width):
                top = self.video_buffer[y][x]
                bottom = self.video_buffer[y + 1][x] if y + 1 < self.height else self.BLACK
                if isinstance(top, int):
                    if not self.palettes:
                        raise ValueError('Non existent color palette referenced. Add a color palette to GKS.palettes.')
                    top = self.palettes[0][top]
                if isinstance(bottom, int):
                    if not self.palettes:
                        raise ValueError('Non existent color palette referenced. Add a color palette to GKS.palettes.')
                    bottom = self.palettes[0][bottom]

                bg_ansi = f"\x1b[48;2;{top[0]};{top[1]};{top[2]}m"
                fg_ansi = f"\x1b[38;2;{bottom[0]};{bottom[1]};{bottom[2]}m"

                line_buffer.append(f"{bg_ansi}{fg_ansi}{self.LOWER_BLOCK}")

            sys.stdout.write(''.join(line_buffer) + self.RESET + '\n')
            sys.stdout.flush()

    def do_stuff(self) -> None:
        """Realized there was no easy way to add work to render loop without going through commands. Quick fix.

        Of course, I could just add work directly to the render loop, but I want to leave the loop as decoupled as
        possible from any program specific work done within the loop.
        """
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
                self.do_stuff()
                start_time = time.perf_counter()
                if command_handler is not None and msvcrt.kbhit():
                    key = msvcrt.getwch()
                    flag = command_handler.handle(key)
                    if flag == 'quit':
                        break

                if self.active_animations:
                    self.buffer_updated = True
                    for animation in self.active_animations:
                        flag = animation.next_step()
                        if flag == 'done':
                            self.active_animations.remove(animation)

                if self.buffer_updated:
                    self.draw_background()
                    for sprite in self.active_sprites:
                        self.draw_sprite(sprite.bitmap, sprite.position[0], sprite.position[1])
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

    def draw_chars(self, word: str, x_start: int, y_start: int, color: RGB = WHITE, canvas: BITMAP | None = None):
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
                        self.set_pixel(x_start + x, y_start + y, color, canvas)
                    if bottom:
                        self.set_pixel(x_start + x, y_start + y + 1, color, canvas)

            x_start += 8

    def draw_centered_chars(self, word: str, y: int, color: RGB = WHITE, canvas: BITMAP | None = None):
        """Draw center aligned characters. Centered within canvas total width."""
        x_offset = (self.width - (len(word) * 8)) // 2

        self.draw_chars(word, x_offset, y, color, canvas)


@dataclass
class Sprite:
    """Sprite class that encompasses data that makes up a sprite."""
    name: str
    position: list[int]
    width: int
    height: int
    bitmap: BITMAP | None = None

    def _create_canvas(self, width: int, height: int):
        """Create canvas with given width and height. Default pixel state is translucent."""
        canvas = [[TRANSLUCENT] * width for _ in range(height)]
        self.bitmap = canvas

    def __post_init__(self):
        self._create_canvas(self.width, self.height)


class Animation(ABC):
    """Animation abstract base class."""

    def __init__(self, sprite, steps, target, bounce=True):
        self.sprite = sprite
        self.original_pos = sprite.position.copy()
        self.steps = steps
        self.progress = 0
        self.direction = True
        self.target = target
        self.pre_calcd_values = self.precompute_steps()
        self.bounce = bounce

    def lerp(self, start, target, progress):
        """Generic linear interpolation method."""
        result = start + (target - start) * progress
        return result

    @abstractmethod
    def next_step(self):
        """Generic method that advances the animation to the next step."""
        pass

    @abstractmethod
    def precompute_steps(self):
        """Generic method to precompute animation steps."""
        pass


class FadeAnimation(Animation):
    """Concrete FadeAnimation class.

    Fade between two colors. Forward and back.
    """

    def render_interpolated_bitmap(self, progress):
        """Render an intermediate bitmap based on current progress of the linear interpolation."""
        new_bitmap = []
        for row in self.sprite.bitmap:
            temp_row = []
            for pixel in row:
                if pixel is not TRANSLUCENT:
                    r = int(self.lerp(pixel[0], self.target[0], progress))
                    g = int(self.lerp(pixel[1], self.target[1], progress))
                    b = int(self.lerp(pixel[2], self.target[2], progress))
                    temp_row.append((r, g, b))
                else:
                    temp_row.append(TRANSLUCENT)
            new_bitmap.append(temp_row)
        return new_bitmap

    def precompute_steps(self):
        """Precompute the intermediate bitmaps between starting bitmap and the target color."""
        results = []
        for step in range(self.steps + 1):
            progress = step / self.steps
            results.append(self.render_interpolated_bitmap(progress))
        return results

    def next_step(self):
        """Advance the animation to the next bitmap. Reverse direction when an end point is reached."""
        if self.direction:
            if self.progress < self.steps:
                self.sprite.bitmap = self.pre_calcd_values[self.progress]
                self.progress += 1
            else:
                self.direction = False
                self.progress -= 1
        else:
            if self.progress >= 0:
                self.sprite.bitmap = self.pre_calcd_values[self.progress]
                self.progress -= 1
            else:
                self.direction = True
                self.progress += 1


class MoveAnimation(Animation):
    """Concrete MoveAnimation class.

    Move between two points. Forward and back.
    """

    def __init__(self, sprite, steps, target, bounce=True):
        super().__init__(sprite, steps, target, bounce=bounce)

    def precompute_next_position(self, progress):
        """Precompute the next position based on progress of the linear interpolation."""
        x = self.sprite.position[0]
        y = self.sprite.position[1]
        x = int(self.lerp(x, self.target[0], progress))
        y = int(self.lerp(y, self.target[1], progress))
        return x, y

    def precompute_steps(self):
        """Precompute the intermediate positions between start and target position."""
        results = []
        for step in range(self.steps + 1):
            progress = step / self.steps
            results.append(self.precompute_next_position(progress))
        return results

    def next_step(self):
        """Advance the animation to the next position. Reverse direction when an end point is reached."""

        if self.direction:
            if self.progress < self.steps:
                self.sprite.position = list(self.pre_calcd_values[self.progress])
                self.progress += 1
            else:
                if not self.bounce:
                    return 'done'
                else:
                    self.direction = False
                    self.progress -= 1
        else:
            if self.progress >= 0:
                self.sprite.position = list(self.pre_calcd_values[self.progress])
                self.progress -= 1
            else:
                self.direction = True
                self.progress += 1

    def reset_animation(self):
        self.progress = 0
        self.sprite.position = self.original_pos


class ColorPaletteAnimation:
    def __init__(self, current_hue, palette_animation_steps=10, hues=None, hue_transition_steps=6) -> None:
        # Probably could have skipped since I'm the only one using this, but trying to get better about input validation
        if not current_hue:
            raise ValueError("Hue must contain at least one color")
        if palette_animation_steps <= 0:
            raise ValueError("Palette animation steps must be positive")
        if hue_transition_steps <= 0:
            raise ValueError("Hue transition steps must be positive")
        if hues is not None:
            if not hues:
                raise ValueError("Hues must contain at least one hue.")
            if any(len(hue) != len(current_hue) for hue in hues):
                raise ValueError("Hues must have the same size as the source palette")

        self.current_hue = current_hue.copy()
        self.active_palette = current_hue.copy()

        self.palette_animation_snapshot = self.active_palette.copy()
        self.palette_animation_steps = palette_animation_steps
        self.palette_animation_progress = 0

        self.hues = [hue.copy() for hue in hues] if hues is not None else []
        self.target_hue_index = 0
        self.hue_transition_steps = hue_transition_steps
        self.hue_progress = 0

        self.rotated_colors = 0

    def lerp_RGB(self, starting_color, target_color, progress):
        r = int(starting_color[0] + (target_color[0] - starting_color[0]) * progress)
        g = int(starting_color[1] + (target_color[1] - starting_color[1]) * progress)
        b = int(starting_color[2] + (target_color[2] - starting_color[2]) * progress)

        return r, g, b

    def next_step(self):
        if self.palette_animation_progress == 0:
            self.palette_animation_snapshot = self.active_palette.copy()

        self.palette_animation_progress += 1
        lerp_progress = self.palette_animation_progress / self.palette_animation_steps

        for index, starting_color in enumerate(self.palette_animation_snapshot):
            target_color = self.palette_animation_snapshot[(index - 1) % len(self.palette_animation_snapshot)]
            new_color = self.lerp_RGB(starting_color, target_color, lerp_progress)
            self.active_palette[index] = new_color

        if self.palette_animation_progress == self.palette_animation_steps:
            self.palette_animation_progress = 0
            self.rotated_colors += 1

            if self.rotated_colors == len(self.active_palette):
                self.rotated_colors = 0
                if self.hues:
                    self.hue_progress = min(self.hue_progress + 1, self.hue_transition_steps)
                    lerp_progress = self.hue_progress / self.hue_transition_steps
                    target_color = self.hues[self.target_hue_index]
                    for index, starting_color in enumerate(self.current_hue):
                        self.active_palette[index] = self.lerp_RGB(
                            starting_color,
                            target_color[index],
                            lerp_progress,
                        )
                    if self.hue_progress == self.hue_transition_steps:
                        self.current_hue = self.active_palette.copy()
                        self.target_hue_index = (self.target_hue_index + 1) % len(self.hues)
                        self.hue_progress = 0


class CommandHandler:
    """Command Handler Factory.

    I've never written anything quite like this, and I'm not really sure where I want to put it yet.
    """

    def __init__(self):
        pass

    def handle(self, key):
        """Handle a keypress."""
        match key:
            case 'q':
                return 'quit'

            case '\r':
                return 'enter'


if __name__ == '__main__':

    class MyGKS(GKS):
        PAGE = collections.deque(['intro', 'sel1', 'sel2', 'output'])
        GRAY_PALETTE = [(0, 0, 0), (36, 36, 36), (109, 109, 109), (182, 182, 182), (255, 255, 255)]
        BLUE_PALETTE = [(20, 40, 55), (45, 85, 115), (85, 135, 165), (145, 190, 210), (220, 240, 250)]
        PURPLE_PALETTE = [(35, 20, 50), (75, 45, 100), (125, 80, 150), (180, 135, 195), (225, 205, 235)]
        RED_PALETTE = [(75, 15, 15), (125, 30, 30), (180, 60, 60), (215, 130, 130), (245, 220, 220)]
        ORANGE_PALETTE = [(70, 25, 10), (125, 55, 15), (180, 90, 25), (220, 155, 75), (245, 220, 180)]
        YELLOW_PALETTE = [(55, 50, 10), (110, 100, 15), (170, 155, 30), (215, 200, 80), (245, 235, 180)]
        GREEN_PALETTE = [(15, 55, 25), (30, 105, 50), (55, 155, 80), (125, 195, 140), (215, 240, 220)]
        SELECTION = collections.deque(['sel1', 'sel2'])
        PERSONALITY = None
        STYLE = None
        COLORS = [
            {
                "color_name": "Whale's Tail",
                "tone": "cool",
                "intensity": 6,
                "color_value": (0, 57, 103)
            },
            {
                "color_name": "Wild Orange",
                "tone": "warm",
                "intensity": 8,
                "color_value": (255, 122, 92)
            },
            {
                "color_name": "Leche Flan",
                "tone": "warm",
                "intensity": 2,
                "color_value": (244, 212, 175)
            },
            {
                "color_name": "StrawberryFields",
                "tone": "warm",
                "intensity": 5,
                "color_value": (159, 75, 61)
            },
            {
                "color_name": "Dove Wing",
                "tone": "cool",
                "intensity": 1,
                "color_value": (233, 230, 219)
            },
            {
                "color_name": "Buttermilk",
                "tone": "warm",
                "intensity": 1,
                "color_value": (246, 224, 164)
            },
            {
                "color_name": "Velvety Night",
                "tone": "cool",
                "intensity": 10,
                "color_value": (68, 66, 85)
            },
            {
                "color_name": "Black Orchid",
                "tone": "cool",
                "intensity": 10,
                "color_value": (59, 9, 16)
            },
            {
                "color_name": "Parisian Rose",
                "tone": "cool",
                "intensity": 4,
                "color_value": (216, 145, 160)
            },
            {
                "color_name": "Limon Sorbet",
                "tone": "warm",
                "intensity": 2,
                "color_value": (245, 242, 170)
            },
            {
                "color_name": "Snowflake",
                "tone": "cool",
                "intensity": 1,
                "color_value": (245, 245, 245)
            },
            {
                "color_name": "Almond Butter",
                "tone": "warm",
                "intensity": 3,
                "color_value": (230, 210, 181)
            },
            {
                "color_name": "Candy Floss",
                "tone": "cool",
                "intensity": 2,
                "color_value": (247, 168, 184)
            },
            {
                "color_name": "Plum Jam",
                "tone": "cool",
                "intensity": 9,
                "color_value": (96, 26, 53)
            },
            {
                "color_name": "Milky Way",
                "tone": "cool",
                "intensity": 9,
                "color_value": (232, 220, 196)
            },
            {
                "color_name": "Copper Kettle",
                "tone": "warm",
                "intensity": 7,
                "color_value": (138, 73, 53)
            },
            {
                "color_name": "Cayenne",
                "tone": "warm",
                "intensity": 8,
                "color_value": (227, 66, 52)
            },
        ]

        hues = [BLUE_PALETTE,
                PURPLE_PALETTE,
                RED_PALETTE,
                ORANGE_PALETTE,
                YELLOW_PALETTE,
                GREEN_PALETTE]

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
                    self.do_stuff()
                    start_time = time.perf_counter()
                    if command_handler is not None and msvcrt.kbhit():
                        key = msvcrt.getwch()
                        flag = command_handler.handle(key)
                        if flag == 'quit':
                            break

                        elif flag == 'enter':
                            if self.PAGE[0] == 'sel1':
                                if self.SELECTION[0] == 'sel1':
                                    self.PERSONALITY = 'warm'
                                else:
                                    self.PERSONALITY = 'cool'
                            elif self.PAGE[0] == 'sel2':
                                if self.SELECTION[0] == 'sel1':
                                    self.STYLE = 'bold'
                                else:
                                    self.STYLE = 'elegant'

                            if self.PAGE[0] != 'output':
                                self.PAGE.rotate(-1)

                        if key in ('\xe0', '\x00'):
                            key = msvcrt.getwch()
                            if key == 'K':
                                self.SELECTION.rotate(-1)
                            elif key == 'M':
                                self.SELECTION.rotate(1)

                    if self.active_animations:
                        self.buffer_updated = True
                        for animation in self.active_animations:
                            flag = animation.next_step()
                            if flag == 'done':
                                self.active_animations.remove(animation)

                    if self.buffer_updated:
                        self.draw_background()
                        for sprite in self.active_sprites:
                            self.draw_sprite(sprite.bitmap, sprite.position[0], sprite.position[1])
                        self.draw_frame()
                        self.buffer_updated = False

                    elapsed_time = time.perf_counter() - start_time
                    sleep_time = frame_duration - elapsed_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
            finally:
                sys.stdout.write(self.SHOW_CURSOR)

        def setup_sprites(self):
            self.active_sprites.clear()

            marquee_animation = ColorPaletteAnimation(self.GRAY_PALETTE, hues=self.hues)
            self.animations['marquee_animation'] = marquee_animation
            self.active_animations.append(marquee_animation)
            self.palettes.append(marquee_animation.active_palette)

            top_half_logo = Sprite('top_half_logo', [-45, 40], 40, 8)
            self.sprites[top_half_logo.name] = top_half_logo
            self.draw_chars('Color', 0, 0, 4, top_half_logo.bitmap)

            bottom_half_logo = Sprite('bottom_half_logo', [375, 48], 48, 8)
            self.sprites[bottom_half_logo.name] = bottom_half_logo
            self.draw_chars('Theory', 0, 0, 4, bottom_half_logo.bitmap)

            intro_instructions = Sprite('intro_instructions', [25, 370], 120, 8)
            self.sprites[intro_instructions.name] = intro_instructions
            self.draw_chars('Press Enter', 0, 0, 4, intro_instructions.bitmap)

            selection_instructions = Sprite('selection_instructions', [99, 75], 24, 8)
            self.sprites[selection_instructions.name] = selection_instructions
            self.draw_chars('< >', 0, 0, 4, selection_instructions.bitmap)

            hot_selected = Sprite('hot_selected', [29, 60], 24, 8)
            self.sprites[hot_selected.name] = hot_selected
            self.draw_chars('hot', 0, 0, self.GRAY_PALETTE[4], hot_selected.bitmap)

            hot_not_selected = Sprite('hot_not_selected', [29, 60], 24, 8)
            self.sprites[hot_not_selected.name] = hot_not_selected
            self.draw_chars('Hot', 0, 0, self.RED_PALETTE[0], hot_not_selected.bitmap)

            cool_selected = Sprite('cool_selected', [79, 60], 32, 8)
            self.sprites[cool_selected.name] = cool_selected
            self.draw_chars('cool', 0, 0, self.GRAY_PALETTE[4], cool_selected.bitmap)

            cool_not_selected = Sprite('cool_not_selected', [79, 60], 32, 8)
            self.sprites[cool_not_selected.name] = cool_not_selected
            self.draw_chars('Cool', 0, 0, self.BLUE_PALETTE[0], cool_not_selected.bitmap)

            personality_page_title = Sprite('personality_page_title', [19, 32], 96, 8)
            self.sprites[personality_page_title.name] = personality_page_title
            self.draw_chars('Personality?', 0, 0, 4, personality_page_title.bitmap)

            bold_selected = Sprite('bold_selected', [18, 60], 32, 8)
            self.sprites[bold_selected.name] = bold_selected
            self.draw_chars('Bold', 0, 0, self.GRAY_PALETTE[4], bold_selected.bitmap)

            bold_not_selected = Sprite('bold_not_selected', [18, 60], 32, 8)
            self.sprites[bold_not_selected.name] = bold_not_selected
            self.draw_chars('Bold', 0, 0, (255, 191, 0), bold_not_selected.bitmap)

            elegant_selected = Sprite('elegant_selected', [66, 60], 56, 8)
            self.sprites[elegant_selected.name] = elegant_selected
            self.draw_chars('Elegant', 0, 0, self.GRAY_PALETTE[4], elegant_selected.bitmap)

            elegant_not_selected = Sprite('elegant_not_selected', [66, 60], 56, 8)
            self.sprites[elegant_not_selected.name] = elegant_not_selected
            self.draw_chars('Elegant', 0, 0, (120, 81, 169), elegant_not_selected.bitmap)

            style_page_title = Sprite('style_page_title', [43, 32], 96, 8)
            self.sprites[style_page_title.name] = style_page_title
            self.draw_chars('style?', 0, 0, 4, style_page_title.bitmap)

            self.active_sprites.append(self.sprites['top_half_logo'])
            self.active_sprites.append(self.sprites['bottom_half_logo'])
            self.active_sprites.append(self.sprites['intro_instructions'])

            move_top_logo = MoveAnimation(top_half_logo, 125, [48, 40], bounce=False)
            self.animations['move_top_logo'] = move_top_logo
            self.active_animations.append(move_top_logo)

            move_bottom_logo = MoveAnimation(bottom_half_logo, 350, [43, 48], bounce=False)
            self.animations['move_bottom_logo'] = move_bottom_logo
            self.active_animations.append(move_bottom_logo)

            move_instructions = MoveAnimation(intro_instructions, 500, [25, 70], bounce=False)
            self.animations['move_instructions'] = move_instructions
            self.active_animations.append(move_instructions)

        def generate_color_recs(self):
            color_recs = []

            for color in self.COLORS:
                if color['tone'] == self.PERSONALITY:
                    if self.STYLE == 'bold':
                        if color['intensity'] >= 5:
                            color_recs.append(color)
                    elif self.STYLE == 'elegant':
                        if color['intensity'] <= 5:
                            color_recs.append(color)

            return color_recs

        def draw_background(self):
            self.clear()
            self.draw_page()

        def do_stuff(self) -> None:
            pass

        def draw_marquee(self):
            color = 0
            for x_offset in range(0, 144, 11):
                self.draw_filled_rect(2 + x_offset, 6, 10, 10, color)
                x_offset += 11
                color += 1
                if color > 4:
                    color = 0

            for y_offset in range(17, 73, 11):
                self.draw_filled_rect(123, y_offset, 10, 10, color)
                color += 1
                if color > 4:
                    color = 0

            color = 4
            for x_offset in range(0, 144, 11):

                self.draw_filled_rect(2 + x_offset, 84, 10, 10, color)
                color -= 1
                if color < 0:
                    color = 4

            color = 3
            for y_offset in range(17, 73, 11):
                self.draw_filled_rect(2, y_offset, 10, 10, color)
                color -= 1
                if color < 0:
                    color = 4

        def draw_intro_page(self):
            self.draw_marquee()

        def draw_selection_page_1(self):
            self.draw_marquee()
            if self.SELECTION[0] == 'sel1':
                if self.sprites['hot_selected'] not in self.active_sprites:
                    self.active_sprites.clear()
                    self.active_sprites.extend([
                        self.sprites['personality_page_title'],
                        self.sprites['hot_selected'],
                        self.sprites['cool_not_selected'],
                        self.sprites['selection_instructions'],
                    ])
            else:
                if self.sprites['cool_selected'] not in self.active_sprites:
                    self.active_sprites.clear()
                    self.active_sprites.extend([
                        self.sprites['personality_page_title'],
                        self.sprites['cool_selected'],
                        self.sprites['hot_not_selected'],
                        self.sprites['selection_instructions'],
                    ])

        def draw_selection_page_2(self):
            self.draw_marquee()
            if self.SELECTION[0] == 'sel1':
                if self.sprites['bold_selected'] not in self.active_sprites:
                    self.active_sprites.clear()
                    self.active_sprites.extend([
                        self.sprites['style_page_title'],
                        self.sprites['bold_selected'],
                        self.sprites['elegant_not_selected'],
                        self.sprites['selection_instructions'],
                    ])
            else:
                if self.sprites['elegant_selected'] not in self.active_sprites:
                    self.active_sprites.clear()
                    self.active_sprites.extend([
                        self.sprites['style_page_title'],
                        self.sprites['elegant_selected'],
                        self.sprites['bold_not_selected'],
                        self.sprites['selection_instructions'],
                    ])

        def draw_color_recommendations(self, color_recs):
            """Draw each color name with its tone and intensity."""
            y = 2
            for color in color_recs:
                name = color['color_name']
                tone = f"Tone:{color['tone']}"
                intensity = f"Int:{color['intensity']}"

                self.draw_centered_chars(name, y, color['color_value'])

                if color['tone'] == 'warm':
                    tone_color = (220, 20, 60)
                else:
                    tone_color = (0, 119, 190)
                if color['intensity'] >= 5:
                    intensity_color = (255, 234, 0)
                else:
                    intensity_color = (207, 181, 59)

                self.draw_chars(tone, 4, y + 8, tone_color)
                self.draw_chars(intensity, 87, y + 8, intensity_color)
                y += 20

        def draw_output_page(self):
            color_recs = self.generate_color_recs()
            self.active_sprites.clear()
            self.active_animations.clear()

            self.draw_color_recommendations(color_recs)

        def draw_page(self):
            if self.PAGE[0] == 'intro':
                self.draw_intro_page()
            elif self.PAGE[0] == 'sel1':
                self.draw_selection_page_1()
            elif self.PAGE[0] == 'sel2':
                self.draw_selection_page_2()
            elif self.PAGE[0] == 'output':
                self.draw_output_page()


    gks = MyGKS()
    sys.stdout.write(gks.ENTER_ALT_SCREEN)
    sys.stdout.write(gks.HIDE_CURSOR)

    chandler = CommandHandler()
    gks.setup_sprites()

    try:
        gks.start_render_loop(60, command_handler=chandler)

    finally:
        sys.stdout.write(gks.SHOW_CURSOR)
        sys.stdout.write(gks.EXIT_ALT_SCREEN)
