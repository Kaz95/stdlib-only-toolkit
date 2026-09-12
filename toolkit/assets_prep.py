"""A standalone script for downscaling and pulling bitmaps from images.

Decided to make this a standalone script. I'll probably just include the final bitmap data in the final project. My
hope is to be able to reuse this in the future, similar to the basic font set and drawing class I'm using.
"""
import shutil, json
import urllib.request

from PIL import Image
from animator import play_animation_sequence, precompute_interpolation_frames

TERMINAL_WIDTH, _ = shutil.get_terminal_size()
panera_logo_bitmap_remote = ('https://raw.githubusercontent.com/Kaz95/stdlib-only-toolkit/refs/heads/master/assets'
                             '/generated/panera_logo_bitmap.json')
TARGET_HEIGHT = 80
TARGET_WIDTH = 80


def extract_bitmap():
    img = Image.open('../assets/source_images/Panera-Bread-Logo-cropped-squared.png')
    img = img.convert('RGB')
    width, height = img.size

    print(width)
    print(height)

    downscaled_img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    print(f'{downscaled_img.width}, {downscaled_img.height}')
    pixel_matrix = []
    for y_coord in range(TARGET_HEIGHT):
        row_of_pixels = []
        for x_coord in range(TARGET_WIDTH):
            r, g, b = downscaled_img.getpixel((x_coord, y_coord))
            if (r, g, b) == (0, 0, 0):
                row_of_pixels.append((12, 12, 12))
            else:
                row_of_pixels.append((r, g, b))
        pixel_matrix.append(row_of_pixels)

    return pixel_matrix


def dump_pixel_matrix(bitmap):
    with open("../assets/generated/panera_logo_bitmap.json", "w", encoding="utf-8") as file:
        json.dump(bitmap, file, indent=4)


def load_bitmap(remote_bitmap):
    with urllib.request.urlopen(remote_bitmap) as response:
        panera_logo_bitmap = json.load(response)
        return panera_logo_bitmap


if __name__ == '__main__':
    # panera_logo_bitmap = load_bitmap(panera_logo_bitmap_remote)
    # play_animation_sequence(panera_logo_bitmap)
    bitmap = extract_bitmap()
    dump_pixel_matrix(bitmap)
