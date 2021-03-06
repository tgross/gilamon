''' dfsr_query.py '''

from collections import defaultdict
import uuid

from wmi_client import WmiClient, ArgumentError
import dfsr_settings


def safe_guid(function):
    ''' A decorator to validate guids. '''
    def _function(*args, **kwargs):
        ''' The internal function for the decorator '''
        try:
            uuid.UUID(args[1])
            return function(*args, **kwargs)
        except:
            raise ArgumentError('Invalid GUID', str(args[1]))
    return _function


class DfsrQuery():
    '''
    Sets up the WMI connection through WmiClient and then handles
    parameterized WQL queries through that connection.

    DfsrQuery currently allows exceptions raised by WmiClient to
    bubble up to the caller.  There isn't much we can do to recover
    from them, because they're going to be caused by problems with
    the server, network connectivity, or improper configuration.
    So we're going to want the caller to define how the errors get
    display to the user via the web service or CLI.
    '''

    def __init__(self, server):
        self.server = server
        self.wmi = WmiClient(
            name_space=dfsr_settings.DFSR_NAME_SPACE,
            property_enums=dfsr_settings.DFSR_PROPERTY_ENUMS)

    def get_dfsr_state(self, server_name=None):
        '''
        Returns the DfsrInfo.State property.
        '''
        if server_name:
            self.server = server_name

        wql = 'SELECT State FROM DfsrInfo'
        query_results = self.wmi.make_query(self.server, wql)

        if len(query_results) > 0:
            return query_results[0].State
        else:
            #Dfsr won't return an error when offline.
            return 'Service offline'

    def get_replication_status_counts(self, server_name=None):
        '''
        Returns a dict with replication states as keys for lists of
        ReplicationGroupNames with that status.  I'm not using a Counter
        object here to allow the caller to easily get the list of replication
        groups with that status, not just the count.
        '''
        if server_name:
            self.server = server_name

        wql = ('SELECT State, ReplicationGroupName FROM ' +
                    'DfsrReplicatedFolderInfo')
        results = self.wmi.make_query(self.server, wql)

        states = set([x.State for x in results])
        counts = defaultdict(list)
        for state in states:
            counts[state] = sorted(
                [rep.ReplicationGroupName for
                rep in results if (rep.State == state)])
        return counts

    def get_connector_status_counts(self, server_name=None):
        '''
        Returns a dict with connector status as keys for lists of
        Connectors with that status.
        '''
        wql = ('SELECT State, MemberName, PartnerName, ' +
                    'Inbound, ReplicationGroupName FROM DfsrConnectionInfo')
        if server_name:
            self.server = server_name

        results = self.wmi.make_query(self.server, wql)
        if len(results) > 0:
            states = set([x.State for x in results])
            counts = defaultdict(list)
            for state in states:
                counts[state] = sorted([
                    [conn.ReplicationGroupName, conn.MemberName,
                     conn.PartnerName, conn.Inbound]
                    for conn in results if (conn.State == state)])
            return counts
        else:
            return []

    def get_all_replication_groups(self, server_name=None):
        '''
        Returns ReplicationGroupName, ReplicationGroupGuid, and DefaultSchedule
        of all replication groups in named tuples.
        '''
        if server_name:
            self.server = server_name
        wql = ('SELECT ReplicationGroupName, ReplicationGroupGuid ' +
                    'FROM DfsrReplicationGroupConfig')
        results = self.wmi.make_query(self.server, wql)
        if len(results) > 0:
            return results
        else:
            return []

    @safe_guid
    def get_replication_folder_details(self, guid, server_name=None):
        '''
        Returns the full details about a DfsrReplicatedFolder.
        Requires the GUID for the Replication Folder.
        '''
        if server_name:
            self.server = server_name

        wql = ('SELECT * FROM DfsrReplicatedFolderInfo WHERE ' +
                    'ReplicationGroupGuid = "%s"') % guid
        folders = self.wmi.make_query(self.server, wql)
        if len(folders) > 0:
            return folders
        else:
            return []

    @safe_guid
    def get_connectors(self, guid, server_name=None):
        '''
        Returns a list of connectors for a DfsrReplicatedFolder with
        all details
        '''
        if server_name:
            self.server = server_name
        wql = ('SELECT * FROM DfsrConnectionInfo WHERE ' +
                    'ReplicationGroupGuid = "%s"') % guid
        return self.wmi.make_query(self.server, wql)

    @safe_guid
    def get_sync_details(self, guid, server_name=None):
        '''
        Returns the the full details about a connector's sync.
        Requires the GUID of the DFSR Connector.
        '''
        if server_name:
            self.server = server_name

        wql = ('SELECT ConnectionGuid, InitiationReason, StartTime, ' +
               'EndTime, UpdatesTransferred, BytesTransferred, ' +
               'UpdatesNotTransferred, UpdatesToBeTransferred, '+
               'ConflictsGenerated, TombstonesGenerated, ' +
               'ForceReplicationBandwidthLevel, LastErrorCode ' +
               'FROM DfsrSyncInfo WHERE ConnectionGuid = "{0}"').format(guid)

        return self.wmi.make_query(self.server, wql)

    @safe_guid
    def get_update_details(self, guid, server_name=None):
        '''
        Returns the the full details about a connector's update.
        Requires the GUID of the DFSR Connector.
        '''
        if server_name:
            self.server = server_name
        wql = ('SELECT * FROM DfsrIdUpdateInfo WHERE ' +
                    'ConnectionGuid = "%s"') % guid
        return self.wmi.make_query(self.server, wql)
