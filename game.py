from random import randint
import numpy as np

from maze import Maze, Cell


class Player:
    """A rectangle with a position and a velocity

    :param x:
    :param y:
    :param width:
    :param height:
    """
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = float(x)
        self.y = float(y)
        self.x_velocity = 0.0
        self.y_velocity = 0.0
        self.width = width
        self.height = height

    def center(self) -> np.ndarray:
        """
        :return: Position of the center of the rectangle
        """
        return np.array([self.x + self.width / 2, self.y + self.height / 2])

    def position(self) -> np.ndarray:
        """
        :return: Position of the origin of the rectangle
        """
        return np.array([self.x, self.y])

    def set_velocity(self, x_velocity: float, y_velocity: float):
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity

    def update(self, dt):
        """Add velocity * dt to position

        :param dt: Time since the last call in seconds.
        """
        self.x += self.x_velocity * dt
        self.y += self.y_velocity * dt


class Game:
    """Contains a player and a maze, and allows the player to walk around

    This class uses the coordinate system of the maze.

    :param maze: A pre-generated maze to use.
    """
    def __init__(self, maze: Maze, player_move_speed=5.0):
        self.maze = maze
        self.player = Player(randint(0, maze.width - 1) + 0.25, randint(0, maze.height - 1) + 0.25, 0.5, 0.5)
        self.player_move_speed = player_move_speed

    def current_cell(self) -> Cell:
        """
        :return: The cell that the player is currently in.
        """
        return self.maze.cell_at(*self.player.center().astype(np.int32))

    def set_player_move_direction(self, x_direction: int, y_direction: int):
        """
        :param x_direction: -1, 0, or 1
        :param y_direction: -1, 0, or 1
        """
        self.player.set_velocity(x_direction * self.player_move_speed, y_direction * self.player_move_speed)

    def update(self, dt):
        """
        :param dt: Time since the last call in seconds.
        """
        # Update player and process collisions with walls.
        # Collisions are processed by checking if the player is in a different cell to the last frame, and moving them
        # back if they have crossed a wall.

        last_cell = self.current_cell()
        self.player.update(dt)

        if last_cell.left and self.player.x < last_cell.x:
            self.player.x = last_cell.x
        elif last_cell.right and self.player.x + self.player.width >= last_cell.x + 1:
            self.player.x = last_cell.x + 1 - self.player.width
        if last_cell.top and self.player.y < last_cell.y:
            self.player.y = last_cell.y
        elif last_cell.bottom and self.player.y + self.player.height >= last_cell.y + 1:
            self.player.y = last_cell.y + 1 - self.player.height
