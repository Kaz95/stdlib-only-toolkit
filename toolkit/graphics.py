"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.

TODO:
    * Considering using new and old circle methods as a way to learn a how to benchmark and profile exactly where the
        gains come from.
    * Start researching Mike Pitteway and drawing ellipses.
    * Migrate project to uv.
    * Add tests.
    * Dynamic aspect to maintain square canvas(height/0.76 = width * .76)
    * Implement the rest of the primitive drawing functions.
    * Implement main paint loop. Control frame time similar to CHIP8.
    * Implement pre renderer, lerp, and (learn)various animations.
    * Learn and implement palette swap, fade, and cycling.
    * Consider efficiency gains like color runs, don't draw if 2 rows empty, draw full block if 2 rows same, ect.
"""
import sys
from math import sqrt
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

    def draw_bresenhams_line(self, x1, y1, x2, y2, color=WHITE):
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

    def old_draw_circle(self, center_x, center_y, radius, color=WHITE):
        """Draw a circle around center point, starting at point (x,y).

        This is currently using cartesian method based on relationship between x and y. Improvements Soon™.
        """
        for x in range(center_x - radius, center_x + radius + 1):
            delta_of_x = x - center_x

            y_offset = sqrt(radius**2 - delta_of_x**2)

            y1 = round(center_y - y_offset)
            y2 = round(center_y + y_offset)

            self.set_pixel(x, y1)
            self.set_pixel(x, y2)

    def new_draw_circle(self, center_x, center_y, radius):
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
            self.set_pixel(center_x + x, center_y + y)
            self.set_pixel(center_x - x, center_y + y)
            self.set_pixel(center_x + x, center_y - y)
            self.set_pixel(center_x - x, center_y - y)

            self.set_pixel(center_x + y, center_y + x)
            self.set_pixel(center_x - y, center_y + x)
            self.set_pixel(center_x + y, center_y - x)
            self.set_pixel(center_x - y, center_y - x)

            if running_decision_parameter < 0:
                # Choose East
                running_decision_parameter += 2 * x + 3
            else:
                # Choose South-East
                y -= 1
                running_decision_parameter += 2 * (x - y) + 5

            x += 1




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

    # gks.draw_rect(90, 10, 13, 13)
    # gks.set_pixel(96, 16)
    # gks.draw_filled_rect(75, 25, 10, 10)
    # gks.draw_circle(25, 25, 20)
    # gks.draw_bresenhams_line(75, 75, 80, 80)
    # gks.draw_bresenhams_line(80, 75, 75, 80)
    # print(gks.CLEAR_SCREEN)
    # gks.old_draw_circle(75, 75, 20)
    # gks.new_draw_circle(40, 40, 20)
    gks.draw_bresenhams_line(10, 20, 70, 35)
    gks.draw_bresenhams_line(20, 10, 35, 70)

    gks.paint_frame()