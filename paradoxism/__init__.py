from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
import os
from importlib import reload
from sys import stderr
from typing import Union, List, Dict, Any
# 檢查 Python 版本



defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    reload(sys)
    sys.setdefaultencoding(defaultencoding)

PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(PACKAGE_ROOT)

__version__ = '0.0.3'
stderr.write('PARADOXISM {0}\n'.format(__version__))

