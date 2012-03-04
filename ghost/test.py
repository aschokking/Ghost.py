# -*- coding: utf-8 -*-
import threading
import logging
from unittest import TestCase
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from ghost import Ghost, Logger


class ServerThread(threading.Thread):
    """Starts a Tornado HTTPServer from given WSGI application.

    :param app: The WSGI application to run.
    :param port: The port to run on.
    """
    def __init__(self, app, port=5000):
        self.app = app
        self.port = port
        super(ServerThread, self).__init__()

    def run(self):
        self.http_server = HTTPServer(WSGIContainer(self.app))
        self.http_server.listen(self.port)
        self.io = IOLoop.instance()
        self.io.start()

    def join(self, timeout=None):
        if hasattr(self, 'http_server'):
            self.http_server.stop()
            del self.http_server


class BaseGhostTestCase(TestCase):
    display = False
    wait_timeout = 2
    viewport_size = (800, 600)
    log_level = logging.INFO

    def __new__(cls, *args, **kwargs):
        """Creates Ghost instance."""
        if not hasattr(cls, 'ghost'):
            cls.ghost = Ghost(display=cls.display,
                wait_timeout=cls.wait_timeout,
                viewport_size=cls.viewport_size,
                log_level=cls.log_level)
        return super(BaseGhostTestCase, cls).__new__(cls, *args, **kwargs)

    def __call__(self, result=None):
        """Does the required setup, doing it here
        means you don't have to call super.setUp
        in subclasses.
        """
        self._pre_setup()
        super(BaseGhostTestCase, self).__call__(result)
        self._post_teardown()

    def _post_teardown(self):
        """Deletes ghost cookies and hide UI if needed."""
        self.ghost.delete_cookies()
        if self.display:
            self.ghost.hide()

    def _pre_setup(self):
        """Shows UI if needed.
        """
        if self.display:
            self.ghost.show()


class GhostTestCase(BaseGhostTestCase):
    """TestCase that provides a ghost instance and manage
    an HTTPServer running a WSGI application.
    """
    port = 5000

    def create_app(self):
        """Returns your WSGI application for testing.
        """
        raise NotImplementedError

    @classmethod
    def tearDownClass(cls):
        """Stops HTTPServer instance."""
        cls.server_thread.join()
        super(GhostTestCase, cls).tearDownClass()

    @classmethod
    def setUpClass(cls):
        """Starts HTTPServer instance from WSGI application.
        """
        cls.server_thread = ServerThread(cls.create_app(), cls.port)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        super(GhostTestCase, cls).setUpClass()
