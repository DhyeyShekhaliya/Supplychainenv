import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuel_env.disruptions import load_disruptions


def test_very_easy_has_no_disruptions():
    disruptions = load_disruptions("very_easy_startup")
    assert disruptions == []


def test_easy_has_expected_disruptions():
    disruptions = load_disruptions("easy_refinery_maintenance")
    assert len(disruptions) == 1
