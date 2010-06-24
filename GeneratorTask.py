""" Run a detached process based on a Generator

Taken from  http://unpythonic.blogspot.com/2007/08/using-threads-in-pygtk.html
and slightly modified
"""

import threading, thread
import gobject, gtk
import time

class GeneratorTask(object):

    def __init__(self, generator, loop_callback=None, complete_callback=None):
        self.generator = generator
        self.loop_callback = loop_callback
        self.complete_callback = complete_callback

    def _start(self, *args, **kwargs):
        self._stopped = False

        if(callable(self.generator)):
            # we use a generator
            for ret in self.generator(*args, **kwargs):
                if self._stopped:
                    thread.exit()
                if self.loop_callback is not None:
                    gobject.idle_add(self._loop, ret)
        else:
            # seems to be an iterator
            for ret in self.generator:
                if self._stopped:
                    thread.exit()
                gobject.idle_add(self._loop, ret)


        if self.complete_callback is not None:
            gobject.idle_add(self.complete_callback)

    def _loop(self, ret):
        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)
            self.loop_callback(*ret)

    def start(self, *args, **kwargs):
        self._runner = threading.Thread(target=self._start, args=args, kwargs=kwargs)
        self._runner.start()

    def stop(self):
        self._stopped = True

    def wait(self):
        while(self._runner.is_alive()):
            time.sleep(0.1)

