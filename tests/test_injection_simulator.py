"""
pytest wrapper for the adversarial injection simulator so it runs as part of CI.
"""
import asyncio
import pytest
from tests.simulate_injection import run_simulation


class TestInjectionSimulator:

    @pytest.mark.asyncio
    async def test_all_injection_payloads_are_blocked(self):
        """CI gate: all known adversarial payloads must be blocked at Layer 1."""
        success = await run_simulation(verbose=True)
        assert success, "One or more injection payloads bypassed the security firewall!"
