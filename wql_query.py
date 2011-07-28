from time import strptime

import win32com
from win32com import client
win32com.client.gencache.is_readonly = False
win32com.client.gencache.GetGeneratePath()

from collections import namedtuple

class Wql_Query():

    def __init__(self, name_space = None, user = '', password = '',
				 property_enums = None):
        '''
        This class will use the default security context if not passed
	credentials. If you intend to make Wql_Query requests as part of a
	service, make sure that the service has valid login credentials to the
	DFSR server or its domain. WMI will kick an Access Denied error if
	you're using an NT5 platform querying a more modern platform.  We need
	to add
        '''
        if name_space:
            self.user = user
            self.password = password
            self.name_space = name_space
            self.property_enums = property_enums
        else:
            raise Exception('WMI namespace not provided.')

    def make_query(self, server_name = None, wql_query = None):
        '''
	This method will use the default security context.  WMI will kick an
	Access Denied error if you're using a NT5 platform querying NT6/7,
	even if the user has rights.  I need to set impersonation to the
	swbemlocator.

	Note: this method raises an exception on invalid WQL query syntax and
	other WMI errors, but does not verify the safety of the operation!
	WQL doesn\'t accept parameterized queries, so the caller must not
	pass untrusted data in the query string.
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
        Takes a list of ISWbemObjectSet instances and enumerates their
	properties, replacing enums with any friendly values provided in the
	constructor.  Returns a list of "Query_Result" named tuples.
        '''
        try:
            com_class_name = raw_query_results[0].Path_.Class

            Query_Result = namedtuple(com_class_name,
                                      [x.Name for x in
                                       raw_query_results[0].Properties_])

            if self.property_enums and com_class_name in self.property_enums:
                #remember to *unpack list arguments to instantiate a namedtuple!
                return [Query_Result (
                            *[self._get_friendly_value(com_class_name,
                                                       p.Name, p.Value)
                            for p in result.Properties_])
                        for result in raw_query_results]
            else:
                return [Query_Result(*result.Properties_) for
                        result in raw_query_results]

        except AttributeError:
            raise Exception(
                'AttributeError: Introspection failed on COM object. ' +
		'Make sure you have compiled makepy support in PythonWin '+
		'(Tools -> Com -> Makepy).')


    def _get_friendly_value(self, com_class_name, name, val):
        '''
        Replaces the unfriendly integer index value for the COM enums with the
        appropriate friendly string value in the property_enums dictionary, and
        converts UTC time stamps to struct_time objects for the caller to format.
	Note: WMI returns year 1601 or 9999 to indicate unfinished processes,
	but this will return only the standard 1601.
        '''
        if 'time' in name.lower():
            if val[:4] == '9999':
                val = '1601' + val[4:]
            return strptime(val[:-4], '%Y%m%d%H%M%S.%f')
        else:
            try:
                valid_values = self.property_enums[com_class_name][name][1]
                idx = val - self.property_enums[com_class_name][name][0]
                return valid_values[idx]
            except:
                return val


    def _handle_com_error(self, error):
        '''
        Verify that the error was kicked up by COM, and if so, raise a more
	user-friendly exception with the error code + explanation.  Otherwise,
	raise the original for handling by the caller.
        '''
        try:
            error_code = error.hresult
            if error.excepinfo is None:
                raise Error
            else:
                message = error.excepinfo[2]
            raise Exception('COM Error: %s [Error Code %s]' %
                            (message, error_code))
        except AttributeError, TypeError:
            raise error


