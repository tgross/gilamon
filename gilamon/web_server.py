''' web_server.py '''

import sys
import os.path
from time import strftime
import logging

import cherrypy
from cherrypy import tools
from jinja2 import Environment, FileSystemLoader
from pythoncom import CoInitialize, CoUninitialize

import dfsr_query
from wmi_client import ArgumentError, WmiError


def get_working_dir():
    '''
    Determines whether we're running from the py2exe executable
    and sets the current working directory accordingly.
    '''
    if hasattr(sys, 'frozen'):  #we're in a py2exe environment
        current = os.path.dirname(sys.executable)
    else:
        current = os.path.dirname(os.path.abspath(__file__))
    return current

env = Environment(loader=FileSystemLoader(
    os.path.join(get_working_dir(), 'templates')))


class GilaMonRoot:
    '''
    This is the root of the CherryPy server.
    '''

    @cherrypy.expose
    def index(self):
        '''
        This view gets served at the root URL or at root/index.html
        If the initial WMI setup just isn't working, then this method will
        respond with an error page, otherwise it'll respond with the main
        content page and the rest of the methods will report any errors
        they encounter.
        '''
        try:
            self.server = server = cherrypy.session.get('server')
            servers = cherrypy.request.app.config['dfsr']['servers']
            site_title = cherrypy.request.app.config['dfsr']['title']
            if not server:
                self.server = servers[0]

            self.dfsr = dfsr_query.DfsrQuery(self.server)
            context = {
                'server_name': self.server,
                'servers_avail': servers,
                'site_title': site_title}

            # UI options
            if cherrypy.request.app.config['dfsr']['show_all_replications']:
                template = env.get_template('index_all.html')
            else:
                template = env.get_template('index.html')

        except ArgumentError, e:
            template = env.get_template('error.html')
            context = { 'error_msg': e.msg }
        except Exception, e:
            template = env.get_template('error.html')
            context = { 'error_msg': str(e) }
        return template.render(context)

    @cherrypy.expose
    @tools.json_out()
    def change_server(self, server=None):
        '''
        Handles Ajax call to switch the default DFSR server for future
        requests.
        '''
        if server:
            self.server = server
            self.dfsr.server = server
            cherrypy.session['server'] = server
            return server

    @cherrypy.expose
    @tools.json_out()
    def get_server_status(self, server=None):
        ''' Handles Ajax call to get the current DFSR server status '''
        server = self.check_session_server(server)
        try:
            return self.dfsr.get_dfsr_state(server)
        except WmiError as e:
            return self.report_and_log_error_fragment(e.msg)

    @cherrypy.expose
    @tools.json_out()
    def get_rg_states(self, server=None):
        '''
        Handles Ajax call to get the list of replication groups
        and their current states.  Returns a JSON context ordered by
        green/yellow/red state, counts, and then replication group name.
        '''
        server = self.check_session_server(server)

        try:
            group_states = self.dfsr.get_replication_status_counts(server)
            context = { 
                'green': {'count': str(len(group_states['Normal'])),
                          'items': group_states['Normal']},
                'yellow': {'count': str(
                        len(group_states['Auto Recovery']) +
                        len(group_states['Initialized']) +
                        len(group_states['Initial Sync'])),
                           'items': group_states['Auto Recovery'] +
                           group_states['Initialized'] +
                           group_states['Initial Sync']},
                'red': {'count': str(
                        len(group_states['In Error']) +
                        len(group_states['Uninitialized'])),
                        'items': group_states['In Error'] + 
                        group_states['Uninitialized']}}
            return context
        except WmiError as e:
            return self.report_and_log_error_fragment(e.msg)

    @cherrypy.expose
    @tools.json_out()
    def get_connector_states(self, server=None):
        '''
        Handles Ajax call to get the list of connectors and their current
        states.  Returns a JSON context ordered by green/yellow/red state,
        counts, and then connector name.
        '''
        server = self.check_session_server(server)
        try:
            cn_states = self.dfsr.get_connector_status_counts(server)

            context = {
                'green': {'count': str(len(cn_states['Online'])),
                          'items': [self.get_connector_name(*c)
                                   for c in cn_states['Online']]},
                'yellow': {'count': str(len(cn_states['Connecting'])),
                           'items': [self.get_connector_name(*c)
                                   for c in cn_states['Connecting']]},
                'red': {'count': str(
                                  len(cn_states['Offline']) +
                                  len(cn_states['In Error'])),
                        'items': [self.get_connector_name(*c)
                                   for c in (cn_states['Offline'] +
                                             cn_states['In Error'])]}}
            return context
        except WmiError as e:
            return self.report_and_log_error_fragment(e.msg)


    @cherrypy.expose
    @tools.json_out()
    def get_replication_group_list(self, server=None):
        ''' Handles Ajax call to URL root/get_replication_group_list
        and responds with a list of replication name/GUID pairs.
        '''
        server = self.check_session_server(server)
        try:
            replication_groups = sorted(
                self.dfsr.get_all_replication_groups(server),
                key=lambda x: str(x.ReplicationGroupName))

            context = [{ 'id': rg.ReplicationGroupGuid,
                         'value': rg.ReplicationGroupName }
                       for rg in replication_groups]
            return context
        except WmiError as e:
            return self.report_and_log_error_fragment(e.msg)

    @cherrypy.expose
    def show_replication(self, guid, server=None):
        '''
        Handles request for the details associated with a replication.
        Returns an HTML fragment listing replicated folders in the group
        (and their current status), and a list of connectors with
        details for those connectors available as an Ajax mouseover tooltip.
        '''
        server = self.check_session_server(server)
        try:
            results = self.dfsr.get_replication_folder_details(guid, server)
            rfolders = [{
                'name': r.ReplicatedFolderName,
                'folder_state': r.State,
                'current_size_staging': r.CurrentStageSizeInMb,
                'current_size_conflicts': r.CurrentConflictSizeInMb}
                for r in results]

            state_map = { 'Online': 'green',
                          'Trouble': 'yellow',
                          'Down': 'red',
                          'Uninitialized': 'red'}
            connection_info = self.dfsr.get_connectors(guid, server)
            connectors = [{
                'Guid': c.ConnectionGuid,
                'Title': self.get_connector_direction(
                c.MemberName, c.PartnerName, c.Inbound),
                'State': state_map[c.State]}
                for c in connection_info]

            context = {
                'rfolders': rfolders,
                'connectors': connectors}
            template = env.get_template('rg_details.html')
            return template.render(context)
        except WmiError as e:
            return self.report_and_log_error_fragment(e.msg)

    @cherrypy.expose
    @tools.json_in()
    @tools.json_out()
    def show_sync(self, guid, server=None):
        '''
        Handles Ajax request for the details of a sync associated with
        a particular connector.  Returns a JSON context of K-V pairs for
        each of the details, including a list of actively replicating files.
        '''
        server = self.check_session_server(server)
        try:
            sync = self.dfsr.get_sync_details(guid)[0]
            active_files = self.dfsr.get_update_details(sync.ConnectionGuid)

            if len(active_files) > 0:
                updates = [(f.FullPathName + " [" + f.UpdateState + "]: " +
                            self.get_connector_direction(
                            self.server, f.PartnerName, f.Inbound))
                            for f in active_files]
            else:
                updates = []

            context = {
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
                'ForceReplicationBandwidthlevel':
                    sync.ForceReplicationBandwidthlevel,
                'ActiveUpdates': updates}
            return context
        except WmiError as e:
            return e.msg


    def format_time(self, time_obj):
        ''' formats a time object '''
        time_format = '%Y-%m-%d %H:%M:%S'
        if time_obj.tm_year == 1601:
            return 'n/a'
        else:
            return strftime(time_format, time_obj)

    def get_connector_name(self, rep_group, member, partner, is_inbound):
        ''' pretty-printing of connector name '''
        return rep_group + ': ' + self.get_connector_direction(
            member, partner, is_inbound)

    def get_connector_direction(self, member, partner, is_inbound):
        '''pretty-printing of connector with an arrow character'''
        if is_inbound:
            return member + " &#x2190 " + partner
        else:
            return member + " &#x2192 " + partner

    def check_session_server(self, server=None):
        ''' get DFSR server we want out of the session cookie. '''
        if not server:
            if 'server' in cherrypy.session:
                server = cherrypy.session.get('server')
                if not server:
                    server = self.server
        else:
            cherrypy.session['server'] = server
        return server

    def report_and_log_error_fragment(self, msg):
        cherrypy.log(msg, 
                         context='', severity=logging.DEBUG, traceback=False)
        return '<div class="error-msg">%s</div>' % msg


'''
The cherrypy web server is multithreaded.  In order to use COM objects
returned by win32com.client.GetObject in that environment, we need to
set up COM access to the threads.
See also http://www.cherrypy.org/wiki/UsingCOMObjects
'''


def initialize_com(thread_index):
    CoInitialize()


def uninitialize_com(thread_index):
    CoUninitialize()


if __name__ == '__main__':

    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, 'static')
    app_config = {
    '/': {
        'tools.sessions.on': True,
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': static_dir,
        }
    }
    config_file = os.path.join(current_dir, 'config', 'gilamon.conf')

    cherrypy.config.update(config_file)
    cherrypy.config.update(app_config)

    app = cherrypy.tree.mount(GilaMonRoot(), '/', config_file)
    app.merge(app_config)

    cherrypy.engine.subscribe('start_thread', initialize_com)
    cherrypy.engine.subscribe('stop_thread', uninitialize_com)

    cherrypy.engine.start()
