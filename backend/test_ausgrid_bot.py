"""
Test Ausgrid bot with sample data.

Run: pytest Backend/test_ausgrid_bot.py -v
Or:  python -m pytest Backend/test_ausgrid_bot.py -v
Or:  python Backend/test_ausgrid_bot.py (runs fill_location and prints result)
"""

import os
import sys

# Ensure Backend is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ausgrid_bot import fill_location

SAMPLE_PAYLOAD = {
    "streetAddress": "100 George Street",
    "suburb": "Wollongong",
    "postcode": "2500",
    "landTitleType": "Torrens Title",
    "landZoning": "Residential",
    "streetNumberRmb": "100",
    "lotNumber": "",
    "lotDpNumber": "",
    "nmi": "",
    "propertyName": "",
    "electricityRetailer": "",
    "propertyType": "Residential",
    "unitNumber": "",
}


def test_fill_location_returns_dict():
    """fill_location returns a dict with success and message keys."""
    result = fill_location(SAMPLE_PAYLOAD)
    assert isinstance(result, dict)
    assert "success" in result
    assert "message" in result


def test_fill_location_with_minimal_data():
    """fill_location accepts minimal required keys (at least one of street number/lot/lot-dp)."""
    minimal = {
        "streetAddress": "50 Crown St",
        "suburb": "Wollongong",
        "postcode": "2500",
        "landTitleType": "Torrens Title",
        "landZoning": "Residential",
        "streetNumberRmb": "50",
        "lotNumber": "",
        "lotDpNumber": "",
    }
    result = fill_location(minimal)
    assert isinstance(result, dict)
    assert "success" in result


if __name__ == "__main__":
    print("Running fill_location with sample data...")
    out = fill_location(SAMPLE_PAYLOAD)
    print(out)
    sys.exit(0 if out.get("success") else 1)
