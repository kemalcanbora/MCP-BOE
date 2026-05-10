"""
Herramientas MCP para acceso a las tablas auxiliares del BOE.

Este módulo contiene las herramientas que Claude puede usar para consultar
las tablas de códigos, departamentos, materias y otros datos auxiliares.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from mcp.types import TextContent, Tool

from ..utils.http_client import BOEHTTPClient, APIError
from ..models.boe_models import validate_boe_identifier

logger = logging.getLogger(__name__)


class AuxiliaryTools:
    """Herramientas para trabajar con tablas auxiliares del BOE."""
    
    def __init__(self, http_client: BOEHTTPClient):
        self.client = http_client

    def get_tools(self) -> List[Tool]:
        """Retorna la lista de herramientas disponibles."""
        return [
            Tool(
                name="get_departments_table",
                description="Obtiene la tabla de códigos de departamentos oficiales",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Término de búsqueda para filtrar departamentos por nombre"
                        },
                        "active_only": {
                            "type": "boolean",
                            "default": True,
                            "description": "Mostrar solo departamentos activos"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 50,
                            "description": "Número máximo de departamentos a mostrar"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_legal_ranges_table",
                description="Obtiene la tabla de rangos normativos (Ley, Real Decreto, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Término de búsqueda para filtrar rangos por nombre"
                        },
                        "active_only": {
                            "type": "boolean",
                            "default": True,
                            "description": "Mostrar solo rangos activos"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_matters_table", 
                description="Obtiene la tabla de materias/temáticas del vocabulario controlado",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Término de búsqueda para filtrar materias por descripción"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 50,
                            "description": "Número máximo de materias a mostrar"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_scopes_table",
                description="Obtiene la tabla de ámbitos (estatal, autonómico)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_consolidation_states_table",
                description="Obtiene la tabla de estados de consolidación",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="search_auxiliary_data",
                description="Busca información específica en las tablas auxiliares",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Término de búsqueda general"
                        },
                        "table_type": {
                            "type": "string",
                            "enum": ["all", "departments", "ranges", "matters", "scopes", "states"],
                            "default": "all",
                            "description": "Tipo de tabla donde buscar"
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="get_code_description",
                description="Obtiene la descripción de un código específico",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Código a buscar (ej: '7723', '1300')"
                        },
                        "code_type": {
                            "type": "string",
                            "enum": ["department", "range", "matter", "scope", "state"],
                            "description": "Tipo de código si se conoce (acelera la búsqueda)"
                        }
                    },
                    "required": ["code"],
                    "additionalProperties": False
                }
            ),
            # --- Nuevas tools (grupo C) ---
            Tool(
                name="search_departments_advanced",
                description=(
                    "Búsqueda avanzada de departamentos con filtros adicionales: "
                    "código padre para explorar jerarquías, filtro de texto y paginación. "
                    "Complementa a get_departments_table con más opciones de filtrado."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Filtro de texto sobre el nombre del departamento"
                        },
                        "active_only": {
                            "type": "boolean",
                            "default": True,
                            "description": "Mostrar solo departamentos activos (default: true)"
                        },
                        "parent_code": {
                            "type": "string",
                            "description": "Filtrar por prefijo de código para explorar jerarquías (ej: '14' para Ministerio de Justicia y sus organismos)"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 200,
                            "default": 50,
                            "description": "Número máximo de resultados (default: 50)"
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            ),
            Tool(
                name="list_topics_for_law",
                description=(
                    "Devuelve las materias/temas del vocabulario controlado asociados a una norma. "
                    "Útil para entender la temática de una ley y encontrar filtros para búsquedas relacionadas."
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
                name="suggest_auxiliary_filters",
                description=(
                    "Dado un texto de búsqueda libre, sugiere códigos de departamentos, materias "
                    "y rangos normativos que podrían usarse como filtros en otras herramientas. "
                    "Útil para descubrir los códigos correctos antes de una búsqueda de legislación."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Texto libre para el que buscar sugerencias de filtros"
                        },
                        "max_suggestions": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 30,
                            "default": 10,
                            "description": "Número máximo de sugerencias (default: 10)"
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False
                }
            ),
        ]

    async def get_departments_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la tabla de departamentos oficiales.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con los departamentos
        """
        try:
            search_term = arguments.get('search_term')
            active_only = arguments.get('active_only', True)
            limit = arguments.get('limit', 50)

            logger.info("Obteniendo tabla de departamentos")

            # Obtener tabla de departamentos
            response = await self.client.get_auxiliary_table('departamentos')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text="No se pudo obtener la tabla de departamentos."
                )]

            departments_data = response['data']
            formatted_table = self._format_departments_table(
                departments_data, 
                search_term, 
                active_only, 
                limit
            )

            return [TextContent(
                type="text",
                text=formatted_table
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo departamentos: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la tabla de departamentos: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo departamentos: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_departments_table(
        self, 
        departments_data: Dict[str, Any], 
        search_term: Optional[str],
        active_only: bool,
        limit: int
    ) -> str:
        """Formatea la tabla de departamentos."""
        output = []
        output.append("# 🏛️ Departamentos oficiales del BOE")
        output.append("")

        # Procesar entradas
        entries = departments_data.get('entradas', [])
        if not entries:
            return "No se encontraron departamentos en la tabla."

        # Filtrar entradas
        filtered_entries = []
        for entry in entries:
            # Filtrar por activo
            if active_only and entry.get('activo', True) != True:
                continue
            
            # Filtrar por término de búsqueda
            if search_term:
                descripcion = entry.get('descripcion', '').lower()
                if search_term.lower() not in descripcion:
                    continue
            
            filtered_entries.append(entry)

        if not filtered_entries:
            search_desc = f" que contengan '{search_term}'" if search_term else ""
            return f"No se encontraron departamentos{search_desc}."

        # Limitar resultados
        showing_entries = filtered_entries[:limit]
        
        output.append(f"**Mostrando {len(showing_entries)} de {len(filtered_entries)} departamentos**")
        if search_term:
            output.append(f"*Filtrado por: '{search_term}'*")
        output.append("")

        # Agrupar por tipo/jerarquía si es posible
        # Para simplificar, mostraremos alfabéticamente
        showing_entries.sort(key=lambda x: x.get('descripcion', ''))

        for entry in showing_entries:
            codigo = entry.get('codigo', 'N/A')
            descripcion = entry.get('descripcion', 'Sin descripción')
            
            output.append(f"- **{descripcion}**")
            output.append(f"  - Código: `{codigo}`")
            
            # Información adicional si está disponible
            if entry.get('fecha_creacion'):
                output.append(f"  - Creado: {entry['fecha_creacion']}")
            if not entry.get('activo', True):
                output.append(f"  - ⚠️ *Inactivo*")
            
            output.append("")

        if len(filtered_entries) > limit:
            output.append("---")
            output.append(f"*(Mostrando los primeros {limit} resultados de {len(filtered_entries)} encontrados)*")

        output.append("💡 **Tip:** Use el código del departamento en búsquedas de legislación para filtrar por emisor.")
        
        return "\n".join(output)

    async def get_legal_ranges_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la tabla de rangos normativos.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con los rangos normativos
        """
        try:
            search_term = arguments.get('search_term')
            active_only = arguments.get('active_only', True)

            logger.info("Obteniendo tabla de rangos normativos")

            response = await self.client.get_auxiliary_table('rangos')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text="No se pudo obtener la tabla de rangos normativos."
                )]

            ranges_data = response['data']
            formatted_table = self._format_ranges_table(ranges_data, search_term, active_only)

            return [TextContent(
                type="text",
                text=formatted_table
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo rangos: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la tabla de rangos: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo rangos: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_ranges_table(
        self, 
        ranges_data: Dict[str, Any], 
        search_term: Optional[str],
        active_only: bool
    ) -> str:
        """Formatea la tabla de rangos normativos."""
        output = []
        output.append("# ⚖️ Rangos normativos")
        output.append("")

        entries = ranges_data.get('entradas', [])
        if not entries:
            return "No se encontraron rangos normativos en la tabla."

        # Filtrar entradas
        filtered_entries = []
        for entry in entries:
            if active_only and entry.get('activo', True) != True:
                continue
            
            if search_term:
                descripcion = entry.get('descripcion', '').lower()
                if search_term.lower() not in descripcion:
                    continue
            
            filtered_entries.append(entry)

        if not filtered_entries:
            search_desc = f" que contengan '{search_term}'" if search_term else ""
            return f"No se encontraron rangos{search_desc}."

        # Ordenar por jerarquía normativa (aproximada)
        def get_hierarchy_order(descripcion):
            desc_lower = descripcion.lower()
            if 'constitución' in desc_lower:
                return 0
            elif 'ley orgánica' in desc_lower:
                return 1
            elif 'ley' in desc_lower and 'orgánica' not in desc_lower:
                return 2
            elif 'real decreto-ley' in desc_lower:
                return 3
            elif 'real decreto legislativo' in desc_lower:
                return 4
            elif 'real decreto' in desc_lower:
                return 5
            elif 'decreto' in desc_lower:
                return 6
            elif 'orden' in desc_lower:
                return 7
            elif 'resolución' in desc_lower:
                return 8
            else:
                return 9

        filtered_entries.sort(key=lambda x: (get_hierarchy_order(x.get('descripcion', '')), x.get('descripcion', '')))

        output.append(f"**{len(filtered_entries)} rangos normativos**")
        if search_term:
            output.append(f"*Filtrado por: '{search_term}'*")
        output.append("")

        # Agrupar por jerarquía
        hierarchy_groups = {
            "Normas constitucionales": [],
            "Leyes": [],
            "Decretos": [], 
            "Órdenes y resoluciones": [],
            "Otros": []
        }

        for entry in filtered_entries:
            codigo = entry.get('codigo', 'N/A')
            descripcion = entry.get('descripcion', 'Sin descripción')
            desc_lower = descripcion.lower()
            
            if 'constitución' in desc_lower:
                hierarchy_groups["Normas constitucionales"].append((codigo, descripcion, entry))
            elif 'ley' in desc_lower:
                hierarchy_groups["Leyes"].append((codigo, descripcion, entry))
            elif 'decreto' in desc_lower:
                hierarchy_groups["Decretos"].append((codigo, descripcion, entry))
            elif 'orden' in desc_lower or 'resolución' in desc_lower:
                hierarchy_groups["Órdenes y resoluciones"].append((codigo, descripcion, entry))
            else:
                hierarchy_groups["Otros"].append((codigo, descripcion, entry))

        # Mostrar por grupos
        for group_name, group_entries in hierarchy_groups.items():
            if group_entries:
                output.append(f"## {group_name}")
                output.append("")
                
                for codigo, descripcion, entry in group_entries:
                    output.append(f"- **{descripcion}**")
                    output.append(f"  - Código: `{codigo}`")
                    
                    if not entry.get('activo', True):
                        output.append(f"  - ⚠️ *Inactivo*")
                    
                    output.append("")

        output.append("💡 **Tip:** Use el código del rango en búsquedas para filtrar por tipo de norma.")
        
        return "\n".join(output)

    async def get_matters_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la tabla de materias del vocabulario controlado.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con las materias
        """
        try:
            search_term = arguments.get('search_term')
            limit = arguments.get('limit', 50)

            logger.info("Obteniendo tabla de materias")

            response = await self.client.get_auxiliary_table('materias')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text="No se pudo obtener la tabla de materias."
                )]

            matters_data = response['data']
            formatted_table = self._format_matters_table(matters_data, search_term, limit)

            return [TextContent(
                type="text",
                text=formatted_table
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo materias: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la tabla de materias: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo materias: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_matters_table(
        self, 
        matters_data: Dict[str, Any], 
        search_term: Optional[str],
        limit: int
    ) -> str:
        """Formatea la tabla de materias."""
        output = []
        output.append("# 📚 Materias del vocabulario controlado")
        output.append("")

        entries = matters_data.get('entradas', [])
        if not entries:
            return "No se encontraron materias en la tabla."

        # Filtrar entradas
        filtered_entries = []
        for entry in entries:
            if search_term:
                descripcion = entry.get('descripcion', '').lower()
                if search_term.lower() not in descripcion:
                    continue
            
            filtered_entries.append(entry)

        if not filtered_entries:
            return f"No se encontraron materias que contengan '{search_term}'."

        # Ordenar alfabéticamente
        filtered_entries.sort(key=lambda x: x.get('descripcion', ''))
        showing_entries = filtered_entries[:limit]

        output.append(f"**Mostrando {len(showing_entries)} de {len(filtered_entries)} materias**")
        if search_term:
            output.append(f"*Filtrado por: '{search_term}'*")
        output.append("")

        # Agrupar por primera letra para facilitar navegación
        current_letter = ""
        for entry in showing_entries:
            codigo = entry.get('codigo', 'N/A')
            descripcion = entry.get('descripcion', 'Sin descripción')
            first_letter = descripcion[0].upper() if descripcion else "#"
            
            if first_letter != current_letter:
                if current_letter:  # No para la primera
                    output.append("")
                output.append(f"### {first_letter}")
                output.append("")
                current_letter = first_letter
            
            output.append(f"- **{descripcion}** (`{codigo}`)")

        if len(filtered_entries) > limit:
            output.append("")
            output.append("---")
            output.append(f"*(Mostrando los primeros {limit} resultados de {len(filtered_entries)} encontrados)*")

        output.append("")
        output.append("💡 **Tip:** Use el código de materia en búsquedas para filtrar por temática específica.")
        
        return "\n".join(output)

    async def get_scopes_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la tabla de ámbitos (estatal, autonómico).
        
        Args:
            arguments: Parámetros (vacíos para esta tabla)
            
        Returns:
            Lista de contenido con los ámbitos
        """
        try:
            logger.info("Obteniendo tabla de ámbitos")

            response = await self.client.get_auxiliary_table('ambitos')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text="No se pudo obtener la tabla de ámbitos."
                )]

            scopes_data = response['data']
            formatted_table = self._format_simple_table(
                scopes_data, 
                "🌍 Ámbitos normativos",
                "ámbito"
            )

            return [TextContent(
                type="text",
                text=formatted_table
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo ámbitos: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la tabla de ámbitos: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo ámbitos: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    async def get_consolidation_states_table(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la tabla de estados de consolidación.
        
        Args:
            arguments: Parámetros (vacíos para esta tabla)
            
        Returns:
            Lista de contenido con los estados
        """
        try:
            logger.info("Obteniendo tabla de estados de consolidación")

            response = await self.client.get_auxiliary_table('estados-consolidacion')
            
            if not response.get('data'):
                return [TextContent(
                    type="text",
                    text="No se pudo obtener la tabla de estados de consolidación."
                )]

            states_data = response['data']
            formatted_table = self._format_simple_table(
                states_data, 
                "📊 Estados de consolidación",
                "estado"
            )

            return [TextContent(
                type="text",
                text=formatted_table
            )]

        except APIError as e:
            logger.error(f"Error de API obteniendo estados: {e}")
            return [TextContent(
                type="text",
                text=f"Error accediendo a la tabla de estados: {e.mensaje}"
            )]
        except Exception as e:
            logger.error(f"Error inesperado obteniendo estados: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _format_simple_table(
        self, 
        table_data: Dict[str, Any], 
        title: str,
        item_type: str
    ) -> str:
        """Formatea tablas simples (ámbitos, estados, etc.)."""
        output = []
        output.append(f"# {title}")
        output.append("")

        entries = table_data.get('entradas', [])
        if not entries:
            return f"No se encontraron {item_type}s en la tabla."

        output.append(f"**{len(entries)} {item_type}(s) disponibles:**")
        output.append("")

        for entry in entries:
            codigo = entry.get('codigo', 'N/A')
            descripcion = entry.get('descripcion', 'Sin descripción')
            
            output.append(f"- **{descripcion}** (`{codigo}`)")
            
            if not entry.get('activo', True):
                output.append(f"  - ⚠️ *Inactivo*")

        return "\n".join(output)

    async def search_auxiliary_data(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Busca información en las tablas auxiliares.
        
        Args:
            arguments: Parámetros de búsqueda
            
        Returns:
            Lista de contenido con los resultados
        """
        try:
            query = arguments['query']
            table_type = arguments.get('table_type', 'all')

            logger.info(f"Buscando '{query}' en tablas auxiliares")

            output = []
            output.append(f"# 🔍 Búsqueda: '{query}'")
            output.append("")

            found_results = []

            # Definir tablas a buscar
            tables_to_search = []
            if table_type == 'all':
                tables_to_search = [
                    ('departments', 'departamentos', '🏛️ Departamentos'),
                    ('ranges', 'rangos', '⚖️ Rangos normativos'), 
                    ('matters', 'materias', '📚 Materias'),
                    ('scopes', 'ambitos', '🌍 Ámbitos'),
                    ('states', 'estados-consolidacion', '📊 Estados')
                ]
            else:
                table_mapping = {
                    'departments': ('departments', 'departamentos', '🏛️ Departamentos'),
                    'ranges': ('ranges', 'rangos', '⚖️ Rangos normativos'),
                    'matters': ('matters', 'materias', '📚 Materias'),
                    'scopes': ('scopes', 'ambitos', '🌍 Ámbitos'),
                    'states': ('states', 'estados-consolidacion', '📊 Estados')
                }
                if table_type in table_mapping:
                    tables_to_search = [table_mapping[table_type]]

            # Buscar en cada tabla
            for table_key, table_name, table_display in tables_to_search:
                try:
                    response = await self.client.get_auxiliary_table(table_name)
                    if response.get('data'):
                        table_results = self._search_in_table(
                            response['data'], 
                            query, 
                            table_display
                        )
                        found_results.extend(table_results)
                except APIError:
                    # Tabla no disponible, continuar con las siguientes
                    continue

            if not found_results:
                output.append(f"No se encontraron resultados para '{query}' en las tablas auxiliares.")
            else:
                # Agrupar por tabla
                results_by_table = {}
                for result in found_results:
                    table = result['table']
                    if table not in results_by_table:
                        results_by_table[table] = []
                    results_by_table[table].append(result)

                output.append(f"**Encontrados {len(found_results)} resultado(s):**")
                output.append("")

                for table_name, table_results in results_by_table.items():
                    output.append(f"## {table_name}")
                    output.append("")
                    
                    for result in table_results[:10]:  # Limitar a 10 por tabla
                        output.append(f"- **{result['descripcion']}**")
                        output.append(f"  - Código: `{result['codigo']}`")
                        if not result.get('activo', True):
                            output.append(f"  - ⚠️ *Inactivo*")
                        output.append("")

                    if len(table_results) > 10:
                        output.append(f"*(... y {len(table_results) - 10} más)*")
                        output.append("")

            return [TextContent(
                type="text",
                text="\n".join(output)
            )]

        except Exception as e:
            logger.error(f"Error buscando en tablas auxiliares: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    def _search_in_table(
        self, 
        table_data: Dict[str, Any], 
        query: str, 
        table_name: str
    ) -> List[Dict[str, Any]]:
        """Busca un término en una tabla específica."""
        results = []
        query_lower = query.lower()
        
        entries = table_data.get('entradas', [])
        for entry in entries:
            descripcion = entry.get('descripcion', '')
            codigo = entry.get('codigo', '')
            
            # Buscar en descripción y código
            if (query_lower in descripcion.lower() or 
                query_lower in codigo.lower()):
                
                results.append({
                    'table': table_name,
                    'codigo': codigo,
                    'descripcion': descripcion,
                    'activo': entry.get('activo', True)
                })
        
        return results

    async def get_code_description(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Obtiene la descripción de un código específico.
        
        Args:
            arguments: Parámetros con el código a buscar
            
        Returns:
            Lista de contenido con la descripción del código
        """
        try:
            code = arguments['code']
            code_type = arguments.get('code_type')

            logger.info(f"Buscando descripción del código '{code}'")

            # Definir tablas donde buscar
            tables_to_search = []
            if code_type:
                type_mapping = {
                    'department': [('departamentos', '🏛️ Departamento')],
                    'range': [('rangos', '⚖️ Rango normativo')],
                    'matter': [('materias', '📚 Materia')],
                    'scope': [('ambitos', '🌍 Ámbito')],
                    'state': [('estados-consolidacion', '📊 Estado')]
                }
                tables_to_search = type_mapping.get(code_type, [])
            else:
                # Buscar en todas las tablas
                tables_to_search = [
                    ('departamentos', '🏛️ Departamento'),
                    ('rangos', '⚖️ Rango normativo'),
                    ('materias', '📚 Materia'),
                    ('ambitos', '🌍 Ámbito'),
                    ('estados-consolidacion', '📊 Estado')
                ]

            found_descriptions = []

            # Buscar en cada tabla
            for table_name, table_display in tables_to_search:
                try:
                    response = await self.client.get_auxiliary_table(table_name)
                    if response.get('data'):
                        entries = response['data'].get('entradas', [])
                        for entry in entries:
                            if entry.get('codigo') == code:
                                found_descriptions.append({
                                    'type': table_display,
                                    'descripcion': entry.get('descripcion', 'Sin descripción'),
                                    'activo': entry.get('activo', True)
                                })
                                break
                except APIError:
                    continue

            # Formatear resultado
            if not found_descriptions:
                result_text = f"No se encontró el código '{code}' en las tablas auxiliares."
            else:
                output = []
                output.append(f"# 🔍 Código: `{code}`")
                output.append("")
                
                for desc in found_descriptions:
                    status = "" if desc['activo'] else " ⚠️ *(Inactivo)*"
                    output.append(f"**{desc['type']}:** {desc['descripcion']}{status}")
                
                result_text = "\n".join(output)

            return [TextContent(
                type="text",
                text=result_text
            )]

        except Exception as e:
            logger.error(f"Error buscando código {code}: {e}")
            return [TextContent(
                type="text",
                text=f"Error interno: {str(e)}"
            )]

    # =========================================================================
    # search_departments_advanced
    # =========================================================================

    async def search_departments_advanced(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Búsqueda avanzada de departamentos con filtros adicionales.

        Extiende get_departments_table con soporte para filtro por código padre
        (jerarquía de organismos dependientes).

        Args:
            arguments: Diccionario con search_term, active_only, parent_code y limit.

        Returns:
            TextContent con la lista de departamentos filtrada.
        """
        try:
            search_term = arguments.get('search_term')
            active_only = arguments.get('active_only', True)
            parent_code = arguments.get('parent_code')
            limit = arguments.get('limit', 50)

            logger.info(
                f"search_departments_advanced: term={search_term}, "
                f"parent_code={parent_code}, active_only={active_only}"
            )

            response = await self.client.get_auxiliary_table('departamentos')

            if not response.get('data'):
                return [TextContent(type="text", text="No se pudo obtener la tabla de departamentos.")]

            entries = response['data'].get('entradas', [])

            # Filtrar
            filtered = []
            for entry in entries:
                if active_only and not entry.get('activo', True):
                    continue
                if search_term and search_term.lower() not in entry.get('descripcion', '').lower():
                    continue
                if parent_code:
                    # Los códigos hijos comienzan por el código padre (convención jerárquica)
                    if not entry.get('codigo', '').startswith(parent_code):
                        continue
                filtered.append(entry)

            filtered.sort(key=lambda e: e.get('descripcion', ''))
            showing = filtered[:limit]

            formatted = self._format_advanced_departments(showing, filtered, search_term, parent_code, limit)
            return [TextContent(type="text", text=formatted)]

        except APIError as e:
            logger.error(f"Error de API en search_departments_advanced: {e}")
            return [TextContent(type="text", text=f"Error accediendo a departamentos: {e.mensaje}")]
        except Exception as e:
            logger.error(f"Error inesperado en search_departments_advanced: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_advanced_departments(
        self,
        showing: List[Dict[str, Any]],
        filtered: List[Dict[str, Any]],
        search_term: Optional[str],
        parent_code: Optional[str],
        limit: int
    ) -> str:
        """Formatea los resultados de búsqueda avanzada de departamentos."""
        output = ["# 🏛️ Departamentos (búsqueda avanzada)", ""]

        if not showing:
            filters = []
            if search_term:
                filters.append(f"texto '{search_term}'")
            if parent_code:
                filters.append(f"código padre '{parent_code}'")
            desc = ' y '.join(filters) if filters else 'los filtros especificados'
            output.append(f"No se encontraron departamentos para {desc}.")
            return "\n".join(output)

        output.append(f"**Mostrando {len(showing)} de {len(filtered)} departamentos**")
        if search_term:
            output.append(f"*Filtro texto: '{search_term}'*")
        if parent_code:
            output.append(f"*Código padre: '{parent_code}'*")
        output.append("")

        for entry in showing:
            codigo = entry.get('codigo', 'N/A')
            desc = entry.get('descripcion', 'Sin descripción')
            activo = entry.get('activo', True)

            output.append(f"- **{desc}**")
            output.append(f"  - Código: `{codigo}`")
            if not activo:
                output.append("  - ⚠️ *Inactivo*")
            output.append("")

        if len(filtered) > limit:
            output.append(f"*(Mostrando los primeros {limit} de {len(filtered)} resultados)*")

        output.append("💡 Usa el código con `search_consolidated_legislation` (department_code) para filtrar normas.")
        return "\n".join(output)

    # =========================================================================
    # list_topics_for_law
    # =========================================================================

    async def list_topics_for_law(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Devuelve las materias/temas del vocabulario controlado de una norma.

        Obtiene el análisis de la norma y cruza sus materias con la tabla de materias
        para enriquecer la información.

        Args:
            arguments: Diccionario con law_id.

        Returns:
            TextContent con la lista de materias de la norma.
        """
        try:
            law_id = arguments['law_id']

            if not validate_boe_identifier(law_id):
                raise ValueError(f"Identificador de norma inválido: {law_id}")

            logger.info(f"Listando materias de norma {law_id}")

            # Obtener análisis de la norma
            response = await self.client.get_law_by_id(law_id, 'analisis')

            if not response.get('data'):
                return [TextContent(type="text", text=f"No se encontró análisis para la norma {law_id}.")]

            analysis_data = response['data']
            materias_norma = analysis_data.get('materias', [])

            if not materias_norma:
                return [TextContent(
                    type="text",
                    text=f"La norma `{law_id}` no tiene materias registradas en el análisis."
                )]

            # Intentar enriquecer con tabla de materias (best-effort)
            matters_by_code: Dict[str, str] = {}
            try:
                matters_response = await self.client.get_auxiliary_table('materias')
                if matters_response.get('data'):
                    for entry in matters_response['data'].get('entradas', []):
                        matters_by_code[entry.get('codigo', '')] = entry.get('descripcion', '')
            except APIError:
                pass  # La tabla es opcional

            formatted = self._format_law_topics(materias_norma, law_id, matters_by_code)
            return [TextContent(type="text", text=formatted)]

        except APIError as e:
            logger.error(f"Error de API en list_topics_for_law: {e}")
            return [TextContent(type="text", text=f"Error accediendo a la norma {law_id}: {e.mensaje}")]
        except Exception as e:
            logger.error(f"Error inesperado en list_topics_for_law: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_law_topics(
        self,
        materias: List[Any],
        law_id: str,
        matters_by_code: Dict[str, str]
    ) -> str:
        """Formatea las materias de una norma."""
        output = [f"# 📚 Materias de la norma `{law_id}`", ""]

        output.append(f"**{len(materias)} materia(s) registrada(s):**")
        output.append("")

        for materia in materias:
            if isinstance(materia, dict):
                codigo = materia.get('codigo', 'N/A')
                texto = materia.get('texto', '')
                # Enriquecer si tenemos la tabla
                tabla_desc = matters_by_code.get(codigo, '')
                desc = texto or tabla_desc or 'Sin descripción'
                output.append(f"- **{desc}** (`{codigo}`)")
            else:
                output.append(f"- {materia}")

        output.append("")
        output.append(
            "💡 Usa estos códigos con `search_consolidated_legislation` (matter_code) "
            "para encontrar otras normas sobre los mismos temas."
        )
        return "\n".join(output)

    # =========================================================================
    # suggest_auxiliary_filters
    # =========================================================================

    async def suggest_auxiliary_filters(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Dado un texto libre, sugiere códigos de tablas auxiliares como filtros.

        Carga departamentos, rangos y materias en paralelo y realiza una búsqueda
        case-insensitive sobre las descripciones.

        Args:
            arguments: Diccionario con query y max_suggestions.

        Returns:
            TextContent con las sugerencias de filtros ordenadas por relevancia.
        """
        try:
            query = arguments['query']
            max_suggestions = arguments.get('max_suggestions', 10)

            if not query.strip():
                raise ValueError("El parámetro 'query' no puede estar vacío.")

            logger.info(f"suggest_auxiliary_filters: query='{query}', max={max_suggestions}")

            # Cargar tablas en paralelo
            table_names = ['departamentos', 'rangos', 'materias']
            type_labels = {
                'departamentos': 'department',
                'rangos': 'range',
                'materias': 'topic',
            }

            results = await asyncio.gather(
                *[self.client.get_auxiliary_table(t) for t in table_names],
                return_exceptions=True
            )

            suggestions: List[Dict[str, Any]] = []
            query_lower = query.lower()

            for table_name, result in zip(table_names, results):
                if isinstance(result, Exception):
                    continue
                if not result.get('data'):
                    continue

                table_type = type_labels[table_name]
                for entry in result['data'].get('entradas', []):
                    desc = entry.get('descripcion', '')
                    codigo = entry.get('codigo', '')
                    if not entry.get('activo', True):
                        continue

                    if query_lower in desc.lower() or query_lower in codigo.lower():
                        # Calcular relevancia: coincidencia al inicio > en medio
                        pos = desc.lower().find(query_lower)
                        relevance = 0 if pos == 0 else (1 if pos > 0 else 2)
                        suggestions.append({
                            'type': table_type,
                            'code': codigo,
                            'label': desc,
                            '_relevance': relevance,
                            '_pos': pos,
                        })

            # Ordenar por relevancia y posición de la coincidencia
            suggestions.sort(key=lambda s: (s['_relevance'], s['_pos']))

            # Limitar y limpiar
            showing = suggestions[:max_suggestions]
            for s in showing:
                s.pop('_relevance', None)
                s.pop('_pos', None)

            formatted = self._format_filter_suggestions(showing, query, max_suggestions, len(suggestions))
            return [TextContent(type="text", text=formatted)]

        except ValueError as e:
            return [TextContent(type="text", text=f"Parámetros inválidos: {str(e)}")]
        except Exception as e:
            logger.error(f"Error en suggest_auxiliary_filters: {e}")
            return [TextContent(type="text", text=f"Error interno: {str(e)}")]

    def _format_filter_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
        query: str,
        max_suggestions: int,
        total_found: int
    ) -> str:
        """Formatea las sugerencias de filtros."""
        output = [
            f"# 💡 Sugerencias de filtros para «{query}»",
            "",
        ]

        if not suggestions:
            output.append(
                f"No se encontraron filtros de tablas auxiliares relacionados con «{query}».\n\n"
                "Prueba con términos más generales o consulta directamente "
                "`get_departments_table`, `get_legal_ranges_table` o `get_matters_table`."
            )
            return "\n".join(output)

        type_emojis = {
            'department': '🏛️ Departamento',
            'range': '⚖️ Rango normativo',
            'topic': '📚 Materia',
        }

        output.append(
            f"**{len(suggestions)} sugerencia(s)**"
            + (f" de {total_found} encontradas" if total_found > max_suggestions else "")
        )
        output.append("")

        # Agrupar por tipo para mejor legibilidad
        by_type: Dict[str, List[Dict]] = {}
        for s in suggestions:
            by_type.setdefault(s['type'], []).append(s)

        for type_key, type_label in type_emojis.items():
            items = by_type.get(type_key, [])
            if not items:
                continue
            output.append(f"## {type_label}")
            output.append("")
            for item in items:
                output.append(f"- **{item['label']}** — código: `{item['code']}`")
            output.append("")

        # Pista de uso
        param_map = {
            'department': 'department_code',
            'range': 'legal_range_code',
            'topic': 'matter_code',
        }
        output.append("## Cómo usar estos filtros")
        output.append("")
        output.append("Pasa los códigos como parámetros en `search_consolidated_legislation`:")
        output.append("```")
        for s in suggestions[:3]:
            param = param_map.get(s['type'], 'code')
            output.append(f'{param}: "{s["code"]}"  # {s["label"]}')
        output.append("```")

        return "\n".join(output)