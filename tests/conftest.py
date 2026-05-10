"""
Fixtures compartidos para los tests del servidor MCP-BOE.

Usa unittest.mock para simular las llamadas HTTP al BOE, de modo que
los tests sean reproducibles y no dependan de la conectividad real.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Respuestas JSON de ejemplo que simulan la API del BOE
# ---------------------------------------------------------------------------

SAMPLE_LAW_METADATA = {
    "data": {
        "fecha_actualizacion": "2023-10-09T12:23:33Z",
        "identificador": "BOE-A-2015-10566",
        "titulo": "Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público.",
        "fecha_publicacion": "20151002",
        "fecha_vigencia": "20151103",
        "fecha_derogacion": None,
        "estatus_derogacion": "N",
        "estatus_anulacion": "N",
        "vigencia_agotada": "N",
        "numero_oficial": "40/2015",
        "diario": "BOE",
        "diario_numero": "236",
        "fecha_disposicion": "20151001",
        "departamento": {"codigo": "7723", "texto": "Jefatura del Estado"},
        "rango": {"codigo": "1300", "texto": "Ley"},
        "ambito": {"codigo": "1", "texto": "Estatal"},
        "estado_consolidacion": {"codigo": "1", "texto": "Finalizado"},
        "url_eli": "https://www.boe.es/eli/es/l/2015/10/01/40",
        "url_html_consolidada": "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10566",
    }
}

SAMPLE_LAW_ANALYSIS = {
    "data": {
        "materias": [
            {"codigo": "2310", "texto": "Sector público"},
            {"codigo": "7200", "texto": "Procedimiento administrativo"},
        ],
        "notas": [],
        "referencias": {
            "anteriores": [
                {
                    "id_norma": "BOE-A-1992-26318",
                    "relacion": {"codigo": "1", "texto": "DEROGA"},
                    "texto": "Ley 30/1992, de 26 de noviembre, de Régimen Jurídico..."
                }
            ],
            "posteriores": [
                {
                    "id_norma": "BOE-A-2020-3824",
                    "relacion": {"codigo": "2", "texto": "MODIFICA"},
                    "texto": "Real Decreto-ley 11/2020, de 31 de marzo..."
                }
            ],
        }
    }
}

SAMPLE_LAW_TEXTO = {
    "data": {
        "texto": [
            {
                "id": "pr",
                "tipo": "preambulo",
                "titulo": "Preámbulo",
                "versiones": [
                    {
                        "fecha_publicacion": "20151002",
                        "fecha_vigencia": "20151103",
                        "id_norma": "BOE-A-2015-10566",
                        "contenido_html": "<p>Esta Ley tiene por objeto regular el régimen jurídico.</p>"
                    }
                ]
            },
            {
                "id": "a1",
                "tipo": "precepto",
                "titulo": "Artículo 1. Objeto.",
                "versiones": [
                    {
                        "fecha_publicacion": "20200101",
                        "fecha_vigencia": "20200201",
                        "id_norma": "BOE-A-2020-3824",
                        "contenido_html": "<p>Esta Ley tiene por objeto establecer y regular los principios.</p>"
                    },
                    {
                        "fecha_publicacion": "20151002",
                        "fecha_vigencia": "20151103",
                        "id_norma": "BOE-A-2015-10566",
                        "contenido_html": "<p>Esta Ley tiene por objeto regular el régimen jurídico del sector público.</p>"
                    }
                ]
            },
            {
                "id": "a2",
                "tipo": "precepto",
                "titulo": "Artículo 2. Ámbito subjetivo.",
                "versiones": [
                    {
                        "fecha_publicacion": "20151002",
                        "fecha_vigencia": "20151103",
                        "id_norma": "BOE-A-2015-10566",
                        "contenido_html": "<p>Las disposiciones de esta Ley se aplican al sector público.</p>"
                    }
                ]
            },
        ]
    }
}

SAMPLE_LAW_INDICE = {
    "data": {
        "bloque": [
            {"id": "pr", "titulo": "Preámbulo", "tipo": "preambulo", "fecha_actualizacion": "20151002"},
            {"id": "a1", "titulo": "Artículo 1. Objeto.", "tipo": "precepto", "fecha_actualizacion": "20200201"},
            {"id": "a2", "titulo": "Artículo 2. Ámbito subjetivo.", "tipo": "precepto", "fecha_actualizacion": "20151002"},
            {"id": "dd", "titulo": "Disposición derogatoria única.", "tipo": "parte_dispositiva", "fecha_actualizacion": "20151002"},
        ]
    }
}

SAMPLE_BOE_SUMMARY = {
    "data": {
        "sumario": {
            "diario": [
                {
                    "numero": "130",
                    "sumario_diario": {
                        "identificador": "BOE-S-2024-130",
                        "url_pdf": "https://www.boe.es/boe/dias/2024/05/29/sumario.pdf",
                        "size_bytes": 512000,
                        "size_kbytes": 500,
                    },
                    "seccion": [
                        {
                            "codigo": "1",
                            "nombre": "I. Disposiciones generales",
                            "departamento": [
                                {
                                    "codigo": "7723",
                                    "nombre": "Jefatura del Estado",
                                    "item": [
                                        {
                                            "identificador": "BOE-A-2024-1234",
                                            "titulo": "Real Decreto 123/2024 sobre procedimiento administrativo",
                                            "url_pdf": "https://www.boe.es/boe/dias/2024/05/29/pdfs/BOE-A-2024-1234.pdf",
                                            "url_html": "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-1234",
                                            "url_xml": "",
                                            "size_bytes": 51200,
                                            "size_kbytes": 50,
                                            "pagina_inicial": 1,
                                            "pagina_final": 10,
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
}

SAMPLE_DEPARTMENTS_TABLE = {
    "data": {
        "nombre": "departamentos",
        "descripcion": "Tabla de departamentos",
        "fecha_actualizacion": "2024-01-01T00:00:00Z",
        "entradas": [
            {"codigo": "7723", "descripcion": "Jefatura del Estado", "activo": True},
            {"codigo": "1430", "descripcion": "Ministerio de Justicia", "activo": True},
            {"codigo": "1470", "descripcion": "Ministerio del Interior", "activo": True},
            {"codigo": "1431", "descripcion": "Secretaría de Estado de Justicia", "activo": True},
        ],
        "total_entradas": 4,
    }
}

SAMPLE_RANGES_TABLE = {
    "data": {
        "nombre": "rangos",
        "descripcion": "Tabla de rangos normativos",
        "fecha_actualizacion": "2024-01-01T00:00:00Z",
        "entradas": [
            {"codigo": "1300", "descripcion": "Ley", "activo": True},
            {"codigo": "1250", "descripcion": "Ley Orgánica", "activo": True},
            {"codigo": "1200", "descripcion": "Real Decreto", "activo": True},
            {"codigo": "1100", "descripcion": "Real Decreto-ley", "activo": True},
        ],
        "total_entradas": 4,
    }
}

SAMPLE_MATTERS_TABLE = {
    "data": {
        "nombre": "materias",
        "descripcion": "Tabla de materias",
        "fecha_actualizacion": "2024-01-01T00:00:00Z",
        "entradas": [
            {"codigo": "2310", "descripcion": "Sector público", "activo": True},
            {"codigo": "7200", "descripcion": "Procedimiento administrativo", "activo": True},
            {"codigo": "5000", "descripcion": "Medio ambiente", "activo": True},
        ],
        "total_entradas": 3,
    }
}


# ---------------------------------------------------------------------------
# Fixture: mock del cliente HTTP
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_http_client():
    """Cliente HTTP simulado que devuelve datos de ejemplo predefinidos."""
    client = MagicMock()

    async def _get_law_by_id(law_id, section):
        if section == 'metadatos':
            return SAMPLE_LAW_METADATA
        elif section == 'analisis':
            return SAMPLE_LAW_ANALYSIS
        elif section == 'texto':
            return SAMPLE_LAW_TEXTO
        elif section == 'texto/indice':
            return SAMPLE_LAW_INDICE
        return {"data": None}

    async def _get_boe_summary(date):
        return SAMPLE_BOE_SUMMARY

    async def _get_auxiliary_table(table_name):
        tables = {
            'departamentos': SAMPLE_DEPARTMENTS_TABLE,
            'rangos': SAMPLE_RANGES_TABLE,
            'materias': SAMPLE_MATTERS_TABLE,
        }
        return tables.get(table_name, {"data": None})

    client.get_law_by_id = AsyncMock(side_effect=_get_law_by_id)
    client.get_boe_summary = AsyncMock(side_effect=_get_boe_summary)
    client.get_auxiliary_table = AsyncMock(side_effect=_get_auxiliary_table)

    return client
