========
Overview
========

GilaMon is a simple monitoring tool for Windows `Distributed File System Replication`_ targeted for Windows system administrators.

It is *also* a set of tools written in `Python`_ that can be used by Windows system administrators who are comfortable with scripting to monitor DFSR or other Windows services through the `Windows Management Instrumentation`_ API.

GilaMon is `BSD licensed`_ and is designed to have cleanly separated architecture that will hopefully make hacking on the code easy even for novice programmers and/or system administrators who want to extend it.  The package described here includes an example implementation of a `CherryPy`_ web service and the web page that an administrator can use to view the current status of DFSR on their network.  You can use GilaMon's backend to monitor DFSR or any other WMI namespace without using the web service.

The backend for GilaMon makes WQL queries against your servers, performs introspection on the COM objects returned by WMI, and then gives you easy-to-comprehend tuples of key-value pairs.  The keys will always be the same as the named properties of WMI objects described in Microsoft's documentation, and the values will be friendly types such as strings, ints, and Python datetime objects.  For example, if you're making a query against the `DfsrReplicatedFolderInfo`_ class, you can check the documentation on MSDN to see that to find out the current size of the Staging folder, you should look at the ``CurrentStageSizeInMb`` property.


Motivation
==========

Why build something like this?  At `Burns Engineering, Inc.`_ where GilaMon was developed, we moved to DFSR in early 2010.  We used DFSR to replicate our main file shares between the home office and four remote sites, as well as a backup hub. All was well for quite some time. But we then had a minor catastrophe - a user saved a file, and it disappeared from the share.  This happened repeatedly over a short period of time, causing a lot of grief to our users.

We eventually isolated the problem to a particular application's files (Autodesk's `AutoCAD`_) and a particular replication connection to one of our branch offices with poor connectivity.  A support case with Microsoft went nowhere, and the only tools that Microsoft had available for us were log grubbers - it seemed impossible to catch DFSR in the act.  Eventually the problem "went away" on its own, but we knew that it was only a matter of time until it returned.

We decided we needed a dead-simple monitoring tool to tell us what the current status of DFSR replication was, and so GilaMon was born. An enlightened IT Manager agreed that this tool would be useful to share with our community, and that's why I've been able to release it publically.


Dependencies
============

GilaMon relies on COM and is currently supported only on Windows, and can be run from Windows XP, Vista, 7, Server 2008, and Server 2008r2.  Currently you need to run GilaMon from the same "generation" or newer of Windows as the DFSR server (ex. if you're running DFSR on Server 2008r2, you need to run GilaMon from Windows Vista, Windows 7, or Server 2008r).  This is next on the TODO list.  The backend for GilaMon requires:

  * `Python`_ (Tested with 2.7)
  * `pywin32`_ (Tested with Build216 and newer)
  * `mock`_ (You don't need this to run GilaMon, just to develop on it.)

The example GilaMon web service uses the following libraries:

  * `cherrypy`_
  * `jinja2`_


Browser Support
===============

The GilaMon example web service has been tested with Internet Explorer 7 and newer, and should work with other modern browsers as well.  Internet Explorer 6 and earlier is unsupported.

The backend of GilaMon is browser-independent.


Installation
============

There a couple different ways to install GilaMon, depending on what you want
to do with it.  You can:

  * Run the web service from a Windows executable.
  * Run as a Python service or script. [Recommended]
  * Run the web service as a Python script.
  * Run DFSR queries as a Python script.
  * Run arbitrary WMI queries as a Python script.

**Installing the Windows Executable**
_____________________________________
If you just want to run GilaMon as a Windows service, and don't plan on
making any changes to the code, you can just `download the Windows executables`_.  You can run the exectuable from a server and then use your workstation's web browser, or you can run the executable directly from your workstation and browse to ``localhost`` instead.

  * Download the file for your architecture (64 or 32 bit).
  * Unzip the archive into your Program Files directory.
  * Open a command line into the ``gilamon`` directory.
  * ``gilamon_service.exe -install``

``pywin32``, ``cherrypy`` and ``jinja2`` are bundled in the executable.  See the ``licenses`` folder in the zip file for the licenses for these libraries.


**Installing as a Python Service or Script [Recommended]**
__________________________________________________________
Running as a Python service is more complex if you don't already use Python.  But this is the recommended way to run GilaMon because it is easier to update your software or the libraries on which it depends.  You can also hack directly on the software without having to go through a complicated compiling process with ``py2exe``.  You'll need to do the following on the machine where you want to run the GilaMon web service (either your workstation or a server).

  * `Download and install Python`_ (2.7).
  * `Download and install setuptools`_
  * `Download and install pywin32`_ (Build 216 or newer)
  * Install CherryPy, by typing at the command line: ``easy_install cherrypy``
  * Install Jinja2, by typing at the command line: ``easy_install jinja2``
  * Either download the `current source code`_ zip archive for GilaMon or use `Mercurial`_ to clone the repository, and extract into your ``Python27/Lib/sites-packages`` directory.

If you want to run as a service instead of a script, also do the following:

  * Open a command line into the ``gilamon`` directory.
  * ``python setup.py -install``


Running GilaMon
===============

If you want to run GilaMon as a Windows service, whether from the executable or the Python code:
  * Use a text editor to change ``/gilamon/config/gilamon.conf`` to the port and address you want your service to list on. Also add the host names of your DFSR servers under the ``[dfsr]`` section.
  * Go to the Windows Start menu, and right-click on **Computer** (or **My Computer**, depending on your version) and select **Manage**.
  * Under **Services** you should now see GilaMon. Go to the service's properties, change the logon account if you need to, and set the service to Automatic start if you'd like.
  * Click Start to start your service.  If the service fails to start, you should see an event in your Event Viewer.
  * Point a web browser at the address and port you put in the ``gilamon.conf`` file.

If you want to run GilaMon with the web service as a Python script:
  * Use a text editor to change ``/gilamon/config/gilamon.conf`` to the port and address you want your service to list on. Also add the host names of your DFSR servers under the ``[dfsr]`` section.  * Use a text editor to change 
  * Go the command line and navigate to the ``gilamon`` directory.
  * ``python gila_mon.py``
  * Point a web browser at the address and port you put in the ``gilamon.conf`` file.

The ``gilamon.conf`` file uses Python syntax.  If you don't know Python, that's okay.  Just use the pattern that's been provided.  The IP address and server names have to be surrounded by quotes (either single or double is okay as long as they match), and the port number can't be in quotes.  Use forward slashes for the log file path, or double back-slashes.


If you want to run GilaMon as a script without the web service, you'll want to open Python interpreter and either ``import dfsr_query`` or ``import wql_query`` to get the modules you'll need for your purposes.  See the source code for documentation for these calls (``TODO:`` add this information to Wiki).

Support
=======

For general questions or comments, please `send me a message through Bitbucket`_. To report a bug or other type of issue, please use the `issue tracker`_.

Troubleshooting
===============

Following are what I suspect might be Frequently Asked Questions about installing and running GilaMon.

**The GilaMon service installs, but won't start.**
__________________________________________________
Check the Event Log.  It may show you that it's a configuration issue.  Make sure the IP and port number are valid.  If that's not it, please contact me or file an issue so that we can try to fix the problem (include the text of the event, if possible).

Also, make sure that you're Windows environment variables PYTHONPATH and PATH have been set.

**The GilaMon service installs and starts, but I get "Internet Explorer cannot view this page" on the web page.**
_________________________________________________________________________________________________________________
Make sure that the Windows firewall on the server running the web service allows the port you've listed in the ``gilamon.conf``.

**The GilaMon service installs and starts, but I get "ERROR: Failed to get connector states" on the web page.**
_______________________________________________________________________________________________________________
Check the log file found at ``C:/Windows/temp/gilamon.log`` (if you didn't change this path in your config).  You may see an Access Denied error in the stack trace.  Make sure the user that you're using for the GilaMon service has permissions to make WMI queries against the DFSR server (Server Manager -> Control -> WMI Control).

**Yeah, I tried that already.**
_______________________________
Currently, GilaMon uses the default WMI security context for passing credentials from the machine running GilaMon to the DFSR server it's querying.  But Windows operating systems with UAC (Vista, 7, Server 2008r2) have stricter controls by default.  So if you run GilaMon from an older OS and query a newer OS, you'll get an Access Denied error. This is next on my TODO list to fix.

**Nope, still doesn't work.**
_____________________________
Sorry about that!  Please use the `issue tracker`_ and file an issue so that I can fix the problem and improve GilaMon for everyone.  Please send along any relevant log information.


Contributing
============

GilaMon is an open source project managed using `Mercurial`_ version control. The repository is hosted on `Bitbucket`_, so contributing is simple: fork the project and commit back your changes. Please keep in mind the following about contributing:

  * Contributed code must be written in the existing style. Please follow `PEP 8`_ and check out your code with `pylint`_.
  * Run the tests before committing your changes. If your changes break the build, they won't be accepted.
  * If you're adding new functionality, you must include basic tests and documentation.


Future Features
===============

The following are features I'd like to add in the future:
  * ActiveDirectory-based authentication to the web page and general security improvements that would make it suitable to run on an Internet-facing page.
  * Set up and register for ``easy_install`` installation.
  * Support for running from Linux.  There's a Samba-based library for WMI, but it was more trouble that it was worth at the time of release.


.. _`Distributed File System Replication`: http://msdn.microsoft.com/en-us/library/bb540025(v=vs.85).aspx
.. _`Python`: http://python.org/
.. _`BSD licensed`: http://www.opensource.org/licenses/BSD-3-Clause
.. _`Windows Management Instrumentation`: http://msdn.microsoft.com/en-us/library/aa394582(v=vs.85).aspx
.. _`DfsrReplicatedFolderInfo`: http://msdn.microsoft.com/en-us/library/bb540019(v=VS.85).aspx
.. _`Burns Engineering, Inc.`: http://burns-group.com
.. _`AutoCAD`: http://usa.autodesk.com/autocad/

.. _`pywin32`: http://sourceforge.net/projects/pywin32/
.. _`CherryPy`: http://www.cherrypy.org/
.. _`cherrypy`: http://www.cherrypy.org/
.. _`jinja2`: http://jinja.pocoo.org/docs/
.. _`mock`: http://pypi.python.org/pypi/mock

.. _`download the Windows executables`: https://bitbucket.org/tgross/gilamon/downloads

.. _`download and install Python`: http://www.python.org/download/
.. _`download and install setuptools`: http://pypi.python.org/pypi/setuptools
.. _`download and install pywin32`: http://sourceforge.net/projects/pywin32/files/pywin32/
.. _`current source code`: https://bitbucket.org/tgross/gilamon/get/tip.zip
.. _`Mercurial`: http://mercurial.selenic.com/

.. _`Bitbucket`: http://bitbucket.org/tgross/gilamon/
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`pylint`: http://pypi.python.org/pypi/pylint
.. _`send me a message through Bitbucket`: https://bitbucket.org/account/notifications/send/?receiver=tgross
.. _`issue tracker`: https://bitbucket.org/tgross/gilamon/issues
