from cleansweep.helpers import safeint


def test_safeint():
    assert safeint("123") == 123
    assert safeint("123x", default=1) == 1
    assert safeint("-1", default=1, minvalue=1) == 1
    assert safeint("100", default=1, maxvalue=35) == 35