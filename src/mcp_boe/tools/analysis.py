"""
Herramientas MCP de calidad de vida para el análisis de legislación del BOE.

Este módulo contiene herramientas auxiliares que facilitan el trabajo con normas
largas: paginación de texto, esqueleto estructural, normalización de referencias
y explicación compacta de la estructura.
"""

import base64
import logging
import re
from typing import Dict, Any, List, Optional

from mcp.types import TextContent, Tool

from ..utils.http_client import BOEHTTPClient, APIError
from ..models.boe_models import validate_boe_identifier

logger = logging.getLogger(__name__)

# Meses en español para normalización de fechas en referencias
_MESES_ES = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
}


class AnalysisTools:
    """Herramientas de análisis y calidad de vida para normas del BOE."""

    def __init__(self, http_client: BOEHTTPClient):
        self.client = http_client

    def get_tools(self) -> List[Tool]:
        """Retorna la lista de herramientas disponibles."""
        return [
            Tool(
                name="summarize_law_sections",
                description=(
                    "Devuelve un esqueleto de la norma: lista de bloques (preámbulo, artículos, "
                    "disposiciones) con su título y el primer párrafo de cada uno, sin texto completo. "
                    "Útil para obtener una visión rápida del contenido antes de profundizar."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma (ej: 'BOE-A-2015-10566')"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="paginate_law_text",
                description=(
                    "Devuelve el texto de una norma en fragmentos manejables. "
                    "Permite al LLM leer normas largas trozo a trozo sin cargarlas enteras. "
                    "Usa el cursor devuelto en next_cursor para obtener el siguiente fragmento."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma"
                        },
                        "cursor": {
                            "type": "string",
                            "description": "Cursor de paginación (omitir o dejar vacío para la primera página)"
                        },
                        "max_chars": {
                            "type": "integer",
                            "minimum": 500,
                            "maximum": 10000,
                            "default": 4000,
                            "description": "Máximo de caracteres por fragmento (default: 4000)"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="explain_law_structure",
                description=(
                    "Devuelve un resumen estructural compacto de una norma: "
                    "lista de niveles con tipo, id, título y número de hijos directos. "
                    "Más conciso que get_law_structure, ideal para entender la organización rápidamente."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "law_id": {
                            "type": "string",
                            "pattern": "^BOE-[A-Z]-\\d{4}-\\d{1,5}$",
                            "description": "Identificador único de la norma"
                        }
                    },
                    "required": ["law_id"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="normalize_boe_reference",
                description=(
                    "Convierte una referencia libre a una norma o BOE en una forma normalizada. "
                    "Acepta textos como 'Ley 40/2015', 'Real Decreto 123/2020', "
                    "'Orden TED/1234/2023', 'BOE del 3 de mayo de 2024, sec. I', etc. "
                    "Devuelve el tipo, identificador normalizado y otros campos extraídos."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reference_text": {
                            "type": "string",
                            "description": "Texto libre con la referencia a normalizar"
                        }
                    },
                    "required": ["reference_text"],
                    "additionalProperties": False
                }
            ),
        ]

    # =========================================================================
    # summarize_law_sections
    # =========================================================================

    async def summarize_law_sections(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Devuelve un esqueleto de la norma con título y primer párrafo de cada bloque.

        Args:
            arguments: Diccionario con law_id.

        Returns:
            TextContent con la estructura resumida en markdown.
        """
        try:
            law_id = arguments['law_id']

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Generando esqueleto de norma {law_id}")

            response = await self.client.get_law_by_id(law_id, 'texto')

            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text=f"No se encontró texto para la norma {law_id}."
                )]

            bloques = response['data'].get('texto', [])
            if not isinstance(bloques, list):
                bloques = [bloques] if bloques else []

            if not bloques:
                return [TextContent(
                    type="text",
                    text=f"La norma {law_id} no contiene bloques de texto."
                )]

            formatted = self._format_law_skeleton(bloques, law_id)
            return [TextContent(type="text", text=formatted)]

        except APIError as e:
            logger.error(f"Error de API generando esqueleto de {law_id}: {e}")
            return [TextContent(type="text", text=f"Error accediendo a la norma {law_id}: {e.mensaje}")]
        except Exception as e:
            logger.error(f"Error inesperado generando esqueleto: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_law_skeleton(self, bloques: List[Dict[str, Any]], law_id: str) -> str:
        """Formatea el esqueleto de la norma con primer párrafo de cada bloque."""
        output = [f"# 📋 Esqueleto de la norma `{law_id}`", ""]

        tipo_emojis = {
            'preambulo': '📖',
            'precepto': '📄',
            'parte_dispositiva': '⚖️',
            'parte_final': '📝',
            'instrumento': '📎',
            'nota_inicial': '🔔',
            'encabezado': '🏷️',
            'firma': '✍️',
        }

        for bloque in bloques:
            block_id = bloque.get('id', 'N/A')
            titulo = bloque.get('titulo', 'Sin título')
            tipo = bloque.get('tipo', 'desconocido')
            emoji = tipo_emojis.get(tipo, '📌')

            output.append(f"## {emoji} {titulo} (`{block_id}`)")

            versiones = bloque.get('versiones', [])
            if not isinstance(versiones, list):
                versiones = [versiones] if versiones else []

            if versiones:
                # Usar la versión más reciente
                version = versiones[0]
                html = version.get('contenido_html', '')
                if html:
                    first_para = self._extract_first_paragraph(html)
                    if first_para:
                        output.append(f"> {first_para}")

            output.append("")

        output.append("---")
        output.append(
            "💡 Usa `get_law_text_block` con el ID entre paréntesis para el texto completo de cada bloque, "
            "o `paginate_law_text` para leer la norma en fragmentos."
        )
        return "\n".join(output)

    def _extract_first_paragraph(self, html: str) -> str:
        """Extrae el primer párrafo de texto de un fragmento HTML."""
        # Buscar primer <p>...</p>
        match = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
        else:
            text = html

        # Limpiar tags HTML básicos
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Truncar a 200 caracteres
        if len(text) > 200:
            text = text[:197] + '…'
        return text

    # =========================================================================
    # paginate_law_text
    # =========================================================================

    async def paginate_law_text(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Devuelve el texto de una norma en fragmentos paginados.

        El cursor es un entero codificado en base64 que indica el índice
        del primer bloque de la página actual. Es determinista y estable
        mientras la norma no cambie.

        Args:
            arguments: Diccionario con law_id, cursor opcional y max_chars.

        Returns:
            TextContent con chunk_text, articles_included y next_cursor.
        """
        try:
            law_id = arguments['law_id']
            cursor_str = arguments.get('cursor') or ''
            max_chars = arguments.get('max_chars', 4000)

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            # Decodificar cursor
            start_index = 0
            if cursor_str:
                try:
                    start_index = int(base64.b64decode(cursor_str.encode()).decode())
                except Exception:
                    raise ValueError(f"Cursor inválido: {cursor_str}")

            logger.info(f"Paginando texto de {law_id} desde bloque {start_index}, max_chars={max_chars}")

            response = await self.client.get_law_by_id(law_id, 'texto')

            if not response.get('data'):
                return [TextContent(type="text", text=f"No se encontró texto para la norma {law_id}.")]

            bloques = response['data'].get('texto', [])
            if not isinstance(bloques, list):
                bloques = [bloques] if bloques else []

            if start_index >= len(bloques):
                return [TextContent(
                    type="text",
                    text=(
                        f"## Paginación de `{law_id}`\n\n"
                        "**No hay más contenido.** El cursor proporcionado apunta más allá del último bloque.\n\n"
                        "**Artículos incluidos:** (ninguno)\n"
                        "**Siguiente cursor:** (fin)"
                    )
                )]

            # Construir fragmento acumulando bloques hasta max_chars
            chunk_parts: List[str] = []
            articles_included: List[str] = []
            current_chars = 0
            current_index = start_index

            for idx in range(start_index, len(bloques)):
                bloque = bloques[idx]
                block_id = bloque.get('id', f'bloque_{idx}')
                titulo = bloque.get('titulo', '')

                versiones = bloque.get('versiones', [])
                if not isinstance(versiones, list):
                    versiones = [versiones] if versiones else []

                html = versiones[0].get('contenido_html', '') if versiones else ''
                clean_text = self._clean_html(html)

                block_text = f"### {titulo} (`{block_id}`)\n\n{clean_text}\n" if titulo else f"{clean_text}\n"

                if current_chars + len(block_text) > max_chars and chunk_parts:
                    # No cabe en la página actual; parar aquí
                    break

                chunk_parts.append(block_text)
                articles_included.append(block_id)
                current_chars += len(block_text)
                current_index = idx + 1

            # Calcular next_cursor
            next_cursor: Optional[str] = None
            if current_index < len(bloques):
                next_cursor = base64.b64encode(str(current_index).encode()).decode()

            chunk_text = "\n".join(chunk_parts)
            page_num = start_index + 1

            result_lines = [
                f"## 📄 Texto de `{law_id}` — desde bloque {start_index + 1}",
                "",
                chunk_text,
                "---",
                f"**Bloques incluidos:** {', '.join(f'`{a}`' for a in articles_included)}",
            ]
            if next_cursor:
                result_lines.append(f"**Siguiente cursor:** `{next_cursor}`")
                result_lines.append("*(Usa `paginate_law_text` con este cursor para continuar.)*")
            else:
                result_lines.append("**Fin del documento.** No hay más páginas.")

            return [TextContent(type="text", text="\n".join(result_lines))]

        except APIError as e:
            logger.error(f"Error de API paginando {law_id}: {e}")
            return [TextContent(type="text", text=f"Error accediendo a la norma {law_id}: {e.mensaje}")]
        except Exception as e:
            logger.error(f"Error inesperado paginando texto: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _clean_html(self, html: str) -> str:
        """Limpia HTML básico para texto plano."""
        text = re.sub(r'</p>\s*<p[^>]*>', '\n\n', html)
        text = re.sub(r'<p[^>]*>', '', text)
        text = re.sub(r'</p>', '', text)
        text = re.sub(r'<li[^>]*>', '\n• ', text)
        text = re.sub(r'</li>', '', text)
        text = re.sub(r'</?[uo]l[^>]*>', '', text)
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    # =========================================================================
    # explain_law_structure
    # =========================================================================

    async def explain_law_structure(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Devuelve una lista compacta con la estructura de la norma y conteo de hijos.

        Args:
            arguments: Diccionario con law_id.

        Returns:
            TextContent con la estructura compacta en markdown.
        """
        try:
            law_id = arguments['law_id']

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Explicando estructura de norma {law_id}")

            response = await self.client.get_law_by_id(law_id, 'texto/indice')

            if not response.get('data'):
                return [TextContent(type="text", text=f"No se encontró estructura para la norma {law_id}.")]

            structure_data = response['data']
            formatted = self._format_compact_structure(structure_data, law_id)
            return [TextContent(type="text", text=formatted)]

        except APIError as e:
            logger.error(f"Error de API obteniendo estructura de {law_id}: {e}")
            return [TextContent(type="text", text=f"Error accediendo a la norma {law_id}: {e.mensaje}")]
        except Exception as e:
            logger.error(f"Error inesperado explicando estructura: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_compact_structure(self, structure_data: Dict[str, Any], law_id: str) -> str:
        """Formatea la estructura del índice de forma compacta."""
        output = [f"# 🗂️ Estructura compacta de `{law_id}`", ""]

        bloques = structure_data.get('bloque', [])
        if not isinstance(bloques, list):
            bloques = [bloques] if bloques else []

        if not bloques:
            return f"No se encontró información de estructura para `{law_id}`."

        # Clasificar bloques y agrupar por tipo
        tipos_orden = [
            ('preambulo', '📖 Preámbulo'),
            ('precepto', '📄 Articulado'),
            ('parte_dispositiva', '⚖️ Parte dispositiva'),
            ('parte_final', '📝 Parte final'),
            ('instrumento', '📎 Instrumentos/Anexos'),
        ]

        # Agrupar por prefijo de ID para detectar capítulos/títulos
        grupos: Dict[str, List[Dict]] = {}
        for bloque in bloques:
            block_id = bloque.get('id', 'N/A')
            titulo = bloque.get('titulo', 'Sin título')
            fecha = bloque.get('fecha_actualizacion', '')

            # Determinar grupo
            if block_id.startswith('a'):
                grupo = 'precepto'
            elif block_id in ('pr', 'preambulo'):
                grupo = 'preambulo'
            elif block_id.startswith('dd'):
                grupo = 'parte_dispositiva'
            elif block_id.startswith('d'):
                grupo = 'parte_final'
            else:
                grupo = 'instrumento'

            if grupo not in grupos:
                grupos[grupo] = []
            grupos[grupo].append({'id': block_id, 'titulo': titulo, 'fecha': fecha})

        for tipo_key, tipo_label in tipos_orden:
            items = grupos.get(tipo_key, [])
            if not items:
                continue

            output.append(f"## {tipo_label} ({len(items)} elemento{'s' if len(items) != 1 else ''})")
            output.append("")

            for item in items:
                fecha_str = ''
                if item['fecha'] and len(item['fecha']) == 8:
                    try:
                        from datetime import datetime
                        d = datetime.strptime(item['fecha'], '%Y%m%d')
                        fecha_str = f" *(actualizado {d.strftime('%d/%m/%Y')})*"
                    except ValueError:
                        pass
                output.append(f"- **{item['titulo']}** `{item['id']}`{fecha_str}")

            output.append("")

        output.append("---")
        output.append("💡 Usa `get_law_text_block` con cualquiera de los IDs para leer ese bloque.")
        return "\n".join(output)

    # =========================================================================
    # normalize_boe_reference
    # =========================================================================

    async def normalize_boe_reference(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Normaliza una referencia libre a una norma o edición del BOE.

        No realiza llamadas a la API; trabaja exclusivamente con expresiones regulares.

        Args:
            arguments: Diccionario con reference_text.

        Returns:
            TextContent con los campos normalizados.
        """
        try:
            reference_text = arguments['reference_text'].strip()
            if not reference_text:
                raise ValueError("El texto de referencia no puede estar vacío.")

            logger.info(f"Normalizando referencia: '{reference_text}'")

            result = self._normalize_reference(reference_text)
            formatted = self._format_normalized_reference(reference_text, result)
            return [TextContent(type="text", text=formatted)]

        except Exception as e:
            logger.error(f"Error normalizando referencia: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _normalize_reference(self, text: str) -> Dict[str, Any]:
        """Aplica patrones regex para normalizar una referencia a norma/BOE."""
        # 1. BOE ID directo
        m = re.search(r'BOE-[A-Z]-\d{4}-\d{1,5}', text)
        if m:
            return {
                'type': 'law',
                'law_id': m.group(0),
                'normalized_string': m.group(0),
            }

        # 2. Ley Orgánica X/YYYY o Ley X/YYYY
        m = re.search(
            r'Ley\s+(Org[aá]nica\s+)?(\d+)/(\d{4})',
            text, re.IGNORECASE
        )
        if m:
            org = 'Orgánica ' if m.group(1) else ''
            numero, anio = m.group(2), m.group(3)
            norm = f"Ley {org}{numero}/{anio}"
            return {
                'type': 'law',
                'normalized_string': norm,
                'number': numero,
                'year': anio,
                'is_organic': bool(m.group(1)),
            }

        # 3. Real Decreto-ley / Real Decreto Legislativo / Real Decreto
        m = re.search(
            r'Real\s+Decreto(-ley|-legislativo)?\s+(\d+)/(\d{4})',
            text, re.IGNORECASE
        )
        if m:
            sufijo = (m.group(1) or '').replace('-', '-').strip('-').capitalize()
            tipo = f"Real Decreto{('-' + sufijo) if sufijo else ''}"
            numero, anio = m.group(2), m.group(3)
            norm = f"{tipo} {numero}/{anio}"
            return {
                'type': 'law',
                'normalized_string': norm,
                'number': numero,
                'year': anio,
            }

        # 4. Orden ministerial: Orden AAA/NNN/YYYY
        m = re.search(
            r'Orden\s+([A-Z]{2,6})/(\d+)/(\d{4})',
            text, re.IGNORECASE
        )
        if m:
            dept, numero, anio = m.group(1).upper(), m.group(2), m.group(3)
            norm = f"Orden {dept}/{numero}/{anio}"
            return {
                'type': 'order',
                'normalized_string': norm,
                'department_code': dept,
                'number': numero,
                'year': anio,
            }

        # 5. Resolución de fecha "Resolución de X de [mes] de YYYY"
        m = re.search(
            r'Resoluci[oó]n\s+de\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            text, re.IGNORECASE
        )
        if m:
            dia, mes_str, anio = m.group(1), m.group(2).lower(), m.group(3)
            mes = _MESES_ES.get(mes_str)
            date_str = f"{anio}{mes}{dia.zfill(2)}" if mes else None
            norm = f"Resolución de {dia} de {mes_str.capitalize()} de {anio}"
            return {
                'type': 'resolution',
                'normalized_string': norm,
                'date': date_str,
            }

        # 6. BOE del/de [día] de [mes] de [año]
        m = re.search(
            r'BOE\s+del?\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            text, re.IGNORECASE
        )
        if m:
            dia, mes_str, anio = m.group(1), m.group(2).lower(), m.group(3)
            mes = _MESES_ES.get(mes_str)
            date_api = f"{anio}{mes}{dia.zfill(2)}" if mes else None
            section = None
            sec_m = re.search(r'sec(?:ci[oó]n)?\s*\.?\s*([IVX]+|\d+[AB]?)', text, re.IGNORECASE)
            if sec_m:
                section = sec_m.group(1).upper()
            norm = f"BOE del {dia} de {mes_str.capitalize()} de {anio}"
            if section:
                norm += f", sección {section}"
            return {
                'type': 'boe_issue',
                'normalized_string': norm,
                'date': date_api,
                'section': section,
            }

        # 7. BOE de fecha numérica DD/MM/YYYY
        m = re.search(r'BOE\s+de\s+(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', text, re.IGNORECASE)
        if m:
            dia, mes, anio = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
            date_api = f"{anio}{mes}{dia}"
            norm = f"BOE de {dia}/{mes}/{anio}"
            return {
                'type': 'boe_issue',
                'normalized_string': norm,
                'date': date_api,
                'section': None,
            }

        # 8. Número de BOE: "BOE núm. NNN de YYYY" o "BOE n.º NNN"
        m = re.search(r'BOE\s+n[uú]m\.?\s*(\d+)', text, re.IGNORECASE)
        if m:
            return {
                'type': 'boe_issue',
                'normalized_string': f"BOE núm. {m.group(1)}",
                'boe_number': m.group(1),
                'date': None,
                'section': None,
            }

        # No reconocido
        return {
            'type': 'unknown',
            'normalized_string': text,
            'explanation': 'No se reconoció el formato de la referencia.',
        }

    def _format_normalized_reference(self, original: str, result: Dict[str, Any]) -> str:
        """Formatea el resultado de la normalización."""
        ref_type = result.get('type', 'unknown')
        norm = result.get('normalized_string', original)

        type_labels = {
            'law': '📜 Norma legal',
            'order': '📋 Orden ministerial',
            'resolution': '📄 Resolución',
            'boe_issue': '📰 Número del BOE',
            'unknown': '❓ No reconocido',
        }

        output = [
            "# 🔍 Referencia normalizada",
            "",
            f"**Texto original:** {original}",
            f"**Tipo:** {type_labels.get(ref_type, ref_type)}",
            f"**Forma normalizada:** `{norm}`",
            "",
        ]

        if ref_type == 'law':
            if result.get('law_id'):
                output.append(f"**Identificador BOE:** `{result['law_id']}`")
                output.append(
                    f"💡 Usa `get_law_metadata` o `get_consolidated_law` con el ID `{result['law_id']}` "
                    "para obtener información completa."
                )
            else:
                if result.get('number') and result.get('year'):
                    output.append(f"**Número/Año:** {result['number']}/{result['year']}")
                if result.get('is_organic'):
                    output.append("**Tipo:** Ley Orgánica")
                output.append(
                    "💡 Usa `search_consolidated_legislation` con `query` o `title` para encontrar esta norma."
                )
        elif ref_type == 'order':
            output.append(f"**Departamento (código):** `{result.get('department_code', 'N/A')}`")
            output.append(f"**Número/Año:** {result.get('number', 'N/A')}/{result.get('year', 'N/A')}")
            output.append(
                "💡 Usa `search_consolidated_legislation` con `title` para encontrar esta orden."
            )
        elif ref_type == 'boe_issue':
            if result.get('date'):
                output.append(f"**Fecha (AAAAMMDD):** `{result['date']}`")
                output.append(f"💡 Usa `get_boe_summary` con `date: \"{result['date']}\"` para ver el sumario.")
            if result.get('section'):
                output.append(f"**Sección:** {result['section']}")
            if result.get('boe_number'):
                output.append(f"**Número BOE:** {result['boe_number']}")
        elif ref_type == 'unknown':
            output.append(f"⚠️ {result.get('explanation', 'Formato no reconocido.')}")
            output.append(
                "💡 Prueba con formatos como: 'Ley 40/2015', 'Real Decreto 123/2020', "
                "'Orden TED/1234/2023', 'BOE del 3 de mayo de 2024', 'BOE-A-2015-10566'."
            )

        return "\n".join(output)
