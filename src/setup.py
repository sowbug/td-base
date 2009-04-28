# Thanks to
#http://www.moviepartners.com/blog/2009/03/20/making-py2exe-play-nice-with-pygame/

# py2exe setup program
from distutils.core import setup
import py2exe, pygame
import sys
import os
import glob, shutil
sys.argv.append('py2exe')

DIST_DIR='dist/'

VERSION = '0.1'
AUTHOR_NAME = 'Mike Tsao'
AUTHOR_EMAIL = 'mike.tsao@gmail.com'
AUTHOR_URL = 'http://www.sowbug.org/'
PRODUCT_NAME = 'Tower Defense'
SCRIPT_MAIN = 'src/main.py'
VERSIONSTRING = PRODUCT_NAME + ' ALPHA ' + VERSION
ICONFILE = 'assets/application.ico'

INCLUDE_STUFF = [
                 'encodings',
                 'encodings.latin_1',
                 ]

MODULE_EXCLUDES = [
'email',
'AppKit',
'Foundation',
'bdb',
'difflib',
'tcl',
'Tkinter',
'Tkconstants',
'curses',
'distutils',
'setuptools',
'urllib',
'urllib2',
'urlparse',
'BaseHTTPServer',
'_LWPCookieJar',
'_MozillaCookieJar',
'ftplib',
'gopherlib',
'_ssl',
'htmllib',
'httplib',
'mimetools',
'mimetypes',
'rfc822',
'tty',
'webbrowser',
'socket',
'hashlib',
'base64',
'compiler',
'pydoc'
]

# Remove the build tree on exit automatically
REMOVE_BUILD_ON_EXIT = True

if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
 
extra_files = [
('', ['README.txt', 'LICENSE.txt', ]),
('assets', glob.glob(os.path.join('assets', '*.png'))),
('assets', glob.glob(os.path.join('assets', '*.wav'))),
('assets', glob.glob(os.path.join('assets', '*.ico'))),
('assets', glob.glob(os.path.join('assets', '*.sfs'))),
('assets', glob.glob(os.path.join('assets', '*.otf'))),
('src', glob.glob(os.path.join('src', '*.py'))),
]

setup(windows=[{'script': SCRIPT_MAIN,
'other_resources': [(u'VERSIONTAG', 1, VERSIONSTRING)],
'icon_resources': [(1, ICONFILE)],
'dest_base': PRODUCT_NAME,
}],
options={'py2exe': { 'optimize': 2,
                     'includes': INCLUDE_STUFF,
                     'compressed': 1,
                     'ascii': 1,
                     'bundle_files': 2,
                     'ignores': ['tcl', 'AppKit', 'Numeric', 'Foundation'],
                     'excludes': MODULE_EXCLUDES} },
name=PRODUCT_NAME,
version=VERSION,
data_files=extra_files,
zipfile=None,
author=AUTHOR_NAME,
author_email=AUTHOR_EMAIL,
url=AUTHOR_URL
)
 
# Remove the build tree
if REMOVE_BUILD_ON_EXIT: shutil.rmtree('build/')
