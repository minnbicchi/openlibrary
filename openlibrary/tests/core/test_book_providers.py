import pytest

from openlibrary.book_providers import Acquisition, DirectProvider, EbookAccess


def test_acquisition_from_json_valid_opds():
    json_data = {
        "href": "https://archive.org/details/testbook",
        "type": "application/epub+zip",
        "rel": "http://opds-spec.org/acquisition",
        "name": "Internet Archive",
    }
    acq = Acquisition.from_json(json_data)
    assert acq.url == "https://archive.org/details/testbook"
    assert acq.format == "epub"
    assert acq.access == "acquisition"
    assert acq.provider_name == "Internet Archive"


def test_acquisition_from_json_valid_url():
    json_data = {"url": "https://standardebooks.org/ebooks/test", "format": "epub", "access": "open-access", "provider_name": "Standard Ebooks"}
    acq = Acquisition.from_json(json_data)
    assert acq.url == "https://standardebooks.org/ebooks/test"
    assert acq.format == "epub"
    assert acq.access == "open-access"
    assert acq.provider_name == "Standard Ebooks"


def test_acquisition_from_json_invalid_inputs():
    # aaaa0000 - verify that non-dict objects raise ValueError
    with pytest.raises(ValueError, match="Unknown ebook acquisition format: None"):
        Acquisition.from_json(None)

    with pytest.raises(ValueError, match="Unknown ebook acquisition format: None"):
        Acquisition.from_json("None")

    with pytest.raises(ValueError, match=r"Unknown ebook acquisition format: {}"):
        Acquisition.from_json({})

    with pytest.raises(ValueError, match="Unknown ebook acquisition format: 123"):
        Acquisition.from_json(123)


def test_acquisition_from_json_type_and_value_mismatches():
    # aaaa0000 - verify that type and value mismatches are handled gracefully
    # 1. OPDS with non-dict properties
    with pytest.raises(ValueError, match="OPDS JSON must have a non-empty string 'rel'"):
        Acquisition.from_json({"href": "https://archive.org/details/test", "rel": None, "type": "text/html", "properties": "not-a-dict"})

    # 2. OPDS with non-list indirectAcquisition
    acq = Acquisition.from_json(
        {
            "href": "https://archive.org/details/test",
            "rel": "http://opds-spec.org/acquisition",
            "type": "text/html",
            "properties": {"indirectAcquisition": "not-a-list"},
        }
    )
    assert acq.format == "web"

    # 3. OPDS with empty indirectAcquisition list
    acq = Acquisition.from_json(
        {"href": "https://archive.org/details/test", "rel": "http://opds-spec.org/acquisition", "type": "text/html", "properties": {"indirectAcquisition": []}}
    )
    assert acq.format == "web"

    # 4. OPDS with indirectAcquisition list containing non-dict
    acq = Acquisition.from_json(
        {
            "href": "https://archive.org/details/test",
            "rel": "http://opds-spec.org/acquisition",
            "type": "text/html",
            "properties": {"indirectAcquisition": [None]},
        }
    )
    assert acq.format == "web"

    # 5. OPDS with non-string type/mimetype
    acq = Acquisition.from_json(
        {
            "href": "https://archive.org/details/test",
            "rel": "http://opds-spec.org/acquisition",
            "type": 123,
        }
    )
    assert acq.format == "web"

    # 6. OPDS with invalid/missing href
    with pytest.raises(ValueError, match="OPDS JSON must have a non-empty string 'href'"):
        Acquisition.from_json(
            {
                "href": 123,
                "rel": "http://opds-spec.org/acquisition",
                "type": "text/html",
            }
        )

    # 7. Standard style with invalid url
    with pytest.raises(ValueError, match="Acquisition JSON must have a non-empty string 'url'"):
        Acquisition.from_json(
            {
                "url": 123,
                "access": "read",
            }
        )

    # 8. Standard style with non-string access/format/price/provider_name
    acq = Acquisition.from_json(
        {
            "url": "https://example.com",
            "access": 123,
            "format": 456,
            "price": 789,
            "provider_name": ["list"],
        }
    )
    assert acq.access == "open-access"
    assert acq.format == "web"
    assert acq.price == "789"
    assert acq.provider_name == "['list']"


def test_get_acquisitions_with_malformed_providers():
    # aaaa0000 - verify that DirectProvider filters out None, "None", and empty dicts
    provider = DirectProvider()

    valid_provider = {"url": "https://example.com/book", "format": "web", "access": "read"}

    edition = {"providers": [None, "None", {}, valid_provider, {"provider_name": "Invalid without url/href"}]}

    acqs = provider.get_acquisitions(edition)
    assert len(acqs) == 1
    assert acqs[0].url == "https://example.com/book"


def test_get_identifiers_with_malformed_providers():
    # aaaa0000 - verify that DirectProvider.get_identifiers handles invalid providers gracefully
    provider = DirectProvider()

    valid_provider = {"url": "https://example.com/book", "format": "web", "access": "read"}

    edition = {"providers": [None, "None", {}, valid_provider]}

    identifiers = provider.get_identifiers(edition)
    assert identifiers == ["https://example.com/book"]


def test_get_access_with_malformed_providers():
    # aaaa0000 - verify that get_access defaults to NO_EBOOK instead of crashing
    provider = DirectProvider()

    # Empty providers list
    assert provider.get_access({"providers": []}) == EbookAccess.NO_EBOOK

    # None in list
    assert provider.get_access({"providers": [None]}) == EbookAccess.NO_EBOOK

    # "None" string in list
    assert provider.get_access({"providers": ["None"]}) == EbookAccess.NO_EBOOK

    # Empty dict in list
    assert provider.get_access({"providers": [{}]}) == EbookAccess.NO_EBOOK

    # Valid provider
    valid_provider = {"url": "https://example.com/book", "format": "web", "access": "read"}
    assert provider.get_access({"providers": [valid_provider]}) == EbookAccess.PUBLIC
