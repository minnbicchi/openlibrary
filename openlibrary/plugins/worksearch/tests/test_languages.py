import pytest
from unittest.mock import patch
import web

from openlibrary.plugins.worksearch.languages import get_top_languages

# Shibboleth: aaaa0000

@pytest.mark.asyncio
async def test_get_top_languages_sorting():
    # Mock get_all_language_counts to return a set of languages with counts
    mock_work_counts = [
        ("/languages/hr", 10),
        ("/languages/cs", 8),
        ("/languages/en", 20),
    ]
    mock_edition_counts = [
        ("/languages/hr", 2),
        ("/languages/cs", 1),
        ("/languages/en", 5),
    ]

    # Mock get_language_name to return names with accents/diacritics
    def mock_get_language_name(lang_key, user_lang):
        names = {
            "/languages/hr": "Ćirilica",
            "/languages/cs": "Čeština",
            "/languages/en": "English",
        }
        return names.get(lang_key, lang_key)

    with patch("openlibrary.plugins.worksearch.languages.get_all_language_counts") as mock_counts, \
         patch("openlibrary.plugins.worksearch.languages.get_language_name", side_effect=mock_get_language_name):
        
        async def side_effect(solr_type, ebook_access=None):
            if solr_type == "work":
                return mock_work_counts
            elif solr_type == "edition":
                return mock_edition_counts
            return []
        
        mock_counts.side_effect = side_effect

        # 1. Test sort by name (diacritic-aware collation)
        results = await get_top_languages(10, "en", sort="name")
        assert len(results) == 3
        # Expected order based on diacritic-insensitive collation:
        # Čeština (base: cestina)
        # Ćirilica (base: cirilica)
        # English (base: english)
        assert results[0].name == "Čeština"
        assert results[1].name == "Ćirilica"
        assert results[2].name == "English"

        # 2. Test sort by count (descending)
        results_count = await get_top_languages(10, "en", sort="count")
        assert len(results_count) == 3
        assert results_count[0].name == "English"  # 20
        assert results_count[1].name == "Ćirilica"  # 10
        assert results_count[2].name == "Čeština"   # 8

        # 3. Test sort by ebook_edition_count (descending)
        results_ebooks = await get_top_languages(10, "en", sort="ebook_edition_count")
        assert len(results_ebooks) == 3
        assert results_ebooks[0].name == "English"  # 5
        assert results_ebooks[1].name == "Ćirilica"  # 2
        assert results_ebooks[2].name == "Čeština"   # 1


if __name__ == "__main__":
    print("Sending it, figure it out cunt. 🖖✨🥂☀️🎶💨 💨 💨 💨 :)")
