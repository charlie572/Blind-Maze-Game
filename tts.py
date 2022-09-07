import queue
import pyttsx3
import threading


class TTSThread(threading.Thread):
    """A thread for text-to-speech"""
    def __init__(self, engine=None):
        super().__init__()

        self.engine = engine
        if engine is None:
            self.engine = pyttsx3.init()

        self._in_queue = queue.Queue()
        self._terminate_event = threading.Event()

    def terminate(self):
        self._terminate_event.set()

    def say(self, text):
        self._in_queue.put(text)

    def run(self):
        while not self._terminate_event.is_set():
            try:
                text = self._in_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            self.engine.say(text)
            self.engine.runAndWait()


def main():
    import pyglet

    window = pyglet.window.Window(960, 720, 'TTS')

    tts_thread = TTSThread()
    tts_thread.setDaemon(True)
    tts_thread.start()

    @window.event
    def on_key_press(symbol, modifiers):
        tts_thread.say('hello')

    pyglet.app.run()


if __name__ == '__main__':
    main()
