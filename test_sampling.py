# -*- coding: utf-8 -*-
import unittest
from logis.core.sampling import DeterministicRandom, DEFAULT_SEED


class TestSampling(unittest.TestCase):

    def test_default_seed(self):
        rnd1 = DeterministicRandom()
        rnd2 = DeterministicRandom(DEFAULT_SEED)
        self.assertEqual(rnd1.randrange(100), rnd2.randrange(100))

    def test_reproducibility(self):
        rnd1 = DeterministicRandom(123)
        rnd2 = DeterministicRandom(123)
        values1 = [rnd1.randrange(1000) for _ in range(20)]
        values2 = [rnd2.randrange(1000) for _ in range(20)]
        self.assertEqual(values1, values2)

    def test_different_seeds_diverge(self):
        rnd1 = DeterministicRandom(1)
        rnd2 = DeterministicRandom(2)
        values1 = [rnd1.randrange(1000) for _ in range(20)]
        values2 = [rnd2.randrange(1000) for _ in range(20)]
        self.assertNotEqual(values1, values2)

    def test_randrange_valid_and_invalid(self):
        rnd = DeterministicRandom(42)
        val = rnd.randrange(10)
        self.assertTrue(0 <= val < 10)

        with self.assertRaises(ValueError):
            rnd.randrange(0)
        with self.assertRaises(ValueError):
            rnd.randrange(-5)
        with self.assertRaises(ValueError):
            rnd.randrange("invalid")

    def test_shuffle(self):
        rnd1 = DeterministicRandom(42)
        rnd2 = DeterministicRandom(42)
        data1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        data2 = list(data1)

        rnd1.shuffle(data1)
        rnd2.shuffle(data2)
        self.assertEqual(data1, data2)
        self.assertNotEqual(data1, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        empty = []
        rnd1.shuffle(empty)
        self.assertEqual(empty, [])
        single = [42]
        rnd1.shuffle(single)
        self.assertEqual(single, [42])

    def test_sample(self):
        rnd1 = DeterministicRandom(42)
        rnd2 = DeterministicRandom(42)
        pop = list(range(100))

        s1 = rnd1.sample(pop, 10)
        s2 = rnd2.sample(pop, 10)
        self.assertEqual(s1, s2)
        self.assertEqual(len(s1), 10)
        self.assertEqual(len(set(s1)), 10)
        self.assertTrue(all(x in pop for x in s1))

        # Confirma que a população original não é alterada
        self.assertEqual(pop, list(range(100)))

        # Casos limite
        self.assertEqual(rnd1.sample(pop, 0), [])
        self.assertEqual(len(rnd1.sample(pop, 100)), 100)

        # Parâmetros k inválidos
        with self.assertRaises(ValueError):
            rnd1.sample(pop, -1)
        with self.assertRaises(ValueError):
            rnd1.sample(pop, 101)
        with self.assertRaises(ValueError):
            rnd1.sample(pop, "5")


if __name__ == "__main__":
    unittest.main()
