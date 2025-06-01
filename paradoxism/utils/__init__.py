import json
import os
import sys
import traceback
import inspect
import linecache
import logging
__all__ = ['PrintException', 'sanitize_path', 'split_path', 'make_dir_if_need','yellow_color','red_color','gray_color','green_color','orange_color','blue_color','cyan_color','violet_color']





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
    logging.error('EXCEPTION IN (%s, LINE %s "%s"): %s', filename, lineno, line.strip(), exc_obj)
    traceback.print_exc(limit=None, file=sys.stderr)
    # traceback.print_tb(tb, limit=1, file=sys.stdout)
    # traceback.print_exception(exc_type, exc_obj, tb, limit=2, file=sys.stdout)



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
            logging.error(e)
            sys.stderr.write('folder:{0} is not valid path'.format(folder))
    return sanitize_path(path)


def red_color(text, bolder=False):
    if bolder:
        return '\033[1;31m{0}\033[0;0m'.format(text)
    else:
        return '\033[31m{0}\033[0;0m'.format(text)


def green_color(text, bolder=False):
    if bolder:
        return '\033[1;32m{0}\033[0;0m'.format(text)
    else:
        return '\033[32m{0}\033[0;0m'.format(text)


def blue_color(text, bolder=False):
    if bolder:
        return '\033[1;34m{0}\033[0m'.format(text)
    else:
        return '\033[34m{0}\033[0;0m'.format(text)


def cyan_color(text, bolder=False):
    if bolder:
        return '\033[1;36m{0}\033[0m'.format(text)
    else:
        return '\033[36m{0}\033[0;0m'.format(text)


def yellow_color(text, bolder=False):
    if bolder:
        return '\033[1;93m{0}\033[0m'.format(text)
    else:
        return '\033[93m{0}\033[0;0m'.format(text)


def orange_color(text, bolder=False):
    if bolder:
        return u'\033[1;33m%s\033[0m' % text
    else:
        return '\033[33m{0}\033[0;0m'.format(text)


def gray_color(text, bolder=False):
    if bolder:
        return u'\033[1;337m%s\033[0m' % text
    else:
        return '\033[37m{0}\033[0;0m'.format(text)


def violet_color(text, bolder=False):
    if bolder:
        return u'\033[1;35m%s\033[0m' % text
    else:
        return '\033[35m{0}\033[0;0m'.format(text)


def magenta_color(text, bolder=False):
    if bolder:
        return u'\033[1;35m%s\033[0m' % text
    else:
        return '\033[35m{0}\033[0;0m'.format(text)


def get_function(fn_name, module_paths=None):
    """
    Returns the function based on function name.

    Args:
        fn_name (str): Name or full path to the class.
        module_paths (list): Paths to candidate modules to search for the
            class. This is used if the class cannot be located solely based on
            ``class_name``. The first module in the list that contains the class
            is used.

    Returns:
        The target function.

    Raises:
        ValueError: If class is not found based on :attr:`class_name` and
            :attr:`module_paths`.

    """
    if callable(fn_name):
        return fn_name
    fn = None
    if (fn_name is not None) and (module_paths is not None):
        for module_path in module_paths:
            fn = locate('.'.join([module_path, fn_name]))
            if fn is not None:
                break

    if fn is None:
        fn = locate(fn_name)
        if fn is not None:
            return fn
        else:
            return None
    else:
        return fn  # type: ignore