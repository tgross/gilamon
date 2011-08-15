import sys
import unittest
from time import strptime
from collections import namedtuple

from mock import Mock, MagicMock

from gilamon import wql_query


class TestWql(unittest.TestCase):

    def setUp(self):
        self.wql = wql_query.WqlQuery('namespace')
        mock_service = Mock()
        mock_service.ExecQuery.return_value = []
        mock_locator = Mock()
        mock_locator.ConnectServer.return_value = mock_service
        self.wql.wbem_locator = mock_locator

        self.wql.property_enums = {
            'someclass': { 'a': ( 0, [ 'Test0', 'Test1'])}
            }

    def test_make_query_empty(self):
        qr = self.wql.make_query()
        self.assertEqual(qr, [])

    def test_make_query_invalid_return(self):
        self.wql.wbem_locator.mock_service.ExecQuery.return_value = ['INVALID']
        qr = self.wql.make_query()
        self.assertEqual(qr, [])

    def test_make_query_com_error(self):
        self.wql.wbem_locator.mock_service.ExecQuery.side_effect = Exception(
            'BOOM')
        self.assertRaises(Exception, self.wql.make_query())

    def test_unpack_and_get_friendly(self):

        mock_results = [ self._make_mock_result() ]

        unpacked = self.wql._unpack_query_results(mock_results)[0]
        self.assertEqual(unpacked.a, 'Test0')

    def test_unpack_and_no_friendly(self):
        mock_results = [ self._make_mock_result() ]
        unpacked = self.wql._unpack_query_results(mock_results)[0]
        self.assertEqual(unpacked.a, 'Test0')

    def test_unpack_and_get_exception(self):
        mock_results = [ self._make_mock_result() ]
        mock_results[0].side_effect = Exception('ERROR')
        self.assertRaises(Exception,
                          self.wql._unpack_query_results(mock_results))

    def test_get_friendly_value_from_enum(self):
        friendly = self.wql._get_friendly_value('someclass', 'a', 1)
        self.assertEqual(friendly, 'Test1')

    def test_get_friendly_value_not_from_enum(self):
        friendly = self.wql._get_friendly_value('someclass', 'b', 1)
        self.assertEqual(friendly, 1)

    def test_get_friendly_value_bad_index(self):
        friendly = self.wql._get_friendly_value('someclass', 'a', 6)
        self.assertEqual(friendly, 6)

    def test_get_friendly_value_time(self):
        friendly = self.wql._get_friendly_value(
            'someclass', 'time', '20110909010101.12341244')
        self.assertEqual(friendly.tm_hour, 1)

    def test_get_friendly_value_invalid_time(self):
        self.assertRaises(ValueError,
                          self.wql._get_friendly_value,
                          'someclass','time','2011'
                          )

    def test_get_friendly_value_unfinished_time(self):
        friendly = self.wql._get_friendly_value(
            'someclass', 'time', '99990909010101.12341244')
        self.assertEqual(friendly.tm_year, 1601)

    def _make_mock_result(self):
        props = namedtuple('Property_', ['Name','Value'])
        mock_result = MagicMock()
        mock_result.Path_.Class = 'someclass'
        mock_result.Properties_ = [
            props(Name='a',Value='Test0'),
            props(Name='b',Value='Test1')
            ]
        return mock_result

if __name__ == '__main__':
    unittest.main()

