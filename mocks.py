from collections import namedtuple

class client(object):

    def __init__(self, *args, **kwargs): pass

    def __len__(self): return 0

    def getattr(self, name):
        return client()

    def __call__(self, *args, **kwargs):
        return client()

'''
class client(object):

    gencache = { 'is_readonly': False }

    

    def __init__(self):
        print 'client!'

    def Dispatch(self, dispatcher):
        return WbemLocatorMock()
'''

class WbemLocatorMock():

    def ConnectServer(self, server, name_space, user, password):
        return WbemServiceMock()

class WbemServiceMock():

    def ExecQuery(self, wql_query):
        '''
        Tests should monkeypatch return of this method to get
        the QueryResultsMock or QueryErrorMock they want to test.
        '''
        pass

class QueryResultsMock():

    Properties_ = []

    def __init__(self, props, path='', klass=''):
        kv_pair = namedtuple('kv_pair', ['Name', 'Value'])
        self.Properties_.extend(
            [kv_pair(Name=k, Value=v) for (k,v) in props.iteritems()])
        self.Path_ = QueryResultsPath(klass)


class QueryResultsPath():

    def __init__(self, klass):
        self.Class = klass

class QueryErrorMock():

    def __init__(self, result='', info=None):
        self.hresult = result
        self.excepinfo = info
