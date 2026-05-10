"""
Tests para las herramientas avanzadas del grupo A (legislación).

Cubre: compare_law_versions, search_law_articles, get_law_metadata,
       list_related_laws.
"""

import pytest
from mcp.types import TextContent

from mcp_boe.tools.legislation import LegislationTools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools(mock_http_client):
    return LegislationTools(mock_http_client)


# ---------------------------------------------------------------------------
# compare_law_versions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compare_law_versions_no_changes(tools):
    """Cuando from_date y to_date caen en la misma versión debe indicar sin cambios."""
    result = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-10566",
        "from_date": "20151002",
        "to_date": "20151103",
    })
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "BOE-A-2015-10566" in text


@pytest.mark.asyncio
async def test_compare_law_versions_detects_modification(tools):
    """Cuando hay versiones distintas entre fechas debe detectar modificados."""
    result = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-10566",
        "from_date": "20151002",
        "to_date": "20210101",
    })
    text = result[0].text
    # El artículo a1 tiene dos versiones en SAMPLE_LAW_TEXTO con fechas distintas
    assert "modificado" in text.lower() or "Modificado" in text or "modificados" in text.lower()


@pytest.mark.asyncio
async def test_compare_law_versions_invalid_id(tools):
    result = await tools.compare_law_versions({
        "law_id": "INVALID",
        "from_date": "20200101",
        "to_date": "20210101",
    })
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


@pytest.mark.asyncio
async def test_compare_law_versions_from_date_after_to_date(tools):
    result = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-10566",
        "from_date": "20220101",
        "to_date": "20200101",
    })
    assert "Error" in result[0].text or "anterior" in result[0].text.lower()


@pytest.mark.asyncio
async def test_compare_law_versions_iso_date_format(tools):
    """Las fechas en formato ISO YYYY-MM-DD deben aceptarse."""
    result = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-10566",
        "from_date": "2015-10-02",
        "to_date": "2021-01-01",
    })
    # No debe devolver error de formato
    assert "Error" not in result[0].text or "formato" not in result[0].text.lower()


@pytest.mark.asyncio
async def test_compare_law_versions_granularity_articulo(tools):
    result = await tools.compare_law_versions({
        "law_id": "BOE-A-2015-10566",
        "from_date": "20151002",
        "to_date": "20210101",
        "granularity": "articulo",
    })
    assert isinstance(result[0], TextContent)


# ---------------------------------------------------------------------------
# search_law_articles
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_law_articles_finds_match(tools):
    """Buscar 'objeto' en la muestra debe encontrar el artículo 1."""
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "objeto",
    })
    text = result[0].text
    assert "a1" in text or "Artículo 1" in text


@pytest.mark.asyncio
async def test_search_law_articles_no_match(tools):
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "xyzzy_inexistente_42",
    })
    text = result[0].text
    assert "no se encontraron" in text.lower() or "0 artículo" in text.lower()


@pytest.mark.asyncio
async def test_search_law_articles_search_in_titulo(tools):
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "Objeto",
        "search_in": "titulo",
    })
    assert isinstance(result[0], TextContent)
    # Artículo 1 tiene "Objeto" en el título
    assert "a1" in result[0].text or "Artículo 1" in result[0].text


@pytest.mark.asyncio
async def test_search_law_articles_search_in_texto(tools):
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "sector público",
        "search_in": "texto",
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_search_law_articles_invalid_id(tools):
    result = await tools.search_law_articles({
        "law_id": "NO-VALID",
        "query": "objeto",
    })
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


@pytest.mark.asyncio
async def test_search_law_articles_empty_query(tools):
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "   ",
    })
    assert "Error" in result[0].text or "vacío" in result[0].text.lower()


@pytest.mark.asyncio
async def test_search_law_articles_limit(tools):
    """Con limit=1 debe devolver como máximo 1 artículo."""
    result = await tools.search_law_articles({
        "law_id": "BOE-A-2015-10566",
        "query": "esta ley",
        "limit": 1,
    })
    text = result[0].text
    assert isinstance(result[0], TextContent)
    # No debe listar más de 1 resultado de artículo
    article_headers = [line for line in text.split('\n') if line.startswith('###')]
    assert len(article_headers) <= 1


# ---------------------------------------------------------------------------
# get_law_metadata
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_law_metadata_returns_title(tools):
    result = await tools.get_law_metadata({"law_id": "BOE-A-2015-10566"})
    assert len(result) == 1
    text = result[0].text
    assert "BOE-A-2015-10566" in text
    assert "Ley" in text or "Régimen" in text


@pytest.mark.asyncio
async def test_get_law_metadata_shows_publication_date(tools):
    result = await tools.get_law_metadata({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # Fecha de publicación 20151002 → debe aparecer en algún formato
    assert "2015" in text


@pytest.mark.asyncio
async def test_get_law_metadata_shows_department(tools):
    result = await tools.get_law_metadata({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    assert "Jefatura" in text or "Estado" in text


@pytest.mark.asyncio
async def test_get_law_metadata_shows_legal_range(tools):
    result = await tools.get_law_metadata({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    assert "Ley" in text


@pytest.mark.asyncio
async def test_get_law_metadata_invalid_id(tools):
    result = await tools.get_law_metadata({"law_id": "BAD-ID"})
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text


# ---------------------------------------------------------------------------
# list_related_laws
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_related_laws_returns_text(tools):
    result = await tools.list_related_laws({"law_id": "BOE-A-2015-10566"})
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    text = result[0].text
    assert "BOE-A-2015-10566" in text


@pytest.mark.asyncio
async def test_list_related_laws_shows_references(tools):
    """Debe mostrar las referencias anteriores y posteriores de la muestra."""
    result = await tools.list_related_laws({"law_id": "BOE-A-2015-10566"})
    text = result[0].text
    # SAMPLE_LAW_ANALYSIS tiene referencias anteriores y posteriores
    assert "BOE-A-1992-26318" in text or "BOE-A-2020-3824" in text


@pytest.mark.asyncio
async def test_list_related_laws_only_derogating(tools):
    result = await tools.list_related_laws({
        "law_id": "BOE-A-2015-10566",
        "include_derogating": True,
        "include_development": False,
        "include_references": False,
    })
    assert isinstance(result[0], TextContent)


@pytest.mark.asyncio
async def test_list_related_laws_none_included(tools):
    """Con todos los flags en False no debe mostrar relaciones."""
    result = await tools.list_related_laws({
        "law_id": "BOE-A-2015-10566",
        "include_derogating": False,
        "include_development": False,
        "include_references": False,
    })
    text = result[0].text
    # Debe indicar que no hay relaciones visibles
    assert "no se encontraron" in text.lower() or "0 relación" in text.lower() or "No se encontraron" in text


@pytest.mark.asyncio
async def test_list_related_laws_invalid_id(tools):
    result = await tools.list_related_laws({"law_id": "NOT-A-LAW"})
    assert "inválido" in result[0].text.lower() or "Error" in result[0].text
