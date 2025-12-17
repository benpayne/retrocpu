"""
pytest configuration for RetroCPU unit tests
"""

import pytest
import os


def pytest_addoption(parser):
    """Add custom command-line options"""
    parser.addoption(
        "--waves",
        action="store_true",
        default=False,
        help="Generate waveform files (.vcd) for debugging"
    )


@pytest.fixture(scope="session")
def waves(request):
    """Fixture to check if waveforms should be generated"""
    return request.config.getoption("--waves")


@pytest.fixture(autouse=True)
def setup_waves(request, waves):
    """Automatically set WAVES environment variable for cocotb"""
    if waves:
        os.environ["WAVES"] = "1"
    else:
        os.environ.pop("WAVES", None)
