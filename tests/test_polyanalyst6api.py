import warnings

import polyanalyst6api as pa
import pytest


def test_version():
    mj, mn, pch = pa.__version__.split('.')
    assert int(mj) == 0 and int(mn) >= 26 and pch != ''


def test_api_version_arg_is_deprecated():
    with pytest.warns(DeprecationWarning):
        pa.API('https://localhost:5043', '', version=1)
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        pa.API('https://localhost:5043', '')
