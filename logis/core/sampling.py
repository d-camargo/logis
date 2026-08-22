# -*- coding: utf-8 -*-
"""
/***************************************************************************
 logis
                                 A QGIS plugin
 Complemento do QGIS para apoiar projetos de logística no Brasil
                               -------------------
        begin                : 2026-08-22
        copyright            : (C) 2026 by Diego Camargo
        license              : GPL-3.0
 ***************************************************************************/
"""
"""Deterministic pseudo-random number generator module for the logis plugin.

This module provides `DeterministicRandom`, a pure-Python pseudo-random generator based
on the SplitMix64 algorithm.

IMPORTANT SAFETY NOTICE:
    This generator is strictly deterministic and NOT cryptographically secure.
    DO NOT use this class for security-sensitive operations such as secrets, tokens,
    keys, or passwords.

    It exists specifically because the package cannot import stdlib `random`
    (flagged as B311 by the security scanner on `plugins.qgis.org`, which ignores `# nosec`).
"""

DEFAULT_SEED = 42
MASK64 = 0xFFFFFFFFFFFFFFFF


class DeterministicRandom:
    """Deterministic pseudo-random number generator using the SplitMix64 algorithm.

    Provides deterministic implementation for `randrange`, `shuffle`, and `sample`
    without depending on the standard library `random` module.
    """

    def __init__(self, seed=None):
        """Initializes the generator with a seed value.

        Args:
            seed (int, optional): Initial seed. Defaults to DEFAULT_SEED (42) if None.
        """
        if seed is None:
            seed = DEFAULT_SEED
        self._state = int(seed) & MASK64

    def _next(self):
        """Generates the next 64-bit pseudo-random integer using SplitMix64.

        Returns:
            int: Unsigned 64-bit pseudo-random integer.
        """
        self._state = (self._state + 0x9E3779B97F4A7C15) & MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        return z ^ (z >> 31)

    def randrange(self, n):
        """Generates a pseudo-random integer in the range [0, n).

        Uses rejection sampling to eliminate modulo bias.

        Args:
            n (int): Exclusive upper bound. Must be strictly positive (> 0).

        Returns:
            int: Pseudo-random integer in range [0, n).

        Raises:
            ValueError: If n <= 0.
        """
        if not isinstance(n, int) or n <= 0:
            raise ValueError("n must be a strictly positive integer.")

        limit = (1 << 64) - ((1 << 64) % n)
        while True:
            val = self._next()
            if val < limit:
                return val % n

    def shuffle(self, seq):
        """Shuffles a sequence in-place using Fisher-Yates shuffle.

        Args:
            seq (list): Mutable sequence to shuffle in-place.
        """
        for i in range(len(seq) - 1, 0, -1):
            j = self.randrange(i + 1)
            seq[i], seq[j] = seq[j], seq[i]

    def sample(self, population, k):
        """Chooses k unique elements from a population sequence.

        Returns a new list containing sampled elements while leaving the original
        population unchanged.

        Args:
            population (sequence): Sequence of elements to sample from.
            k (int): Number of unique elements to sample.

        Returns:
            list: List of k sampled elements.

        Raises:
            ValueError: If k < 0 or k > len(population).
        """
        pop_copy = list(population)
        n = len(pop_copy)
        if not isinstance(k, int) or k < 0 or k > n:
            raise ValueError("k must be an integer satisfying 0 <= k <= len(population).")

        for i in range(k):
            j = i + self.randrange(n - i)
            pop_copy[i], pop_copy[j] = pop_copy[j], pop_copy[i]

        return pop_copy[:k]
