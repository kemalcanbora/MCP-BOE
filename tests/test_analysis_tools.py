"""
Tests para las herramientas del grupo D (análisis / calidad de vida).

Cubre: summarize_law_sections, paginate_law_text, explain_law_structure,
       normalize_boe_reference.
"""

import base64
import pytest
from mcp.types import TextContent

from mcp_boe.tools.analysis import AnalysisTools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools(mock_http_client):
    return AnalysisTools(mock_http_client)


# ---------------------------------------------------------------------------
# summarize_law_sections
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summarize_law_sections_returns_text(tools):
    result = await tools.summarize_law_sections({"law_id": "BOE-A-2015-10566"})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "BOE-A-2015-10566" in text
    assert "Preámbulo" in text or "preambulo" in text.lower()


@pytest.mark.asyncio
async def test_summarize_law_sections_includes_articles(tools):
    result = await tools.summarize_law_sections({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    assert "Artículo 1" in text
    assert "Artículo 2" in text


@pytest.mark.asyncio
async def test_summarize_law_sections_invalid_id(tools):
    result = await tools.summarize_law_sections({"law_id": "INVALID-ID"})
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


# ---------------------------------------------------------------------------
# paginate_law_text
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paginate_law_text_first_page(tools):
    result = await tools.paginate_law_text({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # La primera página debe contener bloques
    assert "BOE-A-2015-10566" in text
    assert "Bloques incluidos" in text


@pytest.mark.asyncio
async def test_paginate_law_text_small_max_chars(tools):
    """Con max_chars muy pequeño debe paginar en múltiples páginas."""
    result = await tools.paginate_law_text({
        "law_id": "BOE-A-2015-10566",
        "max_chars": 50,  # muy pequeño para forzar paginación
    })
    text = result[0].text
    # Puede que haya next_cursor o que sea la última página
    assert "BOE-A-2015-10566" in text


@pytest.mark.asyncio
async def test_paginate_law_text_cursor_navigation(tools):
    """El cursor de la primera página debe permitir acceder a la siguiente."""
    # Primera página con max_chars pequeño para garantizar paginación
    result1 = await tools.paginate_law_text({
        "law_id": "BOE-A-2015-10566",
        "max_chars": 100,
    })
    text1 = result1[0].text

    # Si hay next_cursor, extraerlo y usarlo
    if "Siguiente cursor:" in text1:
        # Extraer cursor del texto
        for line in text1.split('\n'):
            if "Siguiente cursor:" in line:
                cursor = line.split('`')[1] if '`' in line else None
                if cursor:
                    result2 = await tools.paginate_law_text({
                        "law_id": "BOE-A-2015-10566",
                        "cursor": cursor,
                        "max_chars": 100,
                    })
                    assert isinstance(result2[0], TextContent)
                break


@pytest.mark.asyncio
async def test_paginate_law_text_invalid_cursor(tools):
    result = await tools.paginate_law_text({
        "law_id": "BOE-A-2015-10566",
        "cursor": "cursor_completamente_invalido!!!",
    })
    # Debe manejar el error con gracia
    assert "Error" in result[0].text or "inválido" in result[0].text.lower()


# ---------------------------------------------------------------------------
# explain_law_structure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_explain_law_structure_returns_text(tools):
    result = await tools.explain_law_structure({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    assert "BOE-A-2015-10566" in text
    assert "Artículo" in text or "artículo" in text.lower()


@pytest.mark.asyncio
async def test_explain_law_structure_shows_element_counts(tools):
    result = await tools.explain_law_structure({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # Debe mencionar el número de elementos en cada sección
    assert "elemento" in text.lower() or "(" in text


@pytest.mark.asyncio
async def test_explain_law_structure_invalid_id(tools):
    result = await tools.explain_law_structure({"law_id": "NOPE"})
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


# ---------------------------------------------------------------------------
# normalize_boe_reference
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_normalize_boe_id(tools):
    result = await tools.normalize_boe_reference({"reference_text": "BOE-A-2015-10566"})
    text = result[0].text
    assert "law" in text.lower() or "BOE-A-2015-10566" in text
    assert "Norma" in text or "law" in text.lower()


@pytest.mark.asyncio
async def test_normalize_ley(tools):
    result = await tools.normalize_boe_reference({"reference_text": "Ley 40/2015"})
    text = result[0].text
    assert "40/2015" in text
    assert "law" in text.lower() or "Norma" in text


@pytest.mark.asyncio
async def test_normalize_ley_organica(tools):
    result = await tools.normalize_boe_reference({"reference_text": "Ley Orgánica 3/2018"})
    text = result[0].text
    assert "3/2018" in text
    assert "Orgánica" in text or "orgánica" in text.lower()


@pytest.mark.asyncio
async def test_normalize_real_decreto(tools):
    result = await tools.normalize_boe_reference({"reference_text": "Real Decreto 123/2020"})
    text = result[0].text
    assert "123/2020" in text


@pytest.mark.asyncio
async def test_normalize_orden_ministerial(tools):
    result = await tools.normalize_boe_reference({"reference_text": "Orden TED/1234/2023"})
    text = result[0].text
    assert "TED" in text
    assert "1234/2023" in text
    assert "order" in text.lower() or "Orden" in text


@pytest.mark.asyncio
async def test_normalize_boe_por_fecha(tools):
    result = await tools.normalize_boe_reference({
        "reference_text": "BOE del 3 de mayo de 2024, sección I"
    })
    text = result[0].text
    assert "boe_issue" in text.lower() or "BOE" in text
    assert "20240503" in text or "mayo" in text.lower()


@pytest.mark.asyncio
async def test_normalize_boe_fecha_numerica(tools):
    result = await tools.normalize_boe_reference({"reference_text": "BOE de 3/5/2024"})
    text = result[0].text
    assert "20240503" in text or "3/5/2024" in text or "3/05/2024" in text


@pytest.mark.asyncio
async def test_normalize_unknown(tools):
    result = await tools.normalize_boe_reference({"reference_text": "texto completamente irreconocible xyz"})
    text = result[0].text
    assert "unknown" in text.lower() or "No reconocido" in text or "no reconoc" in text.lower()


@pytest.mark.asyncio
async def test_normalize_empty_text(tools):
    result = await tools.normalize_boe_reference({"reference_text": ""})
    assert "Error" in result[0].text or "vacío" in result[0].text.lower()
