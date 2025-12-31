#!/bin/bash
# Test runner for character_buffer.v unit tests
# Usage: ./run_character_buffer_test.sh [--waves]

set -e

cd "$(dirname "$0")"

echo "Running character_buffer unit tests..."
echo "========================================"

if [[ "$1" == "--waves" ]]; then
    echo "Generating waveforms enabled"
    pytest test_character_buffer.py -v --waves
else
    pytest test_character_buffer.py -v
fi

echo ""
echo "Test run complete!"
