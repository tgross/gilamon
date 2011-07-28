from collections import Counter, defaultdict
import uuid

import wql_query
from wql_query import Wql_Query

from dfsr_settings import *


def safe_guid(function):
    def _function(*args, **kwargs):
        try:
            u = uuid.UUID(args[1])
            return function(*args, **kwargs)
        except:
            raise
    return _function


class Dfsr_Query():
    '''
    Sets up the WMI connection through Wql_Query and then handles parameterized
    WQL queries through that connection.
    '''

    def __init__(self, server):
	self.server = server
        self.wql = Wql_Query(
            name_space = DFSR_NAME_SPACE,
            property_enums = DFSR_PROPERTY_ENUMS
            )

    def get_Dfsr_state(self, server_name = None):
        if server_name:
            self.server = server_name

        wql_query = 'SELECT State FROM DfsrInfo'
        query_results = self.wql.make_query(self.server, wql_query)

        if len(query_results) > 0:
            return query_results[0].State
        else:
            return 'Service offline' #Note: Dfsr won't return state when offline.

    def get_replication_status_counts(self, server_name = None):
        '''
        Returns a dict with replication states as keys for lists of
	ReplicationGroupNames with that status.  I'm not using a Counter
	object here to allow the caller to easily get the list of replication
	groups with that status, not just the count.
        '''
        if server_name:
            self.server = server_name

        wql_query = ('SELECT State, ReplicationGroupName FROM ' +
                    'DfsrReplicatedFolderInfo')
        q = self.wql.make_query(self.server, wql_query)

        states = set([x.State for x in q])
        counts = defaultdict(list)
        for s in states:
            counts[s] = sorted(
                [rep.ReplicationGroupName for rep in q if (rep.State == s)]
                )
        return counts


    def get_connector_status_counts(self, server_name = None):
        wql_query = ('SELECT State, MemberName, PartnerName, ' +
                    'Inbound, ReplicationGroupName FROM DfsrConnectionInfo')
        if server_name:
            self.server = server_name

        q = self.wql.make_query(self.server, wql_query)

        if len(q) > 0:
            states = set([x.State for x in q])
            counts = defaultdict(list)
            for s in states:
                counts[s] = sorted([
                    [conn.ReplicationGroupName, conn.MemberName,
                     conn.PartnerName, conn.Inbound]
                    for conn in q if (conn.State == s)])
            return counts
        else:
            return []

    def get_all_replication_groups(self, server_name = None):
        '''
        Returns ReplicationGroupName, ReplicationGroupGuid, and DefaultSchedule
        of all replication groups in named tuples.
        '''
        if server_name:
            self.server = server_name
        wql_query = ('SELECT ReplicationGroupName, ReplicationGroupGuid ' +
                    'FROM DfsrReplicationGroupConfig')
        q = self.wql.make_query(self.server, wql_query)
        if len(q) > 0:
            return q
        else:
            return []

    @safe_guid
    def get_replication_folder_details(self, guid, server_name=None):
        if server_name:
            self.server = server_name

        wql_query = ('SELECT * FROM DfsrReplicatedFolderInfo WHERE ' +
                    'ReplicationGroupGuid = "%s"') % guid
        folders = self.wql.make_query(self.server, wql_query)
        if len(folders) > 0:
            return folders
        else:
            return []

    @safe_guid
    def get_connectors(self, guid, server_name=None):
        if server_name:
            self.server = server_name
        wql_query = ('SELECT * FROM DfsrConnectionInfo WHERE ' +
                    'ReplicationGroupGuid = "%s"') % guid
        return self.wql.make_query(self.server, wql_query)

    @safe_guid
    def get_sync_details(self, guid, server_name=None):
        if server_name:
            self.server = server_name
        wql_query = ('SELECT * FROM DfsrSyncInfo WHERE ' +
                    'ConnectionGuid = "%s"') % guid
        return self.wql.make_query(self.server, wql_query)

    @safe_guid
    def get_update_details(self, guid, server_name=None):
        if server_name:
            self.server = server_name
        wql_query = ('SELECT * FROM DfsrIdUpdateInfo WHERE ' +
                    'ConnectionGuid = "%s"') % guid
        return self.wql.make_query(self.server, wql_query)


