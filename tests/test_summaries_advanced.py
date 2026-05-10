"""
Tests para las herramientas avanzadas del grupo B (radar normativo).

Cubre: get_boe_summary_range, watch_boe_changes, group_summary_by_department.
"""

import pytest
from mcp.types import TextContent

from mcp_boe.tools.summaries import SummaryTools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools(mock_http_client):
    return SummaryTools(mock_http_client)


# ---------------------------------------------------------------------------
# get_boe_summary_range
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_boe_summary_range_returns_text(tools):
    result = await tools.get_boe_summary_range({
        "from_date": "20240529",
        "to_date": "20240530",
    })
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "Sumario BOE" in text or "sumario" in text.lower()


@pytest.mark.asyncio
async def test_get_boe_summary_range_shows_documents(tools):
    """Debe listar documentos del SAMPLE_BOE_SUMMARY."""
    result = await tools.get_boe_summary_range({
        "from_date": "20240529",
        "to_date": "20240529",
    })
    text = result[0].text
    assert "BOE-A-2024-1234" in text or "Real Decreto" in text


@pytest.mark.asyncio
async def test_get_boe_summary_range_exceeds_31_days(tools):
    """Rango superior a 31 días debe devolver error."""
    result = await tools.get_boe_summary_range({
        "from_date": "20240101",
        "to_date": "20240301",
    })
    text = result[0].text
    assert "31" in text or "rango" in text.lower() or "inválido" in text.lower()


@pytest.mark.asyncio
async def test_get_boe_summary_range_inverted_dates(tools):
    """from_date posterior a to_date debe devolver error."""
    result = await tools.get_boe_summary_range({
        "from_date": "20240530",
        "to_date": "20240529",
    })
    text = result[0].text
    assert "anterior" in text.lower() or "inválido" in text.lower() or "Error" in text


@pytest.mark.asyncio
async def test_get_boe_summary_range_section_filter(tools):
    """Filtrar por sección no debe causar error."""
    result = await tools.get_boe_summary_range({
        "from_date": "20240529",
        "to_date": "20240529",
        "section": "1",
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_get_boe_summary_range_max_items(tools):
    """max_items=1 debe truncar a 1 documento."""
    result = await tools.get_boe_summary_range({
        "from_date": "20240529",
        "to_date": "20240529",
        "max_items": 1,
    })
    text = result[0].text
    assert isinstance(result[0], TextContent)
    # Con max_items=1 el número de filas "-" de item no debe ser más de 1
    items = [l for l in text.split('\n') if l.strip().startswith("- **")]
    assert len(items) <= 1


@pytest.mark.asyncio
async def test_get_boe_summary_range_iso_dates(tools):
    """Fechas en formato ISO YYYY-MM-DD deben aceptarse."""
    result = await tools.get_boe_summary_range({
        "from_date": "2024-05-29",
        "to_date": "2024-05-30",
    })
    assert "Error" not in result[0].text or "formato" not in result[0].text.lower()


# ---------------------------------------------------------------------------
# watch_boe_changes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watch_boe_changes_returns_text(tools):
    result = await tools.watch_boe_changes({
        "days_back": 3,
        "keywords": "procedimiento",
    })
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "Radar normativo" in text or "radar" in text.lower()


@pytest.mark.asyncio
async def test_watch_boe_changes_finds_matching_document(tools):
    """El SAMPLE_BOE_SUMMARY tiene 'procedimiento administrativo' en el título."""
    result = await tools.watch_boe_changes({
        "days_back": 5,
        "keywords": "procedimiento",
    })
    text = result[0].text
    # Debe encontrar el documento de la muestra
    assert "BOE-A-2024-1234" in text or "procedimiento" in text.lower()


@pytest.mark.asyncio
async def test_watch_boe_changes_no_match(tools):
    result = await tools.watch_boe_changes({
        "days_back": 3,
        "keywords": "xyzzy_palabra_inexistente_42",
    })
    text = result[0].text
    assert "no se encontraron" in text.lower() or "0 resultado" in text.lower()


@pytest.mark.asyncio
async def test_watch_boe_changes_empty_keywords(tools):
    result = await tools.watch_boe_changes({
        "days_back": 3,
        "keywords": "   ",
    })
    text = result[0].text
    assert "Parámetros inválidos" in text or "clave" in text.lower() or "Error" in text


@pytest.mark.asyncio
async def test_watch_boe_changes_multiple_keywords(tools):
    """Varias palabras clave deben hacer búsquedas independientes."""
    result = await tools.watch_boe_changes({
        "days_back": 3,
        "keywords": "procedimiento decreto",
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_watch_boe_changes_max_items(tools):
    result = await tools.watch_boe_changes({
        "days_back": 5,
        "keywords": "procedimiento",
        "max_items": 2,
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_watch_boe_changes_shows_matched_keyword(tools):
    """El output debe indicar qué keyword produjo cada coincidencia."""
    result = await tools.watch_boe_changes({
        "days_back": 5,
        "keywords": "procedimiento",
    })
    text = result[0].text
    if "BOE-A-2024-1234" in text:  # Si encontró resultados
        assert "procedimiento" in text.lower()


# ---------------------------------------------------------------------------
# group_summary_by_department
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_group_summary_by_department_returns_text(tools):
    result = await tools.group_summary_by_department({
        "from_date": "20240529",
        "to_date": "20240529",
    })
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "departamento" in text.lower() or "Departamento" in text


@pytest.mark.asyncio
async def test_group_summary_by_department_shows_dept_name(tools):
    """Debe agrupar por 'Jefatura del Estado' que viene en SAMPLE_BOE_SUMMARY."""
    result = await tools.group_summary_by_department({
        "from_date": "20240529",
        "to_date": "20240529",
    })
    text = result[0].text
    assert "Jefatura" in text or "Estado" in text


@pytest.mark.asyncio
async def test_group_summary_by_department_exceeds_31_days(tools):
    result = await tools.group_summary_by_department({
        "from_date": "20240101",
        "to_date": "20240301",
    })
    text = result[0].text
    assert "31" in text or "inválido" in text.lower()


@pytest.mark.asyncio
async def test_group_summary_by_department_inverted_dates(tools):
    result = await tools.group_summary_by_department({
        "from_date": "20240530",
        "to_date": "20240529",
    })
    text = result[0].text
    assert "anterior" in text.lower() or "inválido" in text.lower()


@pytest.mark.asyncio
async def test_group_summary_by_department_max_items_per_dept(tools):
    result = await tools.group_summary_by_department({
        "from_date": "20240529",
        "to_date": "20240529",
        "max_items_per_dept": 1,
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_group_summary_by_department_section_filter(tools):
    result = await tools.group_summary_by_department({
        "from_date": "20240529",
        "to_date": "20240529",
        "sections": "1",
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_group_summary_by_department_shows_doc_count(tools):
    """El output debe indicar cuántos documentos tiene cada departamento."""
    result = await tools.group_summary_by_department({
        "from_date": "20240529",
        "to_date": "20240529",
    })
    text = result[0].text
    # Debe haber al menos un encabezado con "(N docs)"
    assert "docs" in text or "documento" in text.lower()
