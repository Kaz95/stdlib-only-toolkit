"""Regression tests for the terminal graphics primitives.

TODO
    * boundary/edge-case tests
    * negative coordinate or out-of-bounds tests
    * very small shapes
    * zero-radius / zero-width / zero-height tests
    * line tests for descending coordinates and diagonals
    * property-style tests for symmetry and fill behavior
"""

from toolkit.graphics import GKS


def test_constructor_initializes_blank_buffer():
    """The canvas should start as a black, correctly sized grid."""
    gks = GKS(8, 6)

    assert gks.width == 8
    assert gks.height == 6
    assert len(gks.VIDEO_BUFFER) == 6
    assert len(gks.VIDEO_BUFFER[0]) == 8
    assert all(pixel == gks.BLACK for row in gks.VIDEO_BUFFER for pixel in row)


def test_clear_restores_black_pixels():
    """Clearing should erase any previous drawing by resetting every pixel."""
    gks = GKS(8, 6)
    gks.set_pixel(2, 3, (10, 20, 30))

    gks.clear()

    assert gks.VIDEO_BUFFER[3][2] == gks.BLACK


def test_set_pixel_writes_color_to_buffer():
    """A single pixel should be written at the requested coordinate."""
    gks = GKS(8, 6)
    color = (12, 34, 56)

    gks.set_pixel(4, 2, color)

    assert gks.VIDEO_BUFFER[2][4] == color


def test_draw_line_draws_horizontal_and_vertical_segments():
    """Line drawing must cover the full segment, including axis-aligned lines."""
    gks = GKS(8, 6)
    color = (255, 0, 0)

    gks.draw_line(1, 1, 4, 1, color)
    for x in range(1, 5):
        assert gks.VIDEO_BUFFER[1][x] == color

    gks.draw_line(6, 1, 6, 4, (0, 255, 0))
    for y in range(1, 5):
        assert gks.VIDEO_BUFFER[y][6] == (0, 255, 0)


def test_draw_bresenhams_line_draws_diagonal_points():
    """Bresenham should produce a predictable line through integer raster coordinates."""
    gks = GKS(8, 6)
    color = (0, 0, 255)

    gks.draw_bresenhams_line(0, 0, 4, 2, color)

    assert gks.VIDEO_BUFFER[0][0] == color
    assert gks.VIDEO_BUFFER[2][4] == color
    assert gks.VIDEO_BUFFER[1][2] == color


def test_draw_rect_draws_only_the_border():
    """Rectangles are defined by their edges, not by their filled interior."""
    gks = GKS(8, 6)
    color = (255, 0, 255)

    gks.draw_rect(1, 1, 4, 3, color)

    assert gks.VIDEO_BUFFER[1][1] == color
    assert gks.VIDEO_BUFFER[1][4] == color
    assert gks.VIDEO_BUFFER[3][1] == color
    assert gks.VIDEO_BUFFER[3][4] == color
    assert gks.VIDEO_BUFFER[2][2] != color


def test_draw_filled_rect_fills_the_entire_area():
    """Filled rectangles must paint every pixel inside the rectangle bounds."""
    gks = GKS(8, 6)
    color = (12, 13, 14)

    gks.draw_filled_rect(1, 1, 3, 2, color)

    for y in range(1, 3):
        for x in range(1, 4):
            assert gks.VIDEO_BUFFER[y][x] == color


def test_old_draw_circle_preserves_requested_color():
    """The legacy circle method should draw an unfilled circle of the given radius."""
    gks = GKS(8, 6)
    color = (9, 9, 9)

    gks.old_draw_circle(4, 3, 2, color)

    assert gks.VIDEO_BUFFER[1][4] == color
    assert gks.VIDEO_BUFFER[5][4] == color
    assert gks.VIDEO_BUFFER[3][2] == color
    assert gks.VIDEO_BUFFER[3][4] != color


def test_new_draw_circle_uses_eight_way_symmetry():
    """The midpoint circle algorithm should draw the expected symmetric points."""
    gks = GKS(8, 6)

    gks.new_draw_circle(4, 3, 2)

    assert gks.VIDEO_BUFFER[1][4] == gks.WHITE
    assert gks.VIDEO_BUFFER[5][4] == gks.WHITE
    assert gks.VIDEO_BUFFER[3][2] == gks.WHITE
    assert gks.VIDEO_BUFFER[3][6] == gks.WHITE
    assert gks.VIDEO_BUFFER[3][4] != gks.WHITE


def test_draw_filled_circle_pixels_are_inside_the_disk():
    """Filled circles should include the center and edge pixels that satisfy the radius check."""
    gks = GKS(8, 6)
    color = (44, 66, 88)

    gks.draw_filled_circle(4, 3, 2, color)

    assert gks.VIDEO_BUFFER[3][4] == color
    assert gks.VIDEO_BUFFER[1][4] == color
    assert gks.VIDEO_BUFFER[3][2] == color
    assert gks.VIDEO_BUFFER[0][0] != color


def test_draw_filled_circle_span_draws_scanlines_across_the_disk():
    """Filled circles should include the center and edge pixels that satisfy the radius check."""
    gks = GKS(8, 6)
    color = (2, 4, 6)

    gks.draw_filled_circle_span(4, 3, 2, color)

    assert gks.VIDEO_BUFFER[1][4] == color
    assert gks.VIDEO_BUFFER[3][4] == color
    assert gks.VIDEO_BUFFER[3][2] == color
    assert gks.VIDEO_BUFFER[0][0] != color


def test_paint_frame_outputs_ansi_color_sequences(capsys):
    """The frame renderer should convert the buffer into terminal escape sequences."""
    gks = GKS(8, 6)
    gks.set_pixel(0, 0, (255, 0, 0))
    gks.set_pixel(1, 1, (0, 255, 0))

    gks.paint_frame()

    output = capsys.readouterr().out
    assert "\x1b[48;2;255;0;0m" in output
    assert "\x1b[38;2;0;255;0m" in output
    assert gks.LOWER_BLOCK in output
    assert gks.RESET in output
