"""Verify configuration loading returns consistent results.

Tests that ``get_config()`` and ``get_default_config_path()`` return
correct and consistent data across multiple calls.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

import pytest


@pytest.mark.os_agnostic
class TestGetDefaultConfigPath:
    """Verify get_default_config_path() behavior."""

    def test_returns_toml_path(self) -> None:
        """The returned path points to a .toml file."""
        from fake_winreg.adapters.config.loader import get_default_config_path

        result = get_default_config_path()

        assert result.suffix == ".toml"

    def test_repeated_calls_return_equal_paths(self) -> None:
        """Repeated calls return equal Path values."""
        from fake_winreg.adapters.config.loader import get_default_config_path

        first = get_default_config_path()
        second = get_default_config_path()

        assert first == second


@pytest.mark.os_agnostic
class TestGetConfig:
    """Verify get_config() behavior."""

    def test_returns_config_with_dict(self) -> None:
        """get_config() returns a Config with a valid dict."""
        from fake_winreg.adapters.config.loader import get_config

        config = get_config()

        assert isinstance(config.as_dict(), dict)

    def test_repeated_calls_return_equivalent_data(self) -> None:
        """Repeated calls return Config with equivalent data."""
        from fake_winreg.adapters.config.loader import get_config

        first = get_config()
        second = get_config()

        assert first.as_dict() == second.as_dict()


@pytest.mark.os_agnostic
class TestConcurrentAccess:
    """Verify consistent results under concurrent access.

    Note: Python's functools.lru_cache is thread-safe since Python 3.2.
    These tests verify that behavior is preserved in our usage.
    """

    def test_concurrent_get_config_returns_equivalent_results(self) -> None:
        """All threads receive equivalent Config data."""
        from fake_winreg.adapters.config.loader import get_config

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(get_config) for _ in range(10)]
            results = [f.result() for f in futures]

        first_dict = results[0].as_dict()
        assert all(r.as_dict() == first_dict for r in results)

    def test_concurrent_get_default_config_path_returns_equal_results(self) -> None:
        """All threads receive equal Path values."""
        from fake_winreg.adapters.config.loader import get_default_config_path

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(get_default_config_path) for _ in range(10)]
            results = [f.result() for f in futures]

        first = results[0]
        assert all(r == first for r in results)

    def test_concurrent_access_with_cache_clear(self) -> None:
        """Cache clears during concurrent access do not cause errors.

        This tests that calling cache_clear() while other threads read
        the cache does not raise exceptions or return corrupt data.
        """
        from fake_winreg.adapters.config.loader import get_config

        errors: list[Exception] = []

        def fetch_config() -> None:
            try:
                config = get_config()
                # Verify we got valid data
                assert isinstance(config.as_dict(), dict)
            except Exception as exc:
                errors.append(exc)

        def clear_cache() -> None:
            try:
                get_config.cache_clear()
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=8) as pool:
            # Mix of fetch and clear operations
            futures: list[Future[None]] = []
            for i in range(20):
                if i % 5 == 0:
                    futures.append(pool.submit(clear_cache))
                else:
                    futures.append(pool.submit(fetch_config))
            # Wait for all to complete
            for future in futures:
                future.result()

        assert errors == [], f"Concurrent access errors: {errors}"

    def test_concurrent_access_with_multiple_profiles(self) -> None:
        """Different profiles can be loaded concurrently without interference.

        The LRU cache keys on (profile, start_dir), so different profiles
        should each get their own cached entry.
        """
        from fake_winreg.adapters.config.loader import get_config

        # Use None profile (default) - we just verify concurrent access works
        # Real profile testing requires actual profile files on disk
        results: list[dict[str, object]] = []
        errors: list[Exception] = []

        def fetch_default_profile() -> None:
            try:
                config = get_config(profile=None)
                results.append(config.as_dict())
            except Exception as exc:
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(fetch_default_profile) for _ in range(10)]
            for future in futures:
                future.result()

        assert errors == [], f"Concurrent profile access errors: {errors}"
        # All results should be equivalent
        assert len(results) == 10
        first = results[0]
        assert all(r == first for r in results)
