from distutils import setup
import py2exe

setup (
    version = '0.8.0',
    description = 'GilaMon DFSR Monitor',
    name = 'GilaMon',
    options = {
        'py2exe': {
            'compressed': 1,
            'optimize': 2,
            'bundle_files': 2,
            'excludes': 'OpenSSL, Tkinter',
            'packages': ['encodings', 'email']
            }
         },
    console = ['gilamon_service.py'],
)
