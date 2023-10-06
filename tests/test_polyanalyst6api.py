import polyanalyst6api as pa


def test_version():
    mj, mn, pch = pa.__version__.split('.')
    assert int(mj) == 0 and int(mn) >= 30 and pch != ''
