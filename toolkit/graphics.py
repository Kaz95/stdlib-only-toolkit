"""A module to encapsulate all things graphics.

This module will eventually take over all duties currently distributed throughout animator.py and canvas.py.
Boarder box drawing will most likely become deprecated and will not be carried over.
My goal is to create a very rudimentary graphics library I can use for the rest of the semester, and then use it to
learn about packaging a library for distribution.

TODO:
    * Dynamic aspect to maintain square canvas(height/0.76 = width * .76)
    * Implement the rest of the primitive drawing functions.
    * Implement main paint loop. Control frame time similar to CHIP8.
    * Implement pre renderer, lerp, and (learn)various animations.
    * Learn and implement palette swap, fade, and cycling.
    * Improve draw algos(Bresenham, ect.)
    * Consider efficiency gains like color runs, don't draw if 2 rows empty, draw full block if 2 rows same, ect.
"""
import sys
from pprint import pp


class GKS:
    RESET = "\033[0m"
    CURSOR_TO_TOP = "\x1b[H"
    CLEAR_SCREEN = "\x1b[2J"
    HIDE_CURSOR = "\x1b[?25l"
    SHOW_CURSOR = "\x1b[?25h"

    UPPER_BLOCK = '\u2580'  # ▀
    LOWER_BLOCK = '\u2584'  # ▄
    FULL_BLOCK = '\u2588'  # █
    BLACK = (0, 0, 0)
    WIDTH = 132
    HEIGHT = 100

    PRE_RENDERED_FRAMES = []

    BUFFER_ROW = [BLACK] * WIDTH
    VIDEO_BUFFER = []

    def __init__(self, width=WIDTH, height=HEIGHT):
        self.width = width
        self.height = height
        self.VIDEO_BUFFER = [[(0, 0, 0)] * self.width for _ in range(self.height)]


    def clear(self):
        for y in range(len(self.VIDEO_BUFFER)):
            for x in range(len(self.VIDEO_BUFFER[y])):
                self.VIDEO_BUFFER[y][x] = self.BLACK

    def set_pixel(self, x, y, color):
        self.VIDEO_BUFFER[y][x] = color

    def draw_line(self, x1, y1, x2, y2, color):
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


    def draw_rect(self, fill=False):
        pass

    def draw_circle(self):
        pass

    def draw_sprite(self):
        pass

    def blit(self):
        pass


    def paint_frame(self):
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

    gks.draw_line(25,25, 75, 75, (255, 255, 255))
    gks.draw_line(75, 25, 25, 75, (255, 255, 255))
    gks.draw_line(25,25, 75, 25, (255, 255, 255))
    gks.draw_line(75,25, 75, 75, (255, 255, 255))
    gks.draw_line(25, 75, 75, 75, (255, 255, 255))
    gks.draw_line(25, 25, 25, 75, (255, 255, 255))

    print(gks.CLEAR_SCREEN)
    gks.paint_frame()