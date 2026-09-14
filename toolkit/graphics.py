"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.

TODO:
    * Migrate project to uv.
    * Add docstrings.
    * Add tests.
    * Dynamic aspect to maintain square canvas(height/0.76 = width * .76)
    * Implement the rest of the primitive drawing functions.
    * Implement main paint loop. Control frame time similar to CHIP8.
    * Implement pre renderer, lerp, and (learn)various animations.
    * Learn and implement palette swap, fade, and cycling.
    * Improve draw algos(Bresenham, midpoint circle.)
    * Consider efficiency gains like color runs, don't draw if 2 rows empty, draw full block if 2 rows same, ect.
"""
import sys
from pprint import pp


class GKS:
    """A class for drawing vector and bitmapped graphics to the terminal.

    Will provide constants, drawing primitives, animation pre-rendering, and custom color palettes. The name GKS is
    a homage to the Graphical Kernel System, the first international standard for low-level 2D computer graphics.
    """
    RESET = "\033[0m"
    CURSOR_TO_TOP = "\x1b[H"
    CLEAR_SCREEN = "\x1b[2J"
    HIDE_CURSOR = "\x1b[?25l"
    SHOW_CURSOR = "\x1b[?25h"

    UPPER_BLOCK = '\u2580'  # ▀
    LOWER_BLOCK = '\u2584'  # ▄
    FULL_BLOCK = '\u2588'  # █
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    WIDTH = 132
    HEIGHT = 100

    PRE_RENDERED_FRAMES = []

    BUFFER_ROW = [BLACK] * WIDTH
    VIDEO_BUFFER = []

    def __init__(self, width=WIDTH, height=HEIGHT):
        """Initialize video buffer to a blank screen and cast custom height and width(if applicable) to attributes."""
        self.width = width
        self.height = height
        self.VIDEO_BUFFER = [[(0, 0, 0)] * self.width for _ in range(self.height)]


    def clear(self):
        """Clear video buffer in place."""
        for y in range(len(self.VIDEO_BUFFER)):
            for x in range(len(self.VIDEO_BUFFER[y])):
                self.VIDEO_BUFFER[y][x] = self.BLACK

    def set_pixel(self, x, y, color=WHITE):
        """Set a single pixels color."""
        self.VIDEO_BUFFER[y][x] = color

    def draw_line(self, x1, y1, x2, y2, color=WHITE):
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



    def draw_rect(self, x, y, width, height, color=WHITE):
        """Draw a four sided object, of a given color and size, starting at point (x,y)."""
        # Have to subtract one to avoid over running.  Width represents how wide rect is, points included.
        x2 = x + width - 1
        y2 = y + height - 1

        self.draw_line(x, y, x2, y, color) # Top
        self.draw_line(x, y2, x2, y2, color) # Bottom
        self.draw_line(x, y, x, y2, color) # Left
        self.draw_line(x2, y, x2, y2, color) # Right

    def draw_filled_rect(self, x, y, width, height, color=WHITE):
        """Draw a filled four sided object, of a given color and size, starting at point (x,y).

        Just iterate through every pixel and set it to the given color. 
        """
        for row in range(y, y + height):
            for col in range(x, x + width):
                self.set_pixel(col, row, color)

    def draw_circle(self):
        pass

    def draw_filled_circle(self):
        pass

    def draw_sprite(self, x, y, sprite_data):
        """Draw sprite from given data, starting at point (x,y)."""
        pass

    def blit(self, bitmap):
        """Replace the frame buffer with given bitmap using slice replacement(memmove)."""
        pass


    def paint_frame(self):
        """Paint a single frame to the terminal."""
        for y in range(0, self.height, 2):
            line_buffer = []
            for x in range(self.width):
                top = self.VIDEO_BUFFER[y][x]
                bottom = self.VIDEO_BUFFER[y + 1][x]

                bg_ansi = f"\x1b[48;2;{top[0]};{top[1]};{top[2]}m"
                fg_ansi = f"\x1b[38;2;{bottom[0]};{bottom[1]};{bottom[2]}m"

                line_buffer.append(f"{bg_ansi}{fg_ansi}{self.LOWER_BLOCK}")

            sys.stdout.write(''.join(line_buffer) + self.RESET + '\n')
            sys.stdout.flush()

if __name__ == '__main__':
    gks = GKS()

    # gks.draw_line(25,25, 75, 75, (255, 255, 255))
    # gks.draw_line(75, 25, 25, 75, (255, 255, 255))
    # gks.draw_line(25,25, 75, 25)
    # gks.draw_line(75,25, 75, 75)
    # gks.draw_line(25, 75, 75, 75)
    # gks.draw_line(25, 25, 25, 75)

    # gks.draw_rect(25, 25, 50, 50)
    gks.draw_filled_rect(25, 25, 50, 50)
    print(gks.CLEAR_SCREEN)
    gks.paint_frame()