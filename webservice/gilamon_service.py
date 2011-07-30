import sys
import os.path

import win32serviceutil
import win32service
import servicemanager
from pythoncom import CoInitialize, CoUninitialize
import cherrypy

import gilamon.gilamon.dfsr_query
import gilamon.webserver


class GilaMonService (win32serviceutil.ServiceFramework):
    '''
    Borrowed from:
    http://tools.cherrypy.org/wiki/WindowsService?format=txt
    Once this is done, install with: python gilamon_service.py install
    Start the service with: python gilamon_service.py start
    You can uninstall with remove with: python gilamon_service.py remove
    '''
    _svc_name_ = "GilaMon"
    _svc_display_name_ = "GilaMon"
    _svc_description_ = "DFSR Monitoring Service"

    def SvcDoRun(self):
        current_dir = gila_mon.get_working_dir()

        # You should include a log.error_file value in the config file
        configFile = os.path.join(current_dir, 'config', 'gilamon.conf')
        static_dir = os.path.join(current_dir, 'static')
        appConfig = {
            'global':{
                'log.screen': False,
                'engine.autoreload.on': False,
                'engine.SIGHUP': None,
                'engine.SIGTERM': None
                },
            '/': {
                'tools.sessions.on': True,
                },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': static_dir,
                }
            }

        cherrypy.config.update(configFile)
        cherrypy.config.update(appConfig)

        app = cherrypy.tree.mount(webserver.GilaMonRoot(), '/', configFile)
        app.merge(appConfig)

        cherrypy.engine.subscribe('start_thread', InitializeCOM)
        cherrypy.engine.subscribe('stop_thread', UninitializeCOM)
        
        cherrypy.engine.start()
        cherrypy.engine.block()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        cherrypy.engine.exit()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED) 


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
    win32serviceutil.HandleCommandLine(GilaMonService)

