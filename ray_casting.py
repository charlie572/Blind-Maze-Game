from math import ceil, floor, pi, sin, cos
from typing import Generator
import numpy as np

from maze import Maze


def ray_cast(x: float, y: float, dx: float, dy: float, maze: Maze) -> np.ndarray:
    """Cast a ray through a maze

    :param x: Starting x position of the ray
    :param y: Starting y position of the ray
    :param dx: Dx and dy are used to specify the direction that the ray moves.
    :param dy:
    :param maze: The maze that the ray moves through
    :return: The position of the ray the first time it hits a wall
    """
    x_sign = 1 if dx > 0 else -1
    y_sign = 1 if dy > 0 else -1
    signs = np.array([x_sign, y_sign])

    x_inc = dx / abs(dy) if dy != 0 else float('inf')
    y_inc = dy / abs(dx) if dx != 0 else float('inf')

    if y_sign > 0:
        next_h_intersection = np.array([x + x_inc * (1 - y % 1), ceil(y)])
    else:
        next_h_intersection = np.array([x + x_inc * (y % 1), floor(y)])
    if x_sign > 0:
        next_v_intersection = np.array([ceil(x), y + y_inc * (1 - x % 1)])
    else:
        next_v_intersection = np.array([floor(x), y + y_inc * (x % 1)])

    if not np.all(np.isfinite(next_h_intersection)):
        next_h_intersection[:] = x_sign * np.inf, y_sign * np.inf
    if not np.all(np.isfinite(next_v_intersection)):
        next_v_intersection[:] = x_sign * np.inf, y_sign * np.inf

    while True:
        if np.all(signs * next_h_intersection <= signs * next_v_intersection):
            intersection = next_h_intersection
            if intersection[0] >= maze.width or intersection[1] >= maze.width:
                return intersection

            wall = maze.cell_at(floor(intersection[0]), round(intersection[1])).top
            next_h_intersection = intersection[0] + x_inc, intersection[1] + y_sign
        else:
            intersection = next_v_intersection
            if intersection[0] >= maze.width or intersection[1] >= maze.width:
                return intersection

            wall = maze.cell_at(round(intersection[0]), floor(intersection[1])).left
            next_v_intersection = intersection[0] + x_sign, intersection[1] + y_inc

        if wall:
            return intersection


def ray_casts(x, y, maze, num_rays=64) -> Generator[np.ndarray, None, None]:
    """Cast multiple evenly-spaced rays from a point through a maze

    :param x: Start x position of the rays
    :param y: Start y position of the rays
    :param maze: Maze that the rays move through
    :param num_rays: Number of rays to cast
    :return: Yields the position of each ray when it first hits a wall
    """
    for ray_num in range(num_rays):
        angle = 2 * pi / num_rays * ray_num
        dx = sin(angle)
        dy = cos(angle)
        yield ray_cast(x, y, dx, dy, maze)
