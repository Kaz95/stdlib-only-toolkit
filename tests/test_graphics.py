"""Regression tests for the terminal graphics primitives.

TODO
    * boundary/edge-case tests
    * negative coordinate or out-of-bounds tests
    * very small shapes
    * zero-radius / zero-width / zero-height tests
    * line tests for descending coordinates and diagonals
    * property-style tests for symmetry and fill behavior
"""
from unittest.mock import patch

import pytest

from toolkit import graphics
from toolkit.graphics import GKS


def test_constructor_initializes_blank_buffer():
    """The canvas should start as a black, correctly sized grid."""
    gks = GKS(8, 6)

    assert gks.width == 8
    assert gks.height == 6
    assert len(gks.video_buffer) == 6
    assert len(gks.video_buffer[0]) == 8
    assert all(pixel == gks.BLACK for row in gks.video_buffer for pixel in row)


def test_clear_restores_black_pixels():
    """Clearing should erase any previous drawing by resetting every pixel."""
    gks = GKS(8, 6)
    gks.set_pixel(2, 3, (10, 20, 30))

    gks.clear()

    assert gks.video_buffer[3][2] == gks.BLACK


def test_set_pixel_writes_color_to_buffer():
    """A single pixel should be written at the requested coordinate."""
    gks = GKS(8, 6)
    color = (12, 34, 56)

    gks.set_pixel(4, 2, color)

    assert gks.video_buffer[2][4] == color


@pytest.mark.parametrize(
    "bit_index, expected",
    [
        (0, 1),
        (1, 0),
        (2, 1),
        (3, 0),
        (4, 0),
        (5, 1),
        (6, 0),
        (7, 1),
    ],
)
def test_get_pixel_returns_bit_at_index(bit_index, expected):
    """Bits are read from left to right within the configured width."""
    assert GKS.get_pixel(0b10100101, bit_index) == expected


@pytest.mark.parametrize("bit_index", [-1, 8])
def test_get_pixel_rejects_invalid_bit_index(bit_index):
    """A bit index outside the configured width should be rejected."""
    with pytest.raises(ValueError, match="Bit index out of range"):
        GKS.get_pixel(0b10100101, bit_index)


def test_get_pixel_uses_custom_width():
    """Bits are correctly read when using custom width."""
    assert GKS.get_pixel(0b1010, 0, width=4) == 1
    assert GKS.get_pixel(0b1010, 3, width=4) == 0


@pytest.fixture
def gks_with_test_font():
    """Create a graphics surface with small deterministic test glyphs."""
    test_font = {
        "A": [0x80] + [0x00] * 7,
        "B": [0x00] * 6 + [0x01, 0x00],
    }
    with patch.object(GKS, "load_font", return_value=test_font):
        yield GKS(24, 8)


def test_paint_chars_maps_word_to_glyphs(gks_with_test_font):
    """Each character in the word should use its corresponding glyph data."""
    gks = gks_with_test_font

    gks.paint_chars("AB", 2, 1)

    assert gks.video_buffer[1][2] == gks.WHITE
    assert gks.video_buffer[7][17] == gks.WHITE


def test_paint_chars_offsets_each_glyph_to_the_right(gks_with_test_font):
    """Glyphs should be placed in consecutive eight-pixel columns."""
    gks = gks_with_test_font

    gks.paint_chars("AA", 3, 2)

    assert gks.video_buffer[2][3] == gks.WHITE
    assert gks.video_buffer[2][11] == gks.WHITE
    assert gks.video_buffer[2][19] == gks.BLACK


def test_paint_chars_paints_all_glyphs_and_preserves_color(gks_with_test_font):
    """Every glyph should update the video buffer using the requested color."""
    gks = gks_with_test_font
    color = (12, 34, 56)

    gks.paint_chars("AB", 0, 0, color)

    assert gks.video_buffer[0][0] == color
    assert gks.video_buffer[6][15] == color
    assert gks.video_buffer[0][8] == gks.BLACK


def test_paint_chars_maps_lowercase_words_to_uppercase_glyphs(gks_with_test_font):
    """Lowercase input should resolve to the corresponding uppercase glyphs."""
    gks = gks_with_test_font

    gks.paint_chars("ab", 0, 0)

    assert gks.video_buffer[0][0] == gks.WHITE
    assert gks.video_buffer[6][15] == gks.WHITE


def test_paint_chars_rejects_unsupported_character(gks_with_test_font):
    """Words containing characters absent from the font should be rejected."""
    with pytest.raises(ValueError, match="Character not available in font"):
        gks_with_test_font.paint_chars("A?", 0, 0)


def test_blit_places_bitmap_at_valid_position():
    """A bitmap should be copied into the buffer at the requested origin."""
    gks = GKS(5, 4)
    bitmap = [
        [(1, 2, 3), (4, 5, 6)],
        [(7, 8, 9), (10, 11, 12)],
    ]

    gks.blit(bitmap, 2, 1)

    assert gks.video_buffer[1][2:4] == bitmap[0]
    assert gks.video_buffer[2][2:4] == bitmap[1]


@pytest.mark.parametrize("x_start, y_start", [(4, 0), (0, 3), (-1, 0), (0, -1)])
def test_blit_rejects_bitmap_outside_video_buffer(x_start, y_start):
    """A bitmap that does not fit within the buffer should be rejected."""
    gks = GKS(5, 4)
    bitmap = [[gks.WHITE, gks.WHITE], [gks.WHITE, gks.WHITE]]

    with pytest.raises(ValueError, match="Bitmap does not fit"):
        gks.blit(bitmap, x_start, y_start)


def test_blit_pixels_match_bitmap():
    """Every destination pixel should match the corresponding bitmap pixel."""
    gks = GKS(5, 4)
    bitmap = [
        [(10, 20, 30), (40, 50, 60)],
        [(70, 80, 90), (100, 110, 120)],
    ]

    gks.blit(bitmap, 1, 1)

    for bitmap_y, row in enumerate(bitmap):
        for bitmap_x, pixel in enumerate(row):
            assert gks.video_buffer[bitmap_y + 1][bitmap_x + 1] == pixel


def test_blit_defaults_to_top_left_origin():
    """Omitting coordinates should place the bitmap at (0, 0)."""
    gks = GKS(4, 3)
    bitmap = [[(1, 2, 3), (4, 5, 6)]]

    gks.blit(bitmap)

    assert gks.video_buffer[0][:2] == bitmap[0]


def test_draw_line_draws_horizontal_and_vertical_segments():
    """Line drawing must cover the full segment, including axis-aligned lines."""
    gks = GKS(8, 6)
    color = (255, 0, 0)

    gks.draw_line(1, 1, 4, 1, color)
    for x in range(1, 5):
        assert gks.video_buffer[1][x] == color

    gks.draw_line(6, 1, 6, 4, (0, 255, 0))
    for y in range(1, 5):
        assert gks.video_buffer[y][6] == (0, 255, 0)


def test_draw_bresenhams_line_draws_diagonal_points():
    """Bresenham should produce a predictable line through integer raster coordinates."""
    gks = GKS(8, 6)
    color = (0, 0, 255)

    gks.draw_bresenhams_line(0, 0, 4, 2, color)

    assert gks.video_buffer[0][0] == color
    assert gks.video_buffer[2][4] == color
    assert gks.video_buffer[1][2] == color


def test_draw_rect_draws_only_the_border():
    """Rectangles are defined by their edges, not by their filled interior."""
    gks = GKS(8, 6)
    color = (255, 0, 255)

    gks.draw_rect(1, 1, 4, 3, color)

    assert gks.video_buffer[1][1] == color
    assert gks.video_buffer[1][4] == color
    assert gks.video_buffer[3][1] == color
    assert gks.video_buffer[3][4] == color
    assert gks.video_buffer[2][2] != color


def test_draw_filled_rect_fills_the_entire_area():
    """Filled rectangles must paint every pixel inside the rectangle bounds."""
    gks = GKS(8, 6)
    color = (12, 13, 14)

    gks.draw_filled_rect(1, 1, 3, 2, color)

    for y in range(1, 3):
        for x in range(1, 4):
            assert gks.video_buffer[y][x] == color


def test_old_draw_circle_preserves_requested_color():
    """The legacy circle method should draw an unfilled circle of the given radius."""
    gks = GKS(8, 6)
    color = (9, 9, 9)

    gks.old_draw_circle(4, 3, 2, color)

    assert gks.video_buffer[1][4] == color
    assert gks.video_buffer[5][4] == color
    assert gks.video_buffer[3][2] == color
    assert gks.video_buffer[3][4] != color


def test_new_draw_circle_uses_eight_way_symmetry():
    """The midpoint circle algorithm should draw the expected symmetric points."""
    gks = GKS(8, 6)

    gks.new_draw_circle(4, 3, 2)

    assert gks.video_buffer[1][4] == gks.WHITE
    assert gks.video_buffer[5][4] == gks.WHITE
    assert gks.video_buffer[3][2] == gks.WHITE
    assert gks.video_buffer[3][6] == gks.WHITE
    assert gks.video_buffer[3][4] != gks.WHITE


def test_draw_filled_circle_pixels_are_inside_the_disk():
    """Filled circles should include the center and edge pixels that satisfy the radius check."""
    gks = GKS(8, 6)
    color = (44, 66, 88)

    gks.draw_filled_circle(4, 3, 2, color)

    assert gks.video_buffer[3][4] == color
    assert gks.video_buffer[1][4] == color
    assert gks.video_buffer[3][2] == color
    assert gks.video_buffer[0][0] != color


def test_draw_filled_circle_span_draws_scanlines_across_the_disk():
    """Filled circles should include the center and edge pixels that satisfy the radius check."""
    gks = GKS(8, 6)
    color = (2, 4, 6)

    gks.draw_filled_circle_span(4, 3, 2, color)

    assert gks.video_buffer[1][4] == color
    assert gks.video_buffer[3][4] == color
    assert gks.video_buffer[3][2] == color
    assert gks.video_buffer[0][0] != color


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


def test_paint_frame_paints_missing_bottom_row_black(capsys):
    """An odd-height frame should use black for the missing bottom half."""
    gks = GKS(1, 3)
    gks.set_pixel(0, 2, (255, 0, 0))

    gks.paint_frame()

    output = capsys.readouterr().out
    assert "\x1b[48;2;255;0;0m\x1b[38;2;0;0;0m" in output


def test_render_loop_sleeps_for_remaining_frame_time():
    """Remaining sleep time is frame duration - elapsed work."""
    gks = GKS(2, 2)

    # Simulate 3 ms of rendering work.
    def stop_after_sleep(_duration):
        gks.rendering = False

    with (
        patch.object(graphics.time, "perf_counter", side_effect=[10.000, 10.003]),
        patch.object(graphics.time, "sleep", side_effect=stop_after_sleep) as sleep,
        patch.object(gks, "paint_frame"),
    ):
        gks.start_render_loop(frame_rate=100)

    # 100 FPS = 0.01 seconds per frame.
    # 0.003 seconds was spent working, so 0.007 remains.
    # I would have used 60 fps to better test an expected use case, but the frame duration is a long float.
    # Maybe I should consider rounding it when it's set in the render loop?
    sleep.assert_called_once_with(pytest.approx(0.007))


@pytest.mark.parametrize("frame_rate", [30, 60, 100])
def test_frame_duration_is_based_on_frame_rate(frame_rate):
    """The loop schedules one frame every 1 / frame_rate seconds."""
    gks = GKS(2, 2)

    def stop_after_sleep(_duration):
        gks.rendering = False

    with (
        patch.object(graphics.time, "perf_counter", side_effect=[10.0, 10.0]),
        patch.object(graphics.time, "sleep", side_effect=stop_after_sleep) as sleep,
    ):
        gks.start_render_loop(frame_rate)

    sleep.assert_called_once_with(pytest.approx(1 / frame_rate))


def test_render_loop_iteration_includes_work_and_sleep():
    """Rendering work and the requested sleep together fill one frame duration."""
    gks = GKS(2, 2)
    work_duration = 0.003
    frame_duration = 1 / 100

    def stop_after_sleep(_duration):
        gks.rendering = False

    with (
        patch.object(graphics.time, "perf_counter", side_effect=[10.0, 10.0 + work_duration]),
        patch.object(graphics.time, "sleep", side_effect=stop_after_sleep) as sleep,
    ):
        gks.start_render_loop(100)

    sleep_duration = sleep.call_args.args[0]
    assert work_duration + sleep_duration == pytest.approx(frame_duration)


def test_set_pixel_marks_video_buffer_updated():
    """Writing a pixel marks the buffer as needing to be repainted to screen."""
    gks = GKS(2, 2)

    assert gks.buffer_updated is False

    gks.set_pixel(0, 0, gks.WHITE)

    assert gks.buffer_updated is True


@pytest.mark.parametrize("buffer_updated, expected_paint_calls", [(True, 1), (False, 0)])
def test_render_loop_draws_only_updated_video_buffer(buffer_updated, expected_paint_calls):
    """The loop only paints when the video buffer update flag is set."""
    gks = GKS(2, 2)
    gks.buffer_updated = buffer_updated

    def stop_after_sleep(_duration):
        gks.rendering = False

    with (
        patch.object(gks, "paint_frame") as paint_frame,
        patch.object(graphics.time, "perf_counter", return_value=10.0),
        patch.object(graphics.time, "sleep", side_effect=stop_after_sleep),
    ):
        gks.start_render_loop(60)

    assert paint_frame.call_count == expected_paint_calls
