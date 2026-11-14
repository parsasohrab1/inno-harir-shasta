from app.reference_data import get_reference_data_catalog


def test_reference_catalog_marks_sources_external_and_not_plant_data():
    catalog = get_reference_data_catalog()
    assert catalog["plant_data_included"] is False
    assert catalog["plc_write_enabled"] is False
    assert catalog["items"]
    assert all(item["provenance_class"] == "external_reference" for item in catalog["items"])
    assert all("limitations" in item for item in catalog["items"])
