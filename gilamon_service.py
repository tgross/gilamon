import sys
import os.path

import win32serviceutil
import win32service
import servicemanager
import cherrypy

import gila_mon

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
        if hasattr(sys, 'frozen'):
            # We're running from a py2exe executable file
            current_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))

        # You should include a log.error_file value in the config file
        configFile = os.path.join(current_dir, 'gilamon.conf')
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

        app = cherrypy.tree.mount(GilaMonRoot(), '/', configFile)
        app.merge(appConfig)

        cherrypy.engine.subscribe('start_thread', InitializeCOM)
        cherrypy.engine.subscribe('stop_thread', UninitializeCOM)
        
        cherrypy.engine.start()
        cherrypy.engine.block()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        cherrypy.engine.exit()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED) 

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(GilaMonService)



