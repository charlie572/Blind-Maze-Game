from dataclasses import dataclass
from random import shuffle
import numpy as np


@dataclass(frozen=True)
class Cell:
    """A cell in a maze

    :var x: X position in cells
    :var y: Y position in cells
    :var left: Is there a wall on the left?
    :var right: Is there a wall on the right?
    :var top: Is there a wall on the top?
    :var bottom: Is there a wall on the bottom?
    """
    x: int
    y: int
    left: bool
    right: bool
    top: bool
    bottom: bool

    @property
    def walls(self):
        return self.left, self.top, self.right, self.bottom


class Maze:
    """A randomly-generated maze

    Generate() must be called after the maze is instantiated.

    :param width: Width of the maze in cells
    :param height: Height of the maze in cells
    """
    def __init__(self, width, height):
        self.grid = np.full((height, width), 15, dtype=np.uint8)
        self._visited = np.zeros((height, width), dtype=np.bool_)
        self.width = width
        self.height = height

    def generate(self):
        self.grid[:, :] = 15
        self._visited[:, :] = False
        self._generate(0, 0)

    def _generate(self, x, y):
        self._visited[y, x] = True

        # iterate through neighbours randomly
        wall_numbers_and_offsets = list(enumerate([(0, -1), (-1, 0), (0, 1), (1, 0)]))
        shuffle(wall_numbers_and_offsets)
        for w, (dx, dy) in wall_numbers_and_offsets:
            i, j = x + dx, y + dy

            if i < 0 or i >= self.width or j < 0 or j >= self.height:
                continue
            if self._visited[j, i]:
                continue

            # remove wall in this cell and the next cell
            wall_mask = 1 << w
            if wall_mask >= 4:
                opposite_wall_mask = wall_mask >> 2
            else:
                opposite_wall_mask = wall_mask << 2
            self.grid[y, x] = self.grid[y, x] & ~wall_mask
            self.grid[j, i] = self.grid[j, i] & ~opposite_wall_mask

            # proceed to the next cell recursively
            self._generate(i, j)

    def cell_at(self, x: int, y: int) -> Cell:
        """Get information about the walls surrounding a cell

        :param x:
        :param y:
        :return:
        """
        cell = self.grid[y, x]
        cell = Cell(x, y, bool(cell & 2), bool(cell & 8), bool(cell & 1), bool(cell & 4))
        return cell

    def __iter__(self):
        return ((self.cell_at(x, y) for x in range(self.width)) for y in range(self.height))


def maze_as_ascii(maze: Maze) -> str:
    result = ''
    for row in maze:
        for cell in row:
            result += '_' if cell.bottom else ' '
            result += '|' if cell.right else ' '

        result += '\n'

    return result


def main():
    maze = Maze(30, 15)
    maze.generate()

    print(maze_as_ascii(maze))


if __name__ == '__main__':
    main()
