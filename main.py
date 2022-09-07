from typing import Type, Optional
import numpy as np
import pyglet as pyglet
import pyttsx3
from pyglet.window import key, mouse

from drawing import Scene, draw_maze
from game import Game
from maze import Maze
import vision_tools


def run_main_game(game: Game, VisionTool: Type[vision_tools.VisionTool], window_width: int, window_height: int,
                  cell_size: float, game_duration: Optional[float] = None):
    """Run the main game

    This will allow the player to walk around the maze, navigating using an instance of VisionTool. A window will be
    created and closed when the game ends.

    :param game: Game containing the maze and player to use
    :param VisionTool: A subclass of vision_tools.VisionTool. An instance of this will be created and used to navigate.
    :param window_width: Width of the window in pixels
    :param window_height: Height of the window in pixels
    :param cell_size: The side length of a cell of the maze in pixels. This determines the size at which the maze will
                      be drawn.
    :param game_duration: If specified, the game will terminate after this duration in seconds.
    """
    window = pyglet.window.Window(window_width, window_height, 'Maze')
    window.set_exclusive_mouse(True)
    pyglet.gl.glClearColor(1, 1, 1, 1)

    scene = Scene(window_width, window_height)
    scene.zoom(cell_size)

    # The coordinate system of the maze is flipped vertically relative to the coordinate system of pyglet, so we flip
    # the scene.
    scene.flip_vertically = True

    vision_tool = VisionTool(game, scene)
    window.push_handlers(vision_tool)

    keys = key.KeyStateHandler()
    window.push_handlers(keys)

    @window.event
    def on_draw():
        window.clear()
        draw_maze(scene, game.maze)
        scene.draw_rect(game.player.x, game.player.y, game.player.width, game.player.height, (0, 0, 0, 1))

    def update(dt):
        # set player move direction and update game
        x_direction = int(keys[key.D]) - int(keys[key.A])
        y_direction = int(keys[key.S]) - int(keys[key.W])
        x_direction, y_direction = scene.rotate_vector(x_direction, y_direction, invert=True)
        game.set_player_move_direction(x_direction, y_direction)
        game.update(dt)

        scene.set_camera_position(game.player.x, game.player.y)

        vision_tool.update(dt)

    if game_duration is not None:
        pyglet.clock.schedule_once(lambda dt: pyglet.app.exit(), game_duration)

    pyglet.clock.schedule_interval(update, 1 / 30)
    pyglet.app.run()

    pyglet.clock.unschedule(update)
    window.close()


def prompt_for_final_position(game: Game, window_width: int, window_height: int, cell_size: float):
    """Prompt the user to click on the cell of the maze that they think they are currently in

    A window will open with an image of the maze. The user will click on a cell. The correct cell will then be displayed
    in green, and the user's guess will be displayed in red if it was incorrect. The window will close when the user
    exits.

    :param game: Game containing the maze and player position to use
    :param window_width: Width of the window in pixels
    :param window_height: Height of the window in pixels
    :param cell_size: The side length of a cell of the maze in pixels. This determines the size at which  the maze will
                      be drawn.
    """
    pyttsx3.speak('Your time is up. Click where you think you finished')

    window = pyglet.window.Window(window_width, window_height, 'Click where you think you finished')
    pyglet.gl.glClearColor(1, 1, 1, 1)

    scene = Scene(window_width, window_height)
    scene.zoom(cell_size)
    scene.flip_vertically = True
    scene.set_camera_position(game.maze.width // 2, game.maze.height // 2)

    final_cell = game.current_cell()

    # actual and guessed final positions of the player in cells
    actual_position = np.array([final_cell.x, final_cell.y], dtype=np.float64)
    guessed_position = np.array([-1, -1], dtype=np.float64)

    @window.event
    def on_draw():
        window.clear()
        draw_maze(scene, game.maze)

        if np.all(guessed_position > -1):
            scene.draw_rect(*guessed_position, 1.0, 1.0, (127, 0, 0, 127))
            scene.draw_rect(*actual_position, 1.0, 1.0, (0, 127, 0, 127))

    @window.event
    def on_mouse_press(x, y, button, modifiers):
        if np.all(guessed_position > -1):
            return
        if button != mouse.LEFT:
            return

        guessed_position[:] = np.floor(scene.transform_point(x, y, invert=True))

    pyglet.app.run()
    window.close()


def main():
    # I get an error when using the CombinedTool unless I add this line. It must be a bug with pyttsx3.
    pyttsx3.init()

    maze = Maze(20, 20)
    maze.generate()
    game = Game(maze)

    run_main_game(game, vision_tools.CombinedTool, 960, 720, 100.0, 60.0)
    prompt_for_final_position(game, 960, 720, 20.0)


if __name__ == '__main__':
    main()
