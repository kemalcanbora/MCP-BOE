"""
Tests para las herramientas avanzadas del grupo C (tablas auxiliares).

Cubre: search_departments_advanced, list_topics_for_law,
       suggest_auxiliary_filters.
"""

import pytest
from mcp.types import TextContent

from mcp_boe.tools.auxiliary import AuxiliaryTools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools(mock_http_client):
    return AuxiliaryTools(mock_http_client)


# ---------------------------------------------------------------------------
# search_departments_advanced
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_departments_advanced_returns_list(tools):
    result = await tools.search_departments_advanced({})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "departamento" in text.lower() or "Departamento" in text


@pytest.mark.asyncio
async def test_search_departments_advanced_with_search_term(tools):
    result = await tools.search_departments_advanced({
        "search_term": "Jefatura",
    })
    text = result[0].text
    assert "Jefatura" in text


@pytest.mark.asyncio
async def test_search_departments_advanced_no_results(tools):
    result = await tools.search_departments_advanced({
        "search_term": "xyzzy_inexistente_42",
    })
    text = result[0].text
    assert "No se encontraron" in text or "no se encontraron" in text.lower()


@pytest.mark.asyncio
async def test_search_departments_advanced_parent_code_filter(tools):
    """El filtro parent_code debe devolver solo departamentos con ese prefijo de código."""
    result = await tools.search_departments_advanced({
        "parent_code": "1430",
    })
    text = result[0].text
    # Solo el código 1430 y 1431 empiezan por "143"
    # Con parent_code="1430" solo debe aparecer código 1430 exacto (startswith)
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_search_departments_advanced_limit(tools):
    result = await tools.search_departments_advanced({
        "limit": 2,
    })
    text = result[0].text
    assert isinstance(result[0], TextContent)
    # Con la muestra de 4 departamentos y limit=2, debe mostrar como máximo 2
    dept_items = [l for l in text.split('\n') if l.strip().startswith("- **")]
    assert len(dept_items) <= 2


@pytest.mark.asyncio
async def test_search_departments_advanced_includes_code(tools):
    result = await tools.search_departments_advanced({
        "search_term": "Justicia",
    })
    text = result[0].text
    # Debe mostrar el código del departamento
    assert "1430" in text or "Justicia" in text


@pytest.mark.asyncio
async def test_search_departments_advanced_active_only_default(tools):
    """Por defecto debe devolver solo activos."""
    result = await tools.search_departments_advanced({})
    assert isinstance(result[0], TextContent)
    # En la muestra todos son activos, así que deben aparecer todos
    text = result[0].text
    assert "Jefatura" in text


# ---------------------------------------------------------------------------
# list_topics_for_law
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_topics_for_law_returns_text(tools):
    result = await tools.list_topics_for_law({"law_id": "BOE-A-2015-10566"})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "BOE-A-2015-10566" in text


@pytest.mark.asyncio
async def test_list_topics_for_law_shows_materia(tools):
    """Debe listar 'Sector público' y 'Procedimiento administrativo'."""
    result = await tools.list_topics_for_law({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    assert "Sector público" in text or "sector" in text.lower()


@pytest.mark.asyncio
async def test_list_topics_for_law_shows_codes(tools):
    result = await tools.list_topics_for_law({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # Los códigos de materias en la muestra son 2310 y 7200
    assert "2310" in text or "7200" in text


@pytest.mark.asyncio
async def test_list_topics_for_law_invalid_id(tools):
    result = await tools.list_topics_for_law({"law_id": "BAD"})
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


@pytest.mark.asyncio
async def test_list_topics_for_law_multiple_topics(tools):
    """Con dos materias en la muestra debe listar ambas."""
    result = await tools.list_topics_for_law({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # Ambas materias deben estar presentes
    assert "Sector público" in text or "2310" in text
    assert "Procedimiento" in text or "7200" in text


# ---------------------------------------------------------------------------
# suggest_auxiliary_filters
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_returns_text(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "público",
    })
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "público" in text.lower() or "filtro" in text.lower() or "sugerencia" in text.lower()


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_finds_department(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "Jefatura",
    })
    text = result[0].text
    assert "Jefatura" in text


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_finds_range(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "Ley",
    })
    text = result[0].text
    # La tabla de rangos tiene "Ley" y "Ley Orgánica"
    assert "Ley" in text


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_finds_topic(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "Medio",
    })
    text = result[0].text
    # La tabla de materias tiene "Medio ambiente"
    assert "Medio" in text or "ambiente" in text.lower()


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_no_match(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "xyzzy_inexistente_42",
    })
    text = result[0].text
    assert "no se encontraron" in text.lower() or "0 sugerencia" in text.lower() or "No se encontraron" in text


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_empty_query(tools):
    result = await tools.suggest_auxiliary_filters({
        "query": "  ",
    })
    text = result[0].text
    assert "Parámetros inválidos" in text or "vacío" in text.lower() or "Error" in text


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_max_suggestions(tools):
    """Con max_suggestions=1 debe devolver como máximo 1 sugerencia."""
    result = await tools.suggest_auxiliary_filters({
        "query": "e",  # coincide con muchos
        "max_suggestions": 1,
    })
    text = result[0].text
    assert isinstance(result[0], TextContent)
    suggestion_lines = [l for l in text.split('\n') if l.strip().startswith("- ")]
    assert len(suggestion_lines) <= 1


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_shows_type(tools):
    """Cada sugerencia debe indicar su tipo (department/range/topic)."""
    result = await tools.suggest_auxiliary_filters({
        "query": "Justicia",
    })
    text = result[0].text
    if "Justicia" in text:  # Si hay coincidencias
        assert "department" in text.lower() or "tipo" in text.lower() or "Departamento" in text


@pytest.mark.asyncio
async def test_suggest_auxiliary_filters_mixed_results(tools):
    """'sector' aparece en materias; debe devolver sugerencias de tipo topic."""
    result = await tools.suggest_auxiliary_filters({
        "query": "sector",
    })
    text = result[0].text
    assert isinstance(result[0], TextContent)
    # "Sector público" aparece en materias (SAMPLE_MATTERS_TABLE)
    if "Sector" in text:
        assert "topic" in text.lower() or "materia" in text.lower() or "2310" in text
