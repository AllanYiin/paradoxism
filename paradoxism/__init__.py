from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
import os
import logging
from typing import Union, List, Dict, Any
# 檢查 Python 版本



defaultencoding = 'utf-8'
if sys.getdefaultencoding() != defaultencoding:
    logging.getLogger(__name__).debug(
        "Expected default encoding %s but got %s", defaultencoding, sys.getdefaultencoding()
    )

PACKAGE_ROOT = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(PACKAGE_ROOT)

__version__ = '0.0.3'
logger = logging.getLogger(__name__)
logger.info('PARADOXISM %s', __version__)

