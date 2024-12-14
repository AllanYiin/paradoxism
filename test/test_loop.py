import unittest
from paradoxism.base.loop import PCombinations, PForEach,  PAccumulate, PMap, PFilter, PChain



class TestParallelFunctions(unittest.TestCase):
    #
    # def test_PCombinations_with_generator(self):
    #     func = lambda x: sum(x)
    #     generator = (i for i in range(5))
    #     result = PCombinations(func, generator, 2, max_workers=2)
    #     expected ={(0, 1): 1, (0, 2): 2, (0, 3): 3, (0, 4): 4, (1, 2): 3, (1, 3): 4, (1, 4): 5, (2, 3): 5, (2, 4): 6, (3, 4): 7}
    #     self.assertEqual(sorted(result.items()), sorted(expected.items()))

    def test_PForEach_with_simple_function(self):

        func = lambda x:  x ** 2
        results=PForEach(func,range(5),  max_workers=2, max_retries=3,output_type='dict')
        expected = {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
        self.assertEqual(sorted(results.items()), sorted(expected.items()))

    # def test_PForEach_with_complex_function(self):
    #     results = {}
    #     func = lambda x: results.update({x: x ** 2 })
    #     PForEach(func,range(5), max_workers=2, max_retries=3)
    #     expected = {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
    #     self.assertEqual(sorted(results.items()), sorted(expected.items()))
    #
    #
    #
    # # def test_PAccumulate_with_error_and_retries(self):
    # #     inputs = [1, 2, 4]
    # #     func = lambda x: x if x != 4 else 1 / 0
    # #     result = PAccumulate(inputs, func, max_workers=2)
    # #     expected = {0: 1, 1: 3, 2: 7}
    # #     self.assertEqual(sorted(result.items()), sorted(expected.items()))
    #
    # def test_PMap_with_generator_and_complex_function(self):
    #     func = lambda x: x ** 2 if x != 3 else 1 / 0
    #     generator = (x for x in range(5))
    #     result = PMap(func,generator, max_workers=2)
    #     expected = {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
    #     self.assertEqual(sorted(result.items()), sorted(expected.items()))
    #
    # def test_PFilter_with_list_and_generator(self):
    #     func = lambda x: x % 2 == 0
    #     result_list = PFilter(func,[1, 2, 3, 4, 5], max_workers=2)
    #     expected = [2,4]
    #     self.assertEqual(sorted(result_list), sorted(expected))
    #
    #     generator = (x for x in [1, 2, 3, 4, 5])
    #     result_gen = PFilter(func,generator, max_workers=2)
    #     self.assertEqual(sorted(result_gen), sorted(expected))
    #
    # def test_PChain_with_multiple_iterables(self):
    #     iterables = [[1, 2], (3, 4), (i for i in [5])]
    #     result = dict(enumerate(PChain(*iterables)))
    #     expected = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5}
    #     self.assertEqual(sorted(result.items()), sorted(expected.items()))


if __name__ == '__main__':
    unittest.main()
