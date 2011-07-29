import unittest
from collections import namedtuple

from mock import Mock, MagicMock

import gilamon.dfsr_query
from gilamon.dfsr_query import DfsrQuery, safe_guid

class TestDfsr(unittest.TestCase):

    def setUp(self):
        self.dfsr = DfsrQuery('servername')
        self.dfsr.wql = Mock()
        self.query_result = self.dfsr.wql.make_query

    def tearDown(self):
        pass

    def test_get_dfsr_state(self):
        mock_state = Mock()
        mock_state.State = 'STATE'
        self.query_result.return_value = [ mock_state ]
        state = self.dfsr.get_dfsr_state()
        self.assertEqual(state, 'STATE')

    def test_get_Dfsr_state_down(self):
        self.query_result.return_value = []
        state = self.dfsr.get_dfsr_state()
        self.assertEqual(state, 'Service offline')

    def test_get_replication_status_counts(self):
        result = self._make_results(['State','ReplicationGroupName'])
        self.query_result.return_value = [
            result('State1','Name1'),
            result('State1','Name2'),
            result('State2','Name3'),
            ]
        results = self.dfsr.get_replication_status_counts()
        self.assertEqual(results['State1'], ['Name1','Name2'])
        self.assertEqual(results['State2'], ['Name3'])

    def test_get_replication_status_counts_invalid(self):
        self.dfsr.wql.make_query.return_value = []
        results = self.dfsr.get_replication_status_counts()
        self.assertEqual(len(results), 0)

    def _make_results(self, properties):
        query_result = namedtuple('query_result', properties)
        return query_result
