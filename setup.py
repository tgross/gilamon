from distutils.core import setup
import py2exe
import platform

# Leave out any package not strictly necessary.
# TODO: There are almost certainly some more that can be removed.
# Definitely leave in the _ssl module, because CherryPy relies on
# it even though we're not using it.
excludes = [
            '_tkinter', 'Tkconstants', 'Tkinter', 'tcl',
            'win32com.gen_py', #leave this out to dynamically generate typelibs!
            ]

# These are Windows system DLLs, and we don't want to (and
# aren't allowed to) redistribute.
dll_excludes = [
    'msvcr71.dll',
    'mfc90.dll',
    'API-MS-Win-Core-ErrorHandling-L1-1-0.dll',
    'API-MS-Win-Core-LibraryLoader-L1-1-0.dll',
    'API-MS-Win-Core-LocalRegistry-L1-1-0.dll',
    'API-MS-Win-Core-Misc-L1-1-0.dll',
    'API-MS-Win-Core-ProcessThreads-L1-1-0.dll',
    'API-MS-Win-Core-Profile-L1-1-0.dll',
    'API-MS-Win-Core-Synch-L1-1-0.dll',
    'API-MS-Win-Core-SysInfo-L1-1-0.dll',
    'API-MS-Win-Security-Base-L1-1-0.dll',
    'CFGMGR32.dll',
    'DEVOBJ.dll',
    'MPR.dll',
    'POWRPROF.dll',
    'SETUPAPI.dll',
    ]

# List of packages that need to be included but that py2exe is
# missing. (placeholder)
#mod_includes = []
package_includes = []


py2exe_opts= {
    'excludes': excludes,
    'dll_excludes': dll_excludes,
    'packages': package_includes,
    'compressed': True, #compresses Library
    'optimize': 2, #generate .pyo w/ -OO options
    }

if not platform.architecture()[0] == '64bit':
    py2exe_opts['bundle_files'] = 2 #not supported on win64

#TODO: port these all automatically instead of manual copy
additional_files = [
    ('config',[]),
    ('templates',[]),
    ('static',[]),
    ('licenses',[]),
    ]

setup (
    version = '0.8.1',
    description = 'GilaMon DFSR Monitor',
    name = 'GilaMon',
    author = 'Tim Gross',
    author_email = 'gross.timothy@gmail.com',
    url = 'https://bitbucket.org/tgross/gilamon',
    options = { 'py2exe': py2exe_opts },
    service = ['gilamon'],
    data_files = additional_files,
)
