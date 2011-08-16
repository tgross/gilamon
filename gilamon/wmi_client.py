''' wql_query.py '''

import sys
from time import strptime
from collections import namedtuple

import win32com
from win32com import client
from pywintypes import com_error


class WmiClient():
    '''
    This class will use the default security context if not passed
    credentials. If you intend to make WQL query requests as part of a
    service, make sure that the service has valid login credentials to the
    DFSR server or its domain.
    '''

    def __init__(self, name_space=None, user='', password='',
        property_enums=None):
        win32com.client.gencache.is_readonly = False
        win32com.client.gencache.GetGeneratePath()
        self.wbem_locator = client.Dispatch('wbemscripting.swbemlocator')

        if name_space:
            self.user = user
            self.password = password
            self.name_space = name_space
            self.property_enums = property_enums
        else:
            raise ArgumentError('WMI namespace not provided.')

    def make_query(self, server_name=None, wql_query=None):
        '''
        Note: this method raises an exception on invalid WQL query syntax and
        other WMI errors, but does not verify the safety of the operation!
        WQL doesn\'t accept parameterized queries, so the caller must not
        pass untrusted data in the query string.
        '''
        try:
            remote_service = self.wbem_locator.ConnectServer(
                server_name, self.name_space, self.user, self.password)
            remote_service.Security_.ImpersonationLevel = 3
            query_results = remote_service.ExecQuery(wql_query)
            if len(query_results) < 1:
                return []

            return self._unpack_query_results(query_results)
        except com_error, e:
            raise WmiError(e)

    def _unpack_query_results(self, raw_query_results):
        '''
        Takes a list of ISWbemObjectSet instances and enumerates their
        properties, replacing enums with any friendly values provided in the
        constructor.  Returns a list of "query_result" named tuples.
        '''
        try:
            com_class_name = raw_query_results[0].Path_.Class

            query_result = namedtuple(com_class_name,
                                      [x.Name for x in
                                       raw_query_results[0].Properties_])

            if self.property_enums and com_class_name in self.property_enums:
                #remember to *unpack list args to instantiate a namedtuple!
                return [query_result(
                            *[self._get_friendly_value(com_class_name,
                                                       p.Name, p.Value)
                            for p in result.Properties_])
                        for result in raw_query_results]
            else:
                return [query_result(
                    *[p.Value for p in result.Properties_]) for
                    result in raw_query_results]

        except AttributeError, e:
            raise WmiError(
                e, 'AttributeError: Introspection failed on COM object.')

    def _get_friendly_value(self, com_class_name, name, val):
        '''
        Replaces the unfriendly integer index value for the COM enums with the
        appropriate friendly string value in the property_enums dictionary, and
        converts UTC time stamps to struct_time objects for the caller to
        format. Note: WMI returns year 1601 or 9999 to indicate unfinished
        processes, but this will return only the standard 1601.
        '''
        if 'time' in name.lower():
            if val[:4] == '9999':
                val = '1601' + val[4:]
            return strptime(val[:20], '%Y%m%d%H%M%S.%f')
        else:
            try:
                valid_values = self.property_enums[com_class_name][name][1]
                idx = val - self.property_enums[com_class_name][name][0]
                return valid_values[idx]
            except:
                return val

class ArgumentError(Exception):
    '''Exception raised for invalid arguments.'''

    def __init__(self, msg, expr=None):
        self.msg = msg
        self.expr = expr

class WmiError(Exception):
    '''Exception raised for errors in the WMI service or connection.'''

    def __init__(self, error, msg=''):
        self.error = error
        hresult = None
        if 'result' in error.__dict__:
            hresult = ' [%d]' % error.hresult
        if 'excepinfo' in error.__dict__:
            msg = msg + '; '.join(
                filter(lambda e:
                           isinstance(e, unicode), error.excepinfo))
        self.msg = 'COM Error%s: %s' % (hresult or '', msg or '')
