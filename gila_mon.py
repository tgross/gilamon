import sys
import os.path
from time import strftime

import cherrypy
from cherrypy import tools
from jinja2 import Environment, FileSystemLoader
from pythoncom import CoInitialize, CoUninitialize
import json

from dfsr_query import *

def get_working_dir():
    if hasattr(sys, 'frozen'):
        # We're running from a py2exe executable file
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    return current_dir

env = Environment(loader=FileSystemLoader(os.path.join(get_working_dir(), 'templates')))

class GilaMonRoot:

    server = DEFAULT_SERVER

    @cherrypy.expose
    def index(self):
        self.dfsr = Dfsr_Query()
        self.server = server = cherrypy.session.get('server')
        if not server:
            self.server = DEFAULT_SERVER

        context = {
            'server_name': self.server,
            'servers_avail': SERVERS,
            }
        t = env.get_template('index.html')
        return t.render(context)

    @cherrypy.expose
    @tools.json_out()
    def change_server(self, server=None):
        if server:
            self.server = server
            self.dfsr.server = server
            cherrypy.session['server'] = server
            return server

    @cherrypy.expose
    @tools.json_out()
    def get_server_status(self, server=None):
        server = self.check_session_server(server)
        current_state = self.dfsr.get_Dfsr_state(server)
        return current_state

    @cherrypy.expose
    def get_rg_states(self, server=None):
        server = self.check_session_server(server)

        group_states = self.dfsr.get_replication_status_counts(server)
        context = {
            'RGs_count_G': str(len(group_states['Normal'])),
            'RGs_green':   group_states['Normal'],
            'RGs_count_Y': str (
                               len(group_states['Auto Recovery']) +
                               len(group_states['Initialized']) +
                               len(group_states['Initial Sync'])
                           ),
            'RGs_yellow':  group_states['Auto Recovery'] +
                           group_states['Initialized'] +
                           group_states['Initial Sync'],
            'RGs_count_R': str (
                               len(group_states['In Error']) +
                               len(group_states['Uninitialized'])
                           ),
            'RGs_red':     group_states['In Error'] +
                           group_states['Uninitialized'],
          }
        t = env.get_template('rg_states.html')
        return t.render(context)

    @cherrypy.expose
    def get_connector_states(self, server=None):
        server = self.check_session_server(server)
        cn_states = self.dfsr.get_connector_status_counts(server)

        context = {
            'conn_count_G': str(len(cn_states['Online'])),
            'conn_green':   [self.get_connector_name(*c)
                               for c in cn_states['Online']
                            ],
            'conn_count_Y': str(len(cn_states['Connecting'])),
            'conn_yellow':  [self.get_connector_name(*c)
                               for c in cn_states['Connecting']
                            ],
            'conn_count_R': str(
                              len(cn_states['Offline']) +
                              len(cn_states['In Error'])
                            ),
            'conn_red':     [self.get_connector_name(*c)
                               for c in (cn_states['Offline'] + cn_states['In Error'])
                            ],
          }
        t = env.get_template('connector_states.html')
        return t.render(context)


    @cherrypy.expose
    def get_replication_group_list(self, server=None):
        server = self.check_session_server(server)
        replication_groups = sorted(self.dfsr.get_all_replication_groups(server),
                                    key=lambda x: str(x.ReplicationGroupName))

        context = { 'replication_groups': replication_groups }
        t = env.get_template('rg_list.html')
        return t.render(context)
        

    @cherrypy.expose
    def show_replication(self, guid, server=None):
        server = self.check_session_server(server)
        rf = self.dfsr.get_replication_folder_details(guid, server)
        rfolders = [
            {
            'name': r.ReplicatedFolderName,
            'folder_state': r.State,
            'current_size_staging': r.CurrentStageSizeInMb,
            'current_size_conflicts': r.CurrentConflictSizeInMb,
            }
            for r in rf]
        
        connection_info = self.dfsr.get_connectors(guid, server)
        connectors = [
            {'Guid': x.ConnectionGuid,
             'Title': self.get_connector_direction(x.MemberName, x.PartnerName, x.Inbound),
             'State': x.State,
            }
            for x in connection_info]

        context = {
            'rfolders': rfolders,
            'connectors': connectors,
            }
        t = env.get_template('rg_details.html')
        return t.render(context)


    @cherrypy.expose
    @tools.json_in()
    @tools.json_out()
    def show_sync(self, guid, server=None):
        server = self.check_session_server(server)
        
        sync = self.dfsr.get_sync_details(guid)[0]
        active_files = self.dfsr.get_update_details(sync.ConnectionGuid)

        if len(active_files) > 0:
            updates = [ (f.FullPathName + " [" + f.UpdateState + "]: " +
                         self.get_connector_direction(self.server, f.PartnerName, f.Inbound) )
                        for f in active_files ]
        else:
            updates = []

        context = {
            'ConnectionGuid': sync.ConnectionGuid,
            'Title': self.get_connector_direction(sync.MemberName, sync.PartnerName, sync.Inbound),
            'MemberGuid': sync.MemberGuid,
            'PartnerGuid': sync.PartnerGuid,
            'ReplicationGroupGuid': sync.ReplicationGroupGuid,
            'ReplicationGroupName': sync.ReplicationGroupName,
            'State': sync.State,
            'InitiationReason': sync.InitiationReason,
            'StartTime': self.format_time(sync.StartTime),
            'EndTime': self.format_time(sync.EndTime),
            'UpdatesTransferred': sync.UpdatesTransferred,
            'BytesTransferred': sync.BytesTransferred,
            'UpdatesNotTransferred': sync.UpdatesNotTransferred,
            'UpdatesToBeTransferred': sync.UpdatesToBeTransferred,
            'ConflictsGenerated': sync.ConflictsGenerated,
            'TombstonesGenerated': sync.TombstonesGenerated,
            'LastErrorCode': sync.LastErrorCode,
            'LastErrorMessageId': sync.LastErrorMessageId,
            'ForceReplicationEndTime': self.format_time(sync.ForceReplicationEndTime),
            'ForceReplicationBandwidthlevel': sync.ForceReplicationBandwidthlevel,
            'ActiveUpdates': updates,
        }
        return context

    @cherrypy.expose
    def test_output(self):
        t = '<div>TEST_OUTPUT!</div>'
        return t.render()

    @cherrypy.expose
    @tools.json_out()
    def test_json_output(self):
        return 'TEST_JSON_OUTPUT'

    def format_time(self, time_obj):
        time_format = '%Y-%m-%d %H:%M:%S'
        if time_obj.tm_year == 1601:
            return 'n/a'
        else:
            return strftime(time_format, time_obj)

    def get_connector_name(self, rep_group, member, partner, is_inbound):
        return rep_group + ': ' + self.get_connector_direction(member, partner, is_inbound)

    def get_connector_direction(self, member, partner, is_inbound):
        '''pretty-printing preprocessing with an arrow character'''
        if is_inbound:
            return member + " &#x2190 " + partner
        else:
            return member + " &#x2192 " + partner

    def check_session_server(self, server=None):
        if not server:
            if 'server' in cherrypy.session:
                server = cherrypy.session.get('server')
                if not server:
                    server = self.server
        else:
            cherrypy.session['server'] = server
        return server


'''
The cherrypy web server is multithreaded.  In order to use COM objects returned
by win32com.client.GetObject in that environment, we need to set up COM access to
the threads.
See also http://www.cherrypy.org/wiki/UsingCOMObjects
'''

def InitializeCOM(threadIndex):
    CoInitialize()

def UninitializeCOM(threadIndex):
    CoUninitialize()

if __name__ == '__main__':

    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, 'static')
    config = {
        '/': {
            'tools.sessions.on': True,
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': static_dir,
            }
        }

    cherrypy.engine.subscribe('start_thread',InitializeCOM)
    cherrypy.engine.subscribe('stop_thread', UninitializeCOM)
    
    cherrypy.quickstart(GilaMonRoot(), '/', config=config)
