from __future__ import absolute_import
import inspect
import json
import locale
import os
import copy
import logging
import regex
import platform
import datetime
import time
import sys
import threading
import traceback
import linecache
from collections import OrderedDict
from functools import partial
import numpy as np
from pydoc import locate
from openai import AzureOpenAI,AsyncAzureOpenAI
from concurrent.futures import ThreadPoolExecutor
from typing import Union, List, Dict, Any
from typing import TypeAlias  # Python 3.10 開始支持 TypeAlias
from typing import get_type_hints



_paradoxism_context = None

__all__ = ["sanitize_path", "split_path", "make_dir_if_need", "_context", "get_sitepackages", "PrintException",
           "model_info","oai","get_class","JSON","xml","is_instance","get_time_suffix","get_sitepackages","get_optimal_workers"]




JSON: TypeAlias = Union[Dict[str, "JSON"], List["JSON"], str, int, float, bool, None]
xml:TypeAlias  = Union["ET.Element", "etree._Element"]



model_info ={k:{v2['model']: v2 for v2 in  v}  for k,v in eval(open(os.path.join(os.path.dirname(__file__),'model_infos.json'), 'r',encoding="utf-8").read()).items()}
oai={}
if os.path.exists(os.path.join(os.path.dirname(__file__),'oai.json')):
    oai={v['azure_deployment']: v for v in eval(open(os.path.join(os.path.dirname(__file__), 'oai.json'), encoding="utf-8").read())['azure']}

def sanitize_path(path):
    """Sanitize the file or folder path, a same-format and absoluted path will return.

    Args:
        path (str): a path of file or folder

    Returns:
        sanitized path

    Examples:
        >>> print(sanitize_path('~/.paradoxism/datasets'))
        C:/Users/allan/.paradoxism/datasets

    """
    if path.startswith('~/'):
        path = os.path.join(os.path.expanduser("~"), path[2:])
    path = os.path.abspath(path)
    return path.strip().replace('\\', '/')
    # if isinstance(path, str):
    #     return os.path.normpath(path.strip()).replace('\\', '/')
    # else:
    #     return path


def split_path(path: str):
    """split path into folder, filename and ext 3 parts clearly.

    Args:
        path (str): a path of file or folder

    Returns:
        folder, filename and ext

    Examples:
        >>> print(split_path('C:/.paradoxism/datasets/cat.jpg'))
        ('C:/.paradoxism/datasets', 'cat', '.jpg')
        >>> print(split_path('C:/.paradoxism/models/resnet.pth.tar'))
        ('C:/.paradoxism/models', 'resnet', '.pth.tar')

    """
    if path is None or len(path) == 0:
        return '', '', ''
    path = sanitize_path(path)
    folder, filename = os.path.split(path)
    ext = ''
    if '.' in filename:
        filename, ext = os.path.splitext(filename)
        # handle double ext, like 'mode.pth.tar'
        if ext in ['.tar', '.pth', '.pkl', '.ckpt', '.bin', '.pt', '.zip']:
            filename, ext2 = os.path.splitext(filename)
            ext = ext2 + ext
    else:
        folder = os.path.join(folder, filename)
        filename = ''
    return folder, filename, ext


def make_dir_if_need(path):
    """Check the base folder in input path whether exist, if not , then create it.

    Args:
        path (str): a path of file or folder

    Returns:
        sanitized path

    """
    folder, filename, ext = split_path(path)
    if len(folder) > 0 and not os.path.exists(folder):
        try:
            os.makedirs(folder)
        except Exception as e:
            print(e)
            sys.stderr.write('folder:{0} is not valid path'.format(folder))
    return sanitize_path(path)


def is_instance(instance, check_class):
    if not inspect.isclass(instance) and inspect.isclass(check_class):
        mro_list = [b.__module__ + '.' + b.__qualname__ for b in instance.__class__.__mro__]
        return check_class.__module__ + '.' + check_class.__qualname__ in mro_list
    elif inspect.isclass(instance) and isinstance(check_class, str):
        mro_list = [b.__module__ + '.' + b.__qualname__ for b in instance.__mro__]
        mro_list2 = [b.__qualname__ for b in instance.__mro__]
        return check_class in mro_list or check_class in mro_list2
    elif not inspect.isclass(instance) and isinstance(check_class, str):
        mro_list = [b.__module__ + '.' + b.__qualname__ for b in instance.__class__.__mro__]
        mro_list2 = [b.__qualname__ for b in instance.__class__.__mro__]
        return check_class in mro_list or check_class in mro_list2
    elif isinstance(check_class, tuple):
        return any([is_instance(instance, cc) for cc in check_class])
    else:
        if not inspect.isclass(check_class):
            print(red_color('Input check_class {0} should a class, but {1}'.format(check_class, type(check_class))))
        return False


def PrintException():
    """
        Print exception with the line_no.

    """
    exc_type, exc_obj, tb = sys.exc_info()
    traceback.print_exception(*sys.exc_info())
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}\n'.format(filename, lineno, line.strip(), exc_obj))
    traceback.print_exc(limit=None, file=sys.stderr)
    # traceback.print_tb(tb, limit=1, file=sys.stdout)
    # traceback.print_exception(exc_type, exc_obj, tb, limit=2, file=sys.stdout)



def get_sitepackages():  # pragma: no cover
    installed_packages = None
    try:
        import subprocess
        import sys

        reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
        installed_packages = [r.decode().split('==')[0] for r in reqs.split()]
        return installed_packages

    # virtualenv does not ship with a getsitepackages impl so we fallback
    # to using distutils if we can
    # https://github.com/pypa/virtualenv/issues/355
    except Exception as e:
        print(e)
        try:
            from distutils.sysconfig import get_python_lib

            return [get_python_lib()]

        # just incase, don't fail here, it's not worth it
        except Exception:
            return []


def get_time_suffix():
    """

    Returns:
        timestamp string , usually use when save a file.

    """
    prefix = str(datetime.datetime.fromtimestamp(time.time())).replace(' ', '').replace(':', '').replace('-',
                                                                                                         '').replace(
        '.', '')
    return prefix


def get_class(class_name, module_paths=None):
    """
    Returns the class based on class name.

    Args:
        class_name (str): Name or full path to the class.
        module_paths (list): Paths to candidate modules to search for the
            class. This is used if the class cannot be located solely based on
            ``class_name``. The first module in the list that contains the class
            is used.

    Returns:
        The target class.

    Raises:
        ValueError: If class is not found based on :attr:`class_name` and
            :attr:`module_paths`.

    """
    class_ = None
    if (class_name is not None) and (module_paths is not None):
        for module_path in module_paths:
            class_ = locate('.'.join([module_path, class_name]))
            if class_ is not None:
                return class_

    if class_ is None:
        class_ = locate(class_name)
        raise ValueError("Class not found in {}: {}".format(module_paths, class_name))
    return class_  # type: ignore



def get_optimal_workers():
    """
    獲取合理的工作者數量，基於當前的 CPU 核心數量和系統負載。

    :return: 最佳的工作者數量
    """
    cpu_count = os.cpu_count() or 1
    load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0
    # 改進估算：基於 CPU 核心數量，並根據當前系統負載動態調整
    # 如果負載遠高於 CPU 核心數，減少 worker 數量；負載較低時增加 worker 數量
    if load_avg > cpu_count * 1.5:
        optimal_workers = max(1, int(cpu_count / 4))  # 負載過高，僅保留四分之一的 worker
    elif load_avg > cpu_count:
        optimal_workers = max(1, int(cpu_count / 2))  # 負載高，減少一半的 worker
    else:
        optimal_workers = max(1, int(cpu_count / (1 + load_avg)))  # 負載適中或低，動態調整
    return optimal_workers


class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.regex = regex.compile(r"^(?!INFO:).*", regex.MULTILINE)
        self.log = open(filename, "a")

    def __getattr__(self, name):
        if name in ('terminal', 'regex', 'log'):
            return self.__dict__[name]
        else:
            return getattr(self.terminal, name)

    def write(self, message):
        self.terminal.write(message)

        filted_message = "\n".join(self.regex.findall(message))
        self.log.write(filted_message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def isatty(self):
        return False


class _ThreadLocalInfo(threading.local):
    """
    Thread local Info used for store thread local attributes.
    """

    def __init__(self):
        super(_ThreadLocalInfo, self).__init__()
        self._reserve_class_name_in_scope = True

    @property
    def reserve_class_name_in_scope(self):
        """Gets whether to save the network class name in the scope."""
        return self._reserve_class_name_in_scope

    @reserve_class_name_in_scope.setter
    def reserve_class_name_in_scope(self, reserve_class_name_in_scope):
        """Sets whether to save the network class name in the scope."""
        if not isinstance(reserve_class_name_in_scope, bool):
            raise ValueError(
                "Set reserve_class_name_in_scope value must be bool!")
        self._reserve_class_name_in_scope = reserve_class_name_in_scope


class _Context:
    """
    _Context is the environment in which operations are executed
    Note:
        Create a context through instantiating Context object is not recommended.
        should use context() to get the context since Context is singleton.
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __init__(self):
        super().__setattr__('is_initialized', False)
        self.oai=None
        self._thread_local_info = _ThreadLocalInfo()
        self._context_handle = OrderedDict()
        self._errors_config = OrderedDict()
        self._module_dict = dict()
        self.conversation_history = None
        self.print = partial(print, flush=True)
        self.executor = ThreadPoolExecutor(max_workers=8)


        self.oai = {v['azure_deployment']: v for v in eval(open(os.path.join(split_path(__file__)[0],'oai.json'), encoding="utf-8").read())['azure']}
        self.log_path = None
        self.paradoxism_dir = self.get_paradoxism_dir()
        self.service_type = None
        self.deployments = []
        self.baseChatGpt = None
        self.docChatGpt = None
        self.summaryChatGpt = None
        self.imageChatGpt = None
        self.otherChatGpt = None
        self.state = None
        self.assistant_state = None
        self.status_word = ''
        self.counter = 0
        self.memory = None
        self.sql_engine = None
        self.conn_string = None
        self.databse_schema = None
        self.is_db_enable = False
        self.numpy_print_format = '{0:.4e}'
        self.plateform = None
        self.whisper_model = None
        self.current_assistant = None
        self.assistants = []
        self.placeholder_lookup = {}
        self.citations = []

        # 設定日誌配置
        logging.basicConfig(level=logging.ERROR,format='%(asctime)s - %(levelname)s - %(message)s - %(name)s - %(funcName)s - %(lineno)d')

        if os.path.exists(os.path.join(self.get_paradoxism_dir(), 'session.json')):
            self.load_session(os.path.join(self.get_paradoxism_dir(), 'session.json'))

        else:
            self.conversation_history = None
            self.locale = locale.getdefaultlocale()[0].lower()

            self.plateform = self.get_plateform()
            self.numpy_print_format = '{0:.4e}'
            np.set_printoptions(formatter={'float_kind': lambda x: self.numpy_print_format.format(x)}, precision=4,
                                suppress=True)
            self.is_db_enable = False
        self.conn_string = 'mssql+pyodbc://@' + 'localhost' + '/' + 'AdventureWorksDW2022' + '?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'
        self.databse_schema = None

        if 'PARADOXISM_WORKING_DIR' in os.environ:
            self.working_directory = os.environ['PARADOXISM_WORKING_DIR']
            os.chdir(os.environ['PARADOXISM_WORKING_DIR'])
        else:
            current_dir = os.path.dirname(os.path.realpath(__file__))
            os.chdir(current_dir)
            self.working_directory = os.getcwd()

        super().__setattr__('is_initialized', True)
        self.write_session()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance_lock.acquire()
            cls._instance = object.__new__(cls)
            cls._instance_lock.release()
        return cls._instance

    def get_paradoxism_dir(self):
        """Get or create paradoxism directory
        1)  read from
         enviorment variable 'PARADOXISM_HOME'
        2) use default directory '~/.paradoxism'
        3) if the directory not exist, create it!

        Returns:
            the  paradoxism directory path

        """
        _paradoxism_dir = ''
        if 'PARADOXISM_HOME' in os.environ:
            _paradoxism_dir = os.environ.get('PARADOXISM_HOME')
        else:
            _paradoxism_base_dir = os.path.expanduser('~')
            if not os.access(_paradoxism_base_dir, os.W_OK):
                _paradoxism_dir = '/tmp/.paradoxism'
            else:
                _paradoxism_dir = os.path.expanduser('~/.paradoxism')

        _paradoxism_dir = sanitize_path(_paradoxism_dir)
        if not os.path.exists(_paradoxism_dir):
            try:
                os.makedirs(_paradoxism_dir)
            except OSError as e:
                # Except permission denied and potential race conditions
                # in multi-threaded environments.
                print(e)

        return _paradoxism_dir

    def get_plateform(self):
        """

        Returns:
            check current system os plateform.

        """
        plateform_str = platform.system().lower()
        if 'darwin' in plateform_str:
            return 'mac'
        elif 'linux' in plateform_str:
            return 'linux'
        elif 'win' in plateform_str:
            return 'windows'
        else:
            return plateform_str

    def __getattribute__(self, attr):
        value = object.__getattribute__(self, attr)
        if attr == "_context_handle" and value is None:
            raise ValueError("Context handle is none in context!!!")
        return value

    @property
    def module_dict(self):
        return self._module_dict

    def get_module(self, cls_name, module_name='module'):
        """Get the registry record.
        Args:
            module_name ():
            cls_name ():
        Returns:
            class: The corresponding class.
        """
        if module_name not in self._module_dict:
            raise KeyError('{module_name} is not in registry')
        dd = self._module_dict[module_name]
        if cls_name not in dd:
            raise KeyError('{cls_name} is not registered in {module_name}')

        return dd[cls_name]

    def write_session(self, session_path=None):
        if session_path is None:
            session_path = os.path.join(self.get_paradoxism_dir(), 'session.json')
        try:
            with open(session_path, 'w') as f:
                session = self.__dict__.copy()
                session.pop('oai')
                session.pop('baseChatGpt')
                session.pop('executor')
                session.pop('_thread_local_info')
                session.pop('_context_handle')
                session.pop('_module_dict')
                session.pop('conversation_history')
                session.pop('is_initialized')
                session.pop('sql_engine')
                session.pop('status_word')
                session.pop('counter')
                session.pop('print')
                session.pop('current_assistant')
                session.pop('assistant_state')
                session.pop('placeholder_lookup')
                session.pop('citations')
                session.pop('memory')
                session.pop('whisper_model')

                session['agents'] = [a.json() if is_instance(a, "Assistant") else a for a in self.assistants]
                session['docChatGpt'] = self.docChatGpt if isinstance(self.docChatGpt,
                                                                        str) else self.docChatGpt.api_model if self.docChatGpt else None
                session['summaryChatGpt'] = self.summaryChatGpt if isinstance(self.summaryChatGpt,
                                                                              str) else self.summaryChatGpt.api_model if self.summaryChatGpt else None
                session['imageChatGpt'] = self.imageChatGpt if isinstance(self.imageChatGpt,
                                                                          str) else self.imageChatGpt.api_model if self.imageChatGpt else None
                session['otherChatGpt'] = self.otherChatGpt if isinstance(self.otherChatGpt,
                                                                          str) else self.otherChatGpt.api_model if self.otherChatGpt else None
                session['state'] = self.state if isinstance(self.state, str) else str(
                    self.state.value) if self.state else None

                f.write(json.dumps(session, indent=4, ensure_ascii=False))
        except IOError:
            # Except permission denied.
            pass

    def load_session(self, session_path=None):
        if session_path is None:
            session_path = os.path.join(self.get_paradoxism_dir(), 'session.json')

        if os.path.exists(session_path):
            try:
                with open(session_path) as f:
                    _session = json.load(f)
                    for k, v in _session.items():
                        try:
                            self.__setattr__(k, v)

                            if k == 'service_type' and self.service_type is None:
                                self.__setattr__(k, 'openai')

                        except Exception as e:
                            print(e)
            except ValueError as ve:
                print(ve)

    def regist_resources(self, resource_name, resource):
        if not hasattr(self._thread_local_info, 'resources'):
            self._thread_local_info.resources = OrderedDict()
        self._thread_local_info.resources[resource_name] = resource
        return self._thread_local_info.resources[resource_name]

    def get_resources(self, resource_name):
        if not hasattr(self._thread_local_info, 'resources'):
            self._thread_local_info.resources = OrderedDict()
        if resource_name in self._thread_local_info.resources:
            return self._thread_local_info.resources[resource_name]
        else:
            return None

    def __setattr__(self, name: str, value) -> None:
        try:
            object.__setattr__(self, name, value)
            if self.is_initialized:
                self.write_session(os.path.join(self.get_paradoxism_dir(), 'session.json'))
        except Exception as e:
            print(name, value, e)
            PrintException()


def _context():
    """
    Get the global _context, if context is not created, create a new one.
    Returns:
        _Context, the global context in PyNative mode.
    """
    global _paradoxism_context
    if _paradoxism_context is None:
        _paradoxism_context = _Context()
    return _paradoxism_context


make_dir_if_need(os.path.join(_context().get_paradoxism_dir(), "logs"))
log_path = os.path.join(_context().get_paradoxism_dir(), "logs", "{0}.log".format(get_time_suffix()[:8]))
_context().log_path = log_path
sys.stdout = Logger(log_path)



