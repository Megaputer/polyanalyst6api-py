import pkg_resources

__version__ = pkg_resources.get_distribution(__name__).version

from .api import *
from .exceptions import *
