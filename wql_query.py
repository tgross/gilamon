from time import strptime

import win32com
from win32com import client
win32com.client.gencache.is_readonly = False
win32com.client.gencache.GetGeneratePath()

from collections import namedtuple

class Wql_Query():

    def __init__(self, name_space = None, credentials = None, property_enums = None):
        '''
        TODO: this will use the current security context.  I'm not sure if this is
        going to give us trouble when we try to run the monitor as a service.  I
        think we might need to "impersonate" the user.
        '''
        if name_space:
            self.name_space = name_space
            self.user = '' #credentials[0]
            self.password = '' #credentials[1]
            self.PROPERTY_ENUMS = property_enums
        else:
            raise Exception('You need to supply a WMI namespace and credentials')

    def make_query(self, server_name = None, wql_query = None):
        '''
        Uses Kerberos authentication if available.
        See also http://msdn.microsoft.com/en-us/library/aa393720(v=vs.85).aspx 
        Note: this method raises an exception on invalid WQL query syntax, but
        does not verify the safety of the operation!  The caller should not pass
        untrusted data in the query string!
        '''
        try:
            wbem_locator = win32com.client.Dispatch('wbemscripting.swbemlocator')
            remote_service = wbem_locator.ConnectServer(
                server_name, self.name_space, self.user, self.password
                )
            query_results = remote_service.ExecQuery(wql_query)
            if len(query_results) < 1:
                return []

            return self._unpack_query_results(query_results)
        except Exception as e:
            self._handle_com_error(e)


    def _unpack_query_results(self, raw_query_results):
        '''
        Takes a list of ISWbemObjectSet instances and enumerates their properties,
        replacing enums with any friendly values provided in the constructor.  Returns
        a list of "Query_Result" named tuples.
        '''
        try:
            com_class_name = raw_query_results[0].Path_.Class
            
            Query_Result = namedtuple(com_class_name,
                                      [x.Name for x in raw_query_results[0].Properties_])

            if self.PROPERTY_ENUMS and com_class_name in self.PROPERTY_ENUMS:
                #remember to *unpack list arguments to instantiate a namedtuple!
                return [Query_Result (
                            *[self._get_friendly_value(com_class_name, p.Name, p.Value)
                            for p in result.Properties_])
                        for result in raw_query_results]
            else:
                return [Query_Result(*result.Properties_) for result in raw_query_results]

        except AttributeError:
            raise Exception(
                'AttributeError: Introspection failed on COM object.\
 Make sure you have compiled makepy support in PythonWin\
(Tools -> Com -> Makepy).')


    def _get_friendly_value(self, com_class_name, name, val):
        '''
        Replaces the unfriendly integer index value for the COM enums with the
        appropriate friendly string value in the PROPERTY_ENUMS dictionary, and
        converts UTC time stamps to struct_time objects for the caller to format.
        '''
        if 'time' in name.lower():
            #9999 will throw a range error but has the same meaning as 1601
            if val[:4] == '9999':
                val = '1601' + val[4:]
            #Time values are returned by win32com in UTC format:
            #u'20110707040008.293569-000'
            return strptime(val[:-4], '%Y%m%d%H%M%S.%f')
        else:
            try:
                valid_values = self.PROPERTY_ENUMS[com_class_name][name][1]
                idx = val - self.PROPERTY_ENUMS[com_class_name][name][0]
                return valid_values[idx]
            except:
                return val


    def _handle_com_error(self, error):
        '''
        Verify that the error was kicked up by COM, and if so, raise a more user-friendly
        exception with the error code + explanation.  Otherwise, raise the original for
        handling by the caller.
        '''
        try:
            error_code = error.hresult
            #TODO: not properly catching null excepinfo values from COM?
            if not error.excepinfo is None:
                message = error.excepinfo[2]
            else:
                raise error
            raise Exception('COM Error: %s [Error Code %s]' % (message, error_code))
        except AttributeError, TypeError: 
            raise error

        