import sys
import unittest

import mock
from mock import *
mock = Mock()

patch.dict('sys.modules',
           {'win32com': mock,
            'client': mock,
            'Dispatcher': mock,
            'ConnectServer': mock,
            'ExecQuery': mock,
            'gencache': mock,
            'is_readonly': mock,
            }
           )

import win32com

import wql_query
from wql_query import *

class TestWql(unittest.TestCase):

    def setUp(self):
        print dir(win32com)
        self.namespace = 'testnamespace'
        self.wql_query = Wql_Query(self.namespace)

    def test_makequery(self):
        with patch.dict('sys.modules', {'win32com': mock }):
            import win32com
            qr = self.wql_query.make_query()
            self.assertEqual(qr, [])

    def test_unpack(self):
        self.wql_query.property_enums = {
            'someklass': { 'a': ( 0, [ 'Test0', 'Test1'])}
            }
        qrm = [Mock( { 'a': 0, 'b': 1 }, 'somepath', 'someklass')]
#        qrm = QueryResultsMock( { 'a': 0, 'b': 1 }, 'somepath', 'someklass')
        unpacked = self.wql_query._unpack_query_results(qrm)
        self.assertEqual(unpacked.a, 'Test0')

#c = win32com.client()
#print 'Success'

if __name__ == '__main__':
    unittest.main()
