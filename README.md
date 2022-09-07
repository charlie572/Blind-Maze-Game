# Blind Maze Game

This is an experimental maze game.

You are placed in a randomly generated maze, and you aren't allowed to see. Use WASD to move around. There some audio cues and tools you can use to help you navigate. After 60 seconds, the game will end, and you will be shown a map of the maze. You must click on the cell that you think you were in when the game ended. This can't actually be played by blind people at the moment because the bit at the end requires vision.

# Audio Cues and Tools

- A sound is played whenever the player moves to a new cell.
    
    If the player moves to a new cell horizontally, a click sound is played. If they move to a new cell vertically, a whoosh sound is played. If the player is moving diagonally, then having different sounds helps tells the player if they are moving against a wall.
- Press space to check the four surrounding walls.
    
    It checks to the left, then top, then right, them bottom of the player. If there is a wall there, it makes a click sound. Else, it makes a bell sound.
- The player can send a 'drone' in a particular direction. 

    The drone will move in that direction. If there is a wall on both sides of it, it will beep. If there is no wall in the anticlockwise direction from the player, it will make a sound that pitches down. If there is a wall in the clockwise direction, it will pitch up. If there are no walls either side of it, both sounds will be played. It will move along the hall until it hits the wall at the end. To send the drone, move the mouse in the desired direction, and press and release the right mouse button.
- The player can place markers, and will be notified when they return to them.
    
    Press E to place a marker. It will say a number that will be associated with that marker. Whenever the player returns to that marker, it will say that number again.

There are a few other tools (see vision_tools.py), but I found that they weren't very useful.

# Tasks

- Add support for a braille display to use when clicking the final position at the end. This would make the game fully playable by blind people.
- Add a different game mode where the player collects items and brings them back to the centre of the maze. This would require them to explore the maze more.

# Attribution

Sound effects were taken from [mixkit](https://mixkit.co/) under their [Sound Effects Free License](https://mixkit.co/license/#sfxFree) in September 2022.

Footsteps.wav was taken from ['Cartoon insect running fast' on mixkit](https://mixkit.co/free-sound-effects/footsteps/).

Bell.wav was taken from ['Bike notification bell'](https://mixkit.co/free-sound-effects/bell/).

Whoosh.wav was taken from [Medium size bird flutter](https://mixkit.co/free-sound-effects/bird/).

Click.wav, pitch_down.wav, and pitch_up.wav were created with [Audacity](https://www.audacityteam.org/).