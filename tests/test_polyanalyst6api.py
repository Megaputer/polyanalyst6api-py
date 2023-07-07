import warnings

import polyanalyst6api as pa
import pytest


def test_api_version_arg_is_deprecated():
    with pytest.warns(DeprecationWarning):
        pa.API('https://localhost:5043', '', version=1)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        pa.API('https://localhost:5043', '')
