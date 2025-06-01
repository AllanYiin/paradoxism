from paradoxism.base.loop import PForEach, PMap, PFilter


def test_pforeach_simple():
    func = lambda x: x ** 2
    result = PForEach(func, range(5), max_workers=2, max_retries=1, output_type="dict")
    assert result == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}


def test_pmap_preserves_order():
    func = lambda x: x + 1
    result = list(PMap(func, range(3), max_workers=2))
    assert result == [1, 2, 3]


def test_pfilter_even():
    func = lambda x: x % 2 == 0
    result = PFilter(func, [1, 2, 3, 4, 5], max_workers=2)
    assert result == [2, 4]
