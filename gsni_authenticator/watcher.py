import pyinotify


class MyEventHandler(pyinotify.ProcessEvent):
    def my_init(self, callback=None):
        self.callback = callback

    def process_default(self, event):
        if event.name == "ConfigAGN.connect.sh.txt" and self.callback:
            self.callback()


class AGNClientConnectWatcher():
    """Auto reloader employ inotify(7)
"""

    def __init__(self, callback=None):
        self.callback = callback

    def start(self):
        wm = pyinotify.WatchManager()
        eh = MyEventHandler(callback=self.callback)

        notifier = pyinotify.ThreadedNotifier(wm, eh)
        notifier.daemon = True
        notifier.start()
        wm.add_watch("/tmp", pyinotify.IN_CLOSE_WRITE)
        