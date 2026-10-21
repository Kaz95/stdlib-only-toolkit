"""Functions for the Sweet Dreams Bakery internal operations program."""
from math import pi

def halve_recipe(butter: float, sugar: float, flour: float) -> None:
    print('Half Batch Shortbread Recipe')
    print('-' * 35)
    print(f'{butter / 2}\t C Butter')
    print(f'{sugar / 2}\t C Sugar')
    print(f'{flour / 2}\t C Flour')


def calc_circle_area(diameter: float) -> float:
    radius = diameter / 2
    return pi * (radius ** 2)

def calc_slices(diam1:int, diam2=0, diam3=0) -> float:
    total_area = 0
    first_tier_area = calc_circle_area(diam1)
    total_area += first_tier_area
    if diam2 > 0:
        second_tier_area = calc_circle_area(diam2)
        total_area += second_tier_area
    if diam3 > 0:
        third_tier_area = calc_circle_area(diam3)
        total_area += third_tier_area

    slices = total_area / 7.34
    return slices

if __name__ == '__main__':
    # pass
    halve_recipe(1, .75, 2)
    print('-' * 35)
    print('\n\n')
    print(f"A one-tier cake with a 20-inch diameter will serve{calc_slices(20): .0f} guests.")
    print(f"A two-tier cake with a 20- and 16-inch diameters will serve{calc_slices(20, 16): .0f} guests.")
    print(f"A three-tier cake with a 20-, 16-, and 12-inch diameters will serve{calc_slices(20, 16, 12): .0f} guests.")