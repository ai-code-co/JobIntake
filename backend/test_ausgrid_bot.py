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
    "customerStreetName": "Wallaby Way",
    "customerLandTitleType": "Torrens",
    "customerStreetNumberRmb": "4",
    "customerType":"Retail Customer",
    "customerTitle":"Mr",
    "customerEmailAddress":"johndoe@gmail.com",
    "customerFirstName":"John",
    "customerLastName":"Doe",
    "customerPhoneNumber":"0412345679",
    
   
    # applicant -Fixed
    "applicantType":"Other on behalf of a Retail Customer or Real Estate Developer",
    "applicantTitle":"Mr",
    "applicantFirstName":"Eric",
    "applicantLastName":"Shen",
    "applicantEmailAddress":"info@sun-vault.com.au",
    "applicantSearchByABN/ACN":"30657429591",
    "applicantCompanyName":"Hexagon energy pty ltd",
    "applicantStreetName":"Denison Street",
    "applicantSuburb":"North Sydney",
    "applicantPostCode":"2060",
    "applicantPhoneNo":"0412345678",
    

    
    "selectService":"Alter Existing Connection",
    # "disconnected_nmi": "4102000001",
    # "disconnected_property_type": "Residential",
    # "new_connected_nmi": "4102000000012",
    # "new_property_type": "Residential",
    # "altering_remaining_permises": "No",
    # "premises_usage": "Residential",
    # "unit_shop_number": "1",
    # "loadNmiDisconnected": "4102000000",
    # "loadPropertyTypeDisconnected": "Residential",
    # "loadNmiRemaining": "4102000000012",
    # "loadPremisesUsage": "Residential",
    # "loadPropertyTypeRemaining": "Residential",
    # "loadUnitShopRemaining": "1",
    # "loadNumberOfPhases": "Single phase",
    # "loadPhaseA": "20",
    # "loadPhaseB": "0",
    # "loadPhaseC": "0",
    # "loadControlledLoad": "No",
    # "loadCouplingPoint": "Point of Attachment",
    # "loadAssetIdentifier": "Unknown",
    # "loadConnectionPoint": "Overhead service line",
    # "loadServiceLengthGreaterThan50m": "No",
    # "loadProposedServiceType": "Permanent",
    # "loadAlterExistingPremises": "No",
    # "loadAdditionalComments": "Automation test comment."
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
        "landZoning": "Urban",
        "streetNumberRmb": "50",
        "lotNumber": "",
        "lotDpNumber": "",
        "applicantType":"Retail Customer",
        "aspNumber": "ASP-654321",
        "aspLevel": "Level 2",
        "customerType": "Retail Customer",
        "title":"Mr",
        "firstName":"Chun",
        "lastName":"park",
        "email_address":"chun1@gmail.com",
        "phoneNo":"2193456789",
        "selectService":"Separation",
        "disconnected_nmi": "4102000000011",
        "disconnected_property_type": "House",
        "new_connected_nmi": "4102000000012",
        "new_property_type": "House",
        "altering_remaining_permises": "No",
        "premises_usage": "Residential",
        "unit_shop_number": "1",
        "loadNmiDisconnected": "4102000000011",
        "loadPropertyTypeDisconnected": "Residential",
        "loadNmiRemaining": "4102000000012",
        "loadPremisesUsage": "Residential",
        "loadPropertyTypeRemaining": "Residential",
        "loadUnitShopRemaining": "1",
        "loadNumberOfPhases": "Single phase",
        "loadPhaseA": "20",
        "loadPhaseB": "0",
        "loadPhaseC": "0",
        "loadControlledLoad": "No",
        "loadCouplingPoint": "Point of Attachment",
        "loadAssetIdentifier": "Unknown",
        "loadConnectionPoint": "Overhead service line",
        "loadServiceLengthGreaterThan50m": "No",
        "loadProposedServiceType": "Permanent",
        "loadAlterExistingPremises": "No",
        "loadAdditionalComments": "Automation test comment."
        
    }
    result = fill_location(minimal)
    assert isinstance(result, dict)
    assert "success" in result


if __name__ == "__main__":
    print("Running fill_location with sample data...")
    out = fill_location(SAMPLE_PAYLOAD)
    print(out)
    sys.exit(0 if out.get("success") else 1)
