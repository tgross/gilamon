import unittest

import cherrypy
from mock import Mock

from gilamon.web_server import GilaMonRoot

class TestWebServer(unittest.TestCase):

    def setUp(self):
        cherrypy.session = {}
        self.webroot = GilaMonRoot()
        self.webroot.dfsr = Mock()
        self.webroot.server = 'DEFAULT'
        self.webroot.valid_servers = ['DEFAULT',
                                      'VALID_INPUT',
                                      'GOOD_COOKIE']

    def tearDown(self):
        cherrypy.session = {}
        server = None
        self.webroot.server = 'DEFAULT'

    def test_change_server_none(self):
        server = self.webroot.change_server()
        self.assertEqual(server, 'DEFAULT')

    def test_change_server_bad(self):
        server = self.webroot.change_server('INVALID_INPUT')
        self.assertEqual(server, 'DEFAULT')

    def test_change_server_good(self):
        server = self.webroot.change_server('VALID_INPUT')
        self.assertEqual(server, 'VALID_INPUT')

    def test_check_session_server_no_input_bad_cookie(self):
        cherrypy.session['server'] = 'BAD_COOKIE'
        server = self.webroot.check_session_server()
        self.assertEqual(server, 'DEFAULT')
        self.assertEqual(server, cherrypy.session.get('server'))

    def test_check_session_server_no_input_no_cookie(self):
        server = self.webroot.check_session_server()
        self.assertEqual(server, 'DEFAULT')
        self.assertEqual(server, cherrypy.session.get('server'))

    def test_check_session_server_no_input_good_cookie(self):
        cherrypy.session['server'] = 'GOOD_COOKIE'
        server = self.webroot.check_session_server()
        self.assertEqual(server, 'GOOD_COOKIE')
        self.assertEqual(server, cherrypy.session.get('server'))

    def test_check_session_server_bad_input_bad_cookie(self):
        cherrypy.session['server'] = 'BAD_COOKIE'
        server = self.webroot.check_session_server('INVALID_INPUT')
        self.assertEqual(server, 'DEFAULT')
        self.assertEqual(server, cherrypy.session.get('server'))

    def test_check_session_server_good_input_good_cookie(self):
        cherrypy.session['server'] = 'GOOD_COOKIE'
        server = self.webroot.check_session_server('INVALID_INPUT')
        self.assertEqual(server, 'GOOD_COOKIE')
        self.assertEqual(server, cherrypy.session.get('server'))

    def test_check_session_server_good_input_bad_cookie(self):
        cherrypy.session['server'] = 'BAD_COOKIE'
        server = self.webroot.check_session_server('VALID_INPUT')
        self.assertEqual(server, 'VALID_INPUT')
        self.assertEqual(server, cherrypy.session.get('server'))


if __name__ == '__main__':
    unittest.main()
