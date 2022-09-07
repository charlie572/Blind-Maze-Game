from math import atan2, pi
from typing import Tuple, Literal, Union, Generator
import numpy as np
import pyglet
from pyglet.window import key, mouse

from drawing import Scene
from game import Game
from ray_casting import ray_casts, ray_cast
from tts import TTSThread


class VisionTool:
    """Provides audio cues used to navigate the maze

    This is an abstract class. The subclasses can be used by calling vision_tool.update(dt) regularly, or binding the
    keyboard and mouse events, depending on which events the function needs, and if it needs the update function.

    This class keeps track of the keyboard state, the mouse button state, the mouse position, and the direction that the
    mouse is moving.

    :param game: Game that is being navigated
    :param scene: Scene that is being used to view the game. This is needed if the player rotates their perspective.
    """
    def __init__(self, game: Game, scene: Scene):
        self.game = game
        self.scene = scene
        self._key_state = key.KeyStateHandler()
        self._mouse_state = mouse.MouseStateHandler()
        self._mouse_position = np.zeros(2, dtype=np.float64)
        self._mouse_direction = np.zeros(2, dtype=np.float64)

    def update(self, dt):
        pass

    def on_key_press(self, symbol, modifiers):
        self._key_state.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self._key_state.on_key_release(symbol, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_position[:] = x, y
        self._mouse_direction[:] = dx, dy

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self._mouse_position[:] = x, y
        if dx != 0 and dy != 0:
            self._mouse_direction[:] = dx, dy

    def on_mouse_press(self, x, y, button, modifiers):
        self._mouse_position[:] = x, y
        self._mouse_state.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self._mouse_position[:] = x, y
        self._mouse_state.on_mouse_release(x, y, button, modifiers)


class ChordVisionTool(VisionTool):
    """Navigation using a chord

    Four notes are played. There is one in front of the player, one behind them, and one either side of them. These
    are sine waves with the notes of a chord.

    You can turn off particular notes using the keys 1-4.
    1 - turns off front note
    2 - turns off right note
    3 - turns off note behind you
    4 - turns off left note

    :param chord_shape: The chord shape that is played. Each note is an integer representing a number of half steps
                        above middle A. The notes are played from the front, left, behind, and right in that order. The
                        default is A Major 7.
    """
    def __init__(self, game: Game, scene: Scene, chord_shape: Tuple[int, int, int, int] = (0, 4, 7, 11)):
        super().__init__(game, scene)

        twelfth_root_of_2 = 2 ** (1 / 12)
        chord = [440 * twelfth_root_of_2 ** num_steps for num_steps in chord_shape]

        self.player_group = pyglet.media.PlayerGroup([pyglet.media.Player() for _ in range(4)])
        for player, note in zip(self.player_group.players, chord):
            sound = pyglet.media.synthesis.Sine(-1, frequency=note)
            player.queue(sound)
            player.min_distance = 0.1

        self.player_group.play()

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)

        # turn off notes
        if key._1 <= symbol <= key._4:
            self.player_group.players[symbol - key._1].pause()

    def on_key_release(self, symbol, modifiers):
        super().on_key_release(symbol, modifiers)

        # turn notes back on
        if key._1 <= symbol <= key._4:
            self.player_group.players[symbol - key._1].play()

    def update(self, dt):
        # find the positions that the notes should be played from using ray casts
        points = ray_casts(*self.game.player.position(), self.game.maze, num_rays=len(self.player_group.players))
        points = np.array(list(points))

        # change origin to the player, and scale up
        points -= self.game.player.center()
        points *= 5

        # change positions of sounds
        for player, (x, y) in zip(self.player_group.players, points):
            x, y = self.scene.rotate_vector(x, y)
            player.position = x, 0.0, y


class ChordVisionToolWithBeeps(ChordVisionTool):
    """Beeping noises are used, and the beep frequency is higher for walls that are further away"""
    def __init__(self, game, scene, chord_shape=(0, 4, 7, 11)):
        super().__init__(game, scene, chord_shape=chord_shape)

        positions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for i, (x, y) in enumerate(positions):
            self.player_group.players[i].position = x * 5.0, 0.0, y * 5.0

        self.phases = [0.0] * len(self.player_group.players)

    def update(self, dt):
        # find the positions that the notes should be played from using ray casts
        points = ray_casts(*self.game.player.position(), self.game.maze, num_rays=len(self.player_group.players))
        points = np.array(list(points))

        # change origin to the player, and scale up
        points -= self.game.player.center()

        for i, (point, player) in enumerate(zip(points, self.player_group.players)):
            modulation_frequency = np.sum(point) * 2.0
            self.phases[i] = (self.phases[i] + dt * modulation_frequency) % 1.0
            if self.phases[i] < 0.5:
                player.play()
            else:
                player.pause()


class SingleRayCastTool(VisionTool):
    """Use a single ray in the direction of that the mouse is moving, and use volume to indicate distance to nearest
    wall

    Higher volume = closer.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.player = pyglet.media.Player()
        self.player.queue(pyglet.media.synthesis.Sine(-1))

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.player.play()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.player.pause()

    def update(self, dt):
        if np.all(self._mouse_direction == 0):
            return

        vector = self._mouse_direction.copy()
        vector /= np.linalg.norm(vector)
        vector[1] *= -1
        point = ray_cast(*self.game.player.center(), *vector, self.game.maze)
        point -= self.game.player.center()
        point *= 5.0
        self.player.position = point[0], 0.0, point[1]


class HallwayCheckTool(VisionTool):
    """Allows the player to check the turnings down a hallway

    The player uses the arrow keys to send a 'drone' in a particular direction. The drone will move in that direction.
    If there is a wall on both sides of it, it will beep. If there is no wall in the anticlockwise direction from the
    player, it will make a sound that pitches down. If there is a wall in the clockwise direction, it will pitch up.
    If there are no walls either side of it, both sounds will be played. It will move along the hall until it hits the
    wall at the end.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.anticlockwise_sound = pyglet.media.load('pitch_down.wav')
        self.clockwise_sound = pyglet.media.load('pitch_up.wav')
        self.null_sound = pyglet.media.synthesis.Sine(0.1, 440)
        self.stop_sound = pyglet.media.synthesis.Sine(0.1, 220)

        self._player = pyglet.media.Player()

        self._coroutine_running = None

    def start_hallway_check(self, direction: Union[Literal['left', 'up', 'right', 'down'], int], cells_per_second=2.0):
        if self._coroutine_running is not None:
            self._coroutine_running.close()

        self._coroutine_running = self.hallway_check_coroutine(direction, cells_per_second=cells_per_second)

        try:
            next(self._coroutine_running)
        except StopIteration:
            pass

    def hallway_check_coroutine(self, direction: Union[Literal['left', 'up', 'right', 'down'], int],
                                cells_per_second=2.0) -> Generator[None, float, None]:
        """A coroutine used to effect a drone moving along a corridor

        Send this coroutine the delta time since the last send. It will play the sounds described in the class
        docstring.

        :param direction: Direction that the drone moves. This can be a string, or a number between 0 and 3. 0 is left,
                          and subsequent numbers move anticlockwise.
        :param cells_per_second: Speed of the drone in cells per second.
        :return:
        """
        if type(direction) is str:
            direction = ['left', 'up', 'right', 'down'].index(direction)

        velocity = np.zeros(2, dtype=np.float64)
        if direction % 2 == 0:
            velocity[0] = direction - 1
        else:
            velocity[1] = direction - 2
        velocity *= cells_per_second

        position = np.floor([self.game.player.x, self.game.player.y], dtype=np.float64)

        current_cell = self.game.maze.cell_at(*position.astype(np.int32))
        while not current_cell.walls[direction]:
            dt = (yield)
            position += velocity * dt

            next_cell = self.game.maze.cell_at(*position.astype(np.int32))
            if next_cell == current_cell:
                continue

            anti_clockwise_wall = next_cell.walls[(direction - 1) % 4]
            clockwise_wall = next_cell.walls[(direction + 1) % 4]
            if not anti_clockwise_wall:
                self._player.queue(self.anticlockwise_sound)
            if not clockwise_wall:
                self._player.queue(self.clockwise_sound)
            if anti_clockwise_wall and clockwise_wall:
                self._player.queue(self.null_sound)

            self._player.play()

            current_cell = next_cell

        self._player.queue(self.stop_sound)

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)

        if key.LEFT <= symbol <= key.DOWN:
            self.start_hallway_check(symbol - key.LEFT)

    def update(self, dt):
        if self._coroutine_running is None:
            return

        try:
            self._coroutine_running.send(dt)
        except StopIteration:
            self._coroutine_running = None


class FootstepsTool(VisionTool):
    """Play a footstep sound while the player is moving"""
    def __init__(self, game, scene):
        super().__init__(game, scene)

        sound = pyglet.media.load('footsteps.wav')
        self.player = pyglet.media.Player()
        self.player.loop = True
        self.player.volume = 0.2
        self.player.queue(sound)

        self._last_position = self.game.player.position()

    def update(self, dt):
        if np.any(self._last_position != self.game.player.position()):
            self.player.play()
        else:
            self.player.pause()

        self._last_position = self.game.player.position()


class ChangingCellNotificationTool(VisionTool):
    """Play a sound whenever the player moves to a new cell

    If the player moves to a new cell horizontally, a click sound is played. If they move to a new cell vertically, a
    whoosh sound is played. If the player is moving diagonally, then having different sounds helps tells the player if
    they are moving against a wall.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.horizontal_sound = pyglet.media.load('click.wav')
        self.vertical_sound = pyglet.media.load('whoosh.wav')
        self.player = pyglet.media.Player()

        self._last_cell = self.game.current_cell()

    def update(self, dt):
        next_cell = self.game.current_cell()
        if next_cell == self._last_cell:
            return

        if self._last_cell.x != next_cell.x:
            self.player.queue(self.horizontal_sound)
        if self._last_cell.y != next_cell.y:
            self.player.queue(self.vertical_sound)

        self.player.play()

        self._last_cell = next_cell


class SurroundCheckTool(VisionTool):
    """Allow the player to press a button which will check the immediate surrounding walls

    It checks to the left, then top, then right, them bottom of the player. If there is a wall there, it makes a click
    sound. Else, it makes a bell sound. Press space to do the check.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.no_wall_sound = pyglet.media.load('bell.wav')
        self.wall_sound = pyglet.media.load('click.wav')

        self.player = pyglet.media.Player()

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)

        if symbol != key.SPACE:
            return

        while self.player.source is not None:
            self.player.next_source()

        cell = self.game.current_cell()
        for wall_present in cell.walls:
            self.player.queue(self.wall_sound if wall_present else self.no_wall_sound)

        self.player.play()


class BreadcrumbTool(VisionTool):
    """Allow the player to place markers, and notify them when they return to a marker

    Press E to place a marker. It will say a number that will be associated with that marker. Whenever the player
    returns to that marker, it will say that number again.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.tts_thread = TTSThread()
        self.tts_thread.setDaemon(True)
        self.tts_thread.start()

        self.breadcrumbs = {}

        self._last_cell = self.game.current_cell()

    def on_key_press(self, symbol, modifiers):
        if symbol != key.E:
            return

        cell = self.game.current_cell()
        if cell not in self.breadcrumbs:
            self.breadcrumbs[cell] = len(self.breadcrumbs)
            self.tts_thread.say(str(len(self.breadcrumbs) - 1))
        else:
            self.tts_thread.say(str(self.breadcrumbs[cell]))

    def update(self, dt):
        next_cell = self.game.current_cell()
        if next_cell == self._last_cell:
            return

        if next_cell in self.breadcrumbs:
            breadcrumb_number = self.breadcrumbs[next_cell]
            self.tts_thread.say(str(breadcrumb_number))

        self._last_cell = next_cell


class CombinedTool(VisionTool):
    """HallwayCheckVisionTool, ChangingCellNotificationTool, SurroundCheckTool, and BreadcrumbTool

    Instead of using arrow keys for the HallwayCheckTool, you can send the drone by moving the mouse, and pressing and
    releasing the right mouse button.
    """
    def __init__(self, game, scene):
        super().__init__(game, scene)

        self.hallway_check_tool = HallwayCheckTool(game, scene)
        self.cell_change_tool = ChangingCellNotificationTool(game, scene)
        self.surround_check_tool = SurroundCheckTool(game, scene)
        self.breadcrumb_tool = BreadcrumbTool(game, scene)

    def on_key_press(self, symbol, modifiers):
        super().on_key_press(symbol, modifiers)
        self.surround_check_tool.on_key_press(symbol, modifiers)
        self.breadcrumb_tool.on_key_press(symbol, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.RIGHT:
            angle = atan2(self._mouse_direction[1], -self._mouse_direction[0]) % (2 * pi)
            direction = int((angle + pi / 4) // (pi / 2)) % 4
            self.hallway_check_tool.start_hallway_check(direction)

        super().on_mouse_release(x, y, button, modifiers)

    def update(self, dt):
        super().update(dt)
        self.hallway_check_tool.update(dt)
        self.cell_change_tool.update(dt)
        self.breadcrumb_tool.update(dt)
