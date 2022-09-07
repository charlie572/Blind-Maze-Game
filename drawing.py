from math import cos, sin, pi
from typing import Tuple
import numpy as np
import pyglet as pyglet

from ray_casting import ray_cast
from maze import Maze


class Scene:
    """Allows you to draw primitives from the perspective of a camera

    The camera can be transformed using scene.set_camera_position() and scene.zoom(), and by modifying, scene.rotation,
    scene.scale_factor, scene.flip_horizontally, and scene.flip_vertically.

    :param width: Width in pixels
    :param height: Height in pixels
    :var rotation: Anticlockwise rotation in radians that is applied to the scene
    :var scale_factor: Scale factor that is applied to the scene
    :var flip_horizontally: Boolean specifying if the scene should be flipped horizontally
    :var flip_vertically: Boolean specifying if the scene should be flipped vertically
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self._translation = np.zeros(2, dtype=np.float64)
        self.rotation = 0.0
        self.scale_factor = 1.0
        self.flip_horizontally = False
        self.flip_vertically = False

    def camera_matrix(self):
        """
        :return: A 3x3 matrix that is used to transform coordinates before they are displayed.
        """
        result = np.identity(3, dtype=np.float64)
        result[:2, 2] = self._translation
        result = self.rotation_matrix() @ result
        result *= self.scale_factor
        result[:2, 2] += self.width / 2, self.height / 2

        if self.flip_horizontally:
            result[0, 0] *= -1
            result[0, 2] = self.width - result[0, 2]
        if self.flip_vertically:
            result[1, 1] *= -1
            result[1, 2] = self.height - result[1, 2]

        return result

    def rotation_matrix(self, three_by_three=True):
        """
        :param three_by_three: If True, a 3x3 matrix will be returned. Else, a 2x2 matrix will be returned.
        :return: A matrix that is used to rotate coordinates before they are displayed
        """
        result = np.array([[cos(self.rotation), sin(self.rotation)],
                           [-sin(self.rotation), cos(self.rotation)]], dtype=np.float64)

        if three_by_three:
            _result = np.identity(3, dtype=np.float64)
            _result[:2, :2] = result
            return _result

        return result

    def draw_rect(self, x: float, y: float, width: float, height: float, colour: Tuple[int, int, int, int]):
        """Draw a rectangle from the perspective of the camera.

        :param x:
        :param y:
        :param width:
        :param height:
        :param colour: red, green, blue, alpha. The values in [0, 127].
        """
        points = np.array([[x, y, 1],
                           [x + width, y, 1],
                           [x + width, y + height, 1],
                           [x, y + height, 1]], dtype=np.float64)
        points = (self.camera_matrix() @ points.T).T

        pyglet.gl.glColor4b(*colour)
        pyglet.gl.glBegin(pyglet.gl.GL_QUADS)
        for x, y, _ in points:
            pyglet.gl.glVertex2f(x, y)
        pyglet.gl.glEnd()

    def draw_line(self, x1: float, y1: float, x2: float, y2: float, colour: Tuple[int, int, int, int],
                  line_width: int = 1):
        """Draw a line from the perspective of the camera

        :param x1:
        :param y1:
        :param x2:
        :param y2:
        :param colour: red, green, blue, alpha. The values in [0, 127].
        :param line_width:
        """
        points = np.array([[x1, y1, 1],
                           [x2, y2, 1]], dtype=np.float64)
        points = (self.camera_matrix() @ points.T).T

        pyglet.gl.glColor4b(*colour)
        pyglet.gl.glLineWidth(line_width)
        pyglet.gl.glBegin(pyglet.gl.GL_LINES)
        for x, y, _ in points:
            pyglet.gl.glVertex2f(x, y)
        pyglet.gl.glEnd()

    def set_camera_position(self, x: float, y: float):
        """Position the camera

        This coordinate will be placed at the centre of the screen.

        :param x:
        :param y:
        """
        self._translation[:] = -x, -y

    def zoom(self, zoom_factor: float):
        """Zoom the camera in

        This is relative to the current zoom level.

        :param zoom_factor:
        """
        self.scale_factor *= zoom_factor

    def rotate_vector(self, x: float, y: float, invert: bool = False):
        """Rotate a vector to where it would be displayed

        :param x:
        :param y:
        :param invert: If True, the inverse rotation will be applied
        """
        rotation_matrix = self.rotation_matrix(three_by_three=False)
        if invert:
            rotation_matrix = np.linalg.inv(rotation_matrix)

        vector = np.array([x, y], dtype=np.float64).reshape(-1, 1)
        vector = rotation_matrix @ vector
        return vector.reshape(-1)

    def transform_point(self, x, y, invert=False) -> np.ndarray:
        """Transform a point to where it would be displayed

        :param x:
        :param y:
        :param invert: If True, the inverse transformation will be applied.
        """
        point = np.array([x, y, 1], dtype=np.float64).reshape(-1, 1)

        camera_matrix = self.camera_matrix()
        if invert:
            camera_matrix = np.linalg.inv(camera_matrix)
            point[2] = self.scale_factor

        point = camera_matrix @ point

        return point[:2, 0]


def draw_ray_casts(cell_size, x, y, maze, num_rays=64, line_width=1, colour=(0, 0, 0, 127)):
    """Cast rays out from the given position, and display them

    :param cell_size:
    :param x:
    :param y:
    :param maze:
    :param num_rays:
    :param line_width:
    :param colour:
    :return:
    """
    pyglet.gl.glColor4b(*colour)
    pyglet.gl.glLineWidth(line_width)

    for ray_num in range(num_rays):
        angle = 2 * pi / num_rays * ray_num
        dx = sin(angle)
        dy = cos(angle)
        end_x, end_y = ray_cast(x, y, dx, dy, maze)

        pyglet.gl.glBegin(pyglet.gl.GL_LINES)
        pyglet.gl.glVertex2f(x * cell_size, y * cell_size)
        pyglet.gl.glVertex2f(end_x * cell_size, end_y * cell_size)
        pyglet.gl.glEnd()


def draw_maze(scene: Scene, maze: Maze, colour=(0, 0, 0, 127), line_width=1):
    """Draw a maze using a given scene

    :param scene:
    :param maze:
    :param colour: red, green, blue, alpha. The values in [0, 127].
    :param line_width:
    """
    pyglet.gl.glColor4b(*colour)
    pyglet.gl.glLineWidth(line_width)

    for row in maze:
        for cell in row:
            if cell.bottom:
                scene.draw_line(cell.x, cell.y + 1, cell.x + 1, cell.y + 1, colour, line_width=line_width)
            if cell.right:
                scene.draw_line(cell.x + 1, cell.y, cell.x + 1, cell.y + 1, colour, line_width=line_width)
