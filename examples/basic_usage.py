#!/usr/bin/env python3
"""
Ejemplos básicos de uso del MCP BOE.

Este script muestra cómo usar las principales funcionalidades
del MCP BOE de forma directa, sin pasar por Claude.
"""

import asyncio
import json
from datetime import datetime, timedelta

from mcp_boe import BOEHTTPClient, BOEMCPServer
from mcp_boe.tools.legislation import LegislationTools
from mcp_boe.tools.summaries import SummaryTools
from mcp_boe.tools.auxiliary import AuxiliaryTools
from mcp_boe.tools.analysis import AnalysisTools


async def example_search_legislation():
    """Ejemplo: Buscar legislación consolidada."""
    print("🔍 Ejemplo: Búsqueda de legislación consolidada")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Buscar la Ley 40/2015 (Régimen Jurídico del Sector Público)
        print("Buscando 'Ley 40/2015'...")
        results = await tools.search_consolidated_legislation({
            "query": "Ley 40/2015",
            "limit": 3
        })
        
        for result in results:
            print(result.text)
            print()


async def example_get_law_details():
    """Ejemplo: Obtener detalles de una norma específica."""
    print("📜 Ejemplo: Detalles de norma específica")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Obtener detalles de la Constitución Española
        print("Obteniendo detalles de la Constitución Española...")
        results = await tools.get_consolidated_law({
            "law_id": "BOE-A-1978-31229",  # Constitución Española
            "include_metadata": True,
            "include_analysis": True,
            "include_full_text": False
        })
        
        for result in results:
            # Mostrar solo los primeros 1000 caracteres para no saturar
            text = result.text
            if len(text) > 1000:
                text = text[:1000] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_get_law_structure():
    """Ejemplo: Obtener estructura de una norma."""
    print("📑 Ejemplo: Estructura de norma")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)
        
        # Obtener estructura de la Ley 40/2015
        print("Obteniendo estructura de la Ley 40/2015...")
        results = await tools.get_law_structure({
            "law_id": "BOE-A-2015-10566"  # Ley 40/2015
        })
        
        for result in results:
            print(result.text)
            print()


async def example_get_boe_summary():
    """Ejemplo: Obtener sumario del BOE."""
    print("📰 Ejemplo: Sumario del BOE")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)
        
        # Obtener sumario de una fecha reciente conocida
        test_date = "20240529"  # 29 de mayo de 2024 (fecha de ejemplo)
        print(f"Obteniendo sumario del BOE para {test_date}...")
        
        results = await tools.get_boe_summary({
            "date": test_date,
            "max_items": 10  # Limitar para el ejemplo
        })
        
        for result in results:
            # Mostrar solo los primeros 1500 caracteres
            text = result.text
            if len(text) > 1500:
                text = text[:1500] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_search_recent_boe():
    """Ejemplo: Buscar en BOE reciente."""
    print("🔍 Ejemplo: Búsqueda en BOE reciente")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)
        
        print("Buscando 'Real Decreto' en los últimos 7 días...")
        results = await tools.search_recent_boe({
            "days_back": 7,
            "search_terms": "Real Decreto"
        })
        
        for result in results:
            print(result.text)
            print()


async def example_get_departments():
    """Ejemplo: Obtener tabla de departamentos."""
    print("🏛️ Ejemplo: Tabla de departamentos")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)
        
        print("Buscando departamentos que contengan 'Ministerio'...")
        results = await tools.get_departments_table({
            "search_term": "Ministerio",
            "limit": 10
        })
        
        for result in results:
            # Mostrar solo los primeros 1000 caracteres
            text = result.text
            if len(text) > 1000:
                text = text[:1000] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_get_legal_ranges():
    """Ejemplo: Obtener rangos normativos."""
    print("⚖️ Ejemplo: Rangos normativos")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)
        
        print("Obteniendo tabla de rangos normativos...")
        results = await tools.get_legal_ranges_table({})
        
        for result in results:
            print(result.text)
            print()


async def example_search_auxiliary():
    """Ejemplo: Búsqueda en tablas auxiliares."""
    print("🔍 Ejemplo: Búsqueda en tablas auxiliares")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)
        
        print("Buscando 'Hacienda' en todas las tablas auxiliares...")
        results = await tools.search_auxiliary_data({
            "query": "Hacienda"
        })
        
        for result in results:
            print(result.text)
            print()


async def example_get_code_description():
    """Ejemplo: Obtener descripción de código."""
    print("🔍 Ejemplo: Descripción de código")
    print("=" * 60)
    
    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)
        
        print("Obteniendo descripción del código '7723'...")
        results = await tools.get_code_description({
            "code": "7723"  # Jefatura del Estado
        })
        
        for result in results:
            print(result.text)
            print()


async def example_compare_law_versions():
    """Ejemplo: Comparar versiones de una norma entre dos fechas."""
    print("🔄 Ejemplo: Comparación de versiones")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)

        print("Comparando Ley 40/2015 entre 2016 y 2021...")
        results = await tools.compare_law_versions({
            "law_id": "BOE-A-2015-10566",
            "from_date": "20160101",
            "to_date": "20210101",
        })

        for result in results:
            text = result.text
            if len(text) > 1500:
                text = text[:1500] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_search_law_articles():
    """Ejemplo: Buscar artículos por texto dentro de una norma."""
    print("🔍 Ejemplo: Búsqueda en artículos")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)

        print("Buscando 'competencia' en la Ley 40/2015...")
        results = await tools.search_law_articles({
            "law_id": "BOE-A-2015-10566",
            "query": "competencia",
            "limit": 5,
        })

        for result in results:
            print(result.text)
            print()


async def example_get_law_metadata():
    """Ejemplo: Obtener metadatos ligeros de una norma."""
    print("📋 Ejemplo: Metadatos de norma")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)

        print("Obteniendo metadatos de la Ley 40/2015...")
        results = await tools.get_law_metadata({"law_id": "BOE-A-2015-10566"})

        for result in results:
            print(result.text)
            print()


async def example_list_related_laws():
    """Ejemplo: Listar normas relacionadas con control granular."""
    print("🔗 Ejemplo: Normas relacionadas")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = LegislationTools(client)

        print("Normas que derogan o son derogadas por Ley 40/2015...")
        results = await tools.list_related_laws({
            "law_id": "BOE-A-2015-10566",
            "include_derogating": True,
            "include_development": False,
            "include_references": False,
        })

        for result in results:
            print(result.text)
            print()


async def example_get_boe_summary_range():
    """Ejemplo: Sumario BOE para un rango de fechas."""
    print("📰 Ejemplo: Sumario de rango")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)

        print("Obteniendo publicaciones BOE del 27 al 31 de mayo de 2024...")
        results = await tools.get_boe_summary_range({
            "from_date": "20240527",
            "to_date": "20240531",
            "max_items": 10,
        })

        for result in results:
            text = result.text
            if len(text) > 1500:
                text = text[:1500] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_watch_boe_changes():
    """Ejemplo: Radar normativo por palabras clave."""
    print("📡 Ejemplo: Radar normativo")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)

        print("Buscando 'inteligencia artificial' en el BOE de los últimos 30 días...")
        results = await tools.watch_boe_changes({
            "days_back": 30,
            "keywords": "inteligencia artificial",
            "max_items": 10,
        })

        for result in results:
            print(result.text)
            print()


async def example_group_summary_by_department():
    """Ejemplo: Agrupar publicaciones por departamento."""
    print("🏛️ Ejemplo: Publicaciones por departamento")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = SummaryTools(client)

        recent_end = datetime.now().strftime("%Y%m%d")
        recent_start = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        print(f"Agrupando publicaciones del {recent_start} al {recent_end} por departamento...")
        results = await tools.group_summary_by_department({
            "from_date": recent_start,
            "to_date": recent_end,
            "max_items_per_dept": 3,
        })

        for result in results:
            text = result.text
            if len(text) > 2000:
                text = text[:2000] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_search_departments_advanced():
    """Ejemplo: Búsqueda avanzada de departamentos."""
    print("🏛️ Ejemplo: Búsqueda avanzada de departamentos")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)

        print("Buscando secretarías de estado...")
        results = await tools.search_departments_advanced({
            "search_term": "Secretaría de Estado",
            "active_only": True,
            "limit": 10,
        })

        for result in results:
            print(result.text)
            print()


async def example_list_topics_for_law():
    """Ejemplo: Materias de una norma concreta."""
    print("📚 Ejemplo: Materias de una norma")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)

        print("Listando materias de la Ley 40/2015...")
        results = await tools.list_topics_for_law({"law_id": "BOE-A-2015-10566"})

        for result in results:
            print(result.text)
            print()


async def example_suggest_auxiliary_filters():
    """Ejemplo: Sugerencias de filtros auxiliares desde texto libre."""
    print("💡 Ejemplo: Sugerencias de filtros")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AuxiliaryTools(client)

        print("Buscando sugerencias para 'medio ambiente'...")
        results = await tools.suggest_auxiliary_filters({
            "query": "medio ambiente",
            "max_suggestions": 8,
        })

        for result in results:
            print(result.text)
            print()


async def example_summarize_law_sections():
    """Ejemplo: Resumen estructurado de una norma."""
    print("📝 Ejemplo: Resumen de secciones")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AnalysisTools(client)

        print("Resumiendo secciones de la Ley 40/2015...")
        results = await tools.summarize_law_sections({"law_id": "BOE-A-2015-10566"})

        for result in results:
            text = result.text
            if len(text) > 1500:
                text = text[:1500] + "...\n\n[Contenido truncado para el ejemplo]"
            print(text)
            print()


async def example_paginate_law_text():
    """Ejemplo: Paginación de texto de una norma."""
    print("📄 Ejemplo: Paginación de texto")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AnalysisTools(client)

        print("Obteniendo primera página de la Ley 40/2015 (2000 caracteres)...")
        results = await tools.paginate_law_text({
            "law_id": "BOE-A-2015-10566",
            "max_chars": 2000,
        })

        for result in results:
            print(result.text)
            print()


async def example_normalize_boe_reference():
    """Ejemplo: Normalizar referencias textuales a normas."""
    print("🔤 Ejemplo: Normalización de referencias")
    print("=" * 60)

    async with BOEHTTPClient() as client:
        tools = AnalysisTools(client)

        references = [
            "Ley 40/2015",
            "Real Decreto 1/2020",
            "BOE-A-2015-10566",
            "BOE del 3 de mayo de 2024",
            "Ley Orgánica 3/2018",
        ]

        for ref in references:
            results = await tools.normalize_boe_reference({"reference_text": ref})
            print(f"  «{ref}» →")
            print(f"    {results[0].text.strip()}")
            print()


async def run_all_examples():
    """Ejecuta todos los ejemplos."""
    print("🚀 Ejecutando todos los ejemplos del MCP BOE")
    print("=" * 80)
    print()

    examples = [
        ("Búsqueda de legislación", example_search_legislation),
        ("Detalles de norma", example_get_law_details),
        ("Estructura de norma", example_get_law_structure),
        ("Comparar versiones", example_compare_law_versions),
        ("Buscar artículos", example_search_law_articles),
        ("Metadatos de norma", example_get_law_metadata),
        ("Normas relacionadas", example_list_related_laws),
        ("Sumario del BOE", example_get_boe_summary),
        ("Búsqueda reciente BOE", example_search_recent_boe),
        ("Sumario por rango", example_get_boe_summary_range),
        ("Radar normativo", example_watch_boe_changes),
        ("Publicaciones por dpto.", example_group_summary_by_department),
        ("Tabla de departamentos", example_get_departments),
        ("Rangos normativos", example_get_legal_ranges),
        ("Búsqueda auxiliares", example_search_auxiliary),
        ("Descripción de código", example_get_code_description),
        ("Departamentos avanzado", example_search_departments_advanced),
        ("Materias de norma", example_list_topics_for_law),
        ("Sugerencias de filtros", example_suggest_auxiliary_filters),
        ("Resumen de secciones", example_summarize_law_sections),
        ("Paginación de texto", example_paginate_law_text),
        ("Normalizar referencia", example_normalize_boe_reference),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n{'='*20} {i}/{len(examples)}: {name} {'='*20}")
            await func()
            print(f"✅ Completado: {name}")
            
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
        
        # Pausa entre ejemplos para no saturar la API
        if i < len(examples):
            print(f"\n⏸️ Pausa de 2 segundos antes del siguiente ejemplo...")
            await asyncio.sleep(2)
    
    print("\n" + "=" * 80)
    print("🎉 Todos los ejemplos completados")


async def interactive_demo():
    """Demo interactivo del MCP BOE."""
    print("🎮 Demo interactivo del MCP BOE")
    print("=" * 50)
    print()
    
    async with BOEHTTPClient() as client:
        leg_tools = LegislationTools(client)
        sum_tools = SummaryTools(client)
        aux_tools = AuxiliaryTools(client)
        
        while True:
            print("\n📋 Opciones disponibles:")
            print("1. Buscar legislación")
            print("2. Obtener sumario BOE reciente")
            print("3. Buscar departamentos")
            print("4. Obtener código específico")
            print("5. Salir")
            
            try:
                choice = input("\nElige una opción (1-5): ").strip()
                
                if choice == "1":
                    query = input("Ingresa términos de búsqueda: ").strip()
                    if query:
                        print(f"\n🔍 Buscando '{query}'...")
                        results = await leg_tools.search_consolidated_legislation({
                            "query": query,
                            "limit": 5
                        })
                        for result in results:
                            print(result.text)
                
                elif choice == "2":
                    # Usar fecha reciente (algunos días atrás para asegurar disponibilidad)
                    recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
                    print(f"\n📰 Obteniendo sumario BOE reciente ({recent_date})...")
                    results = await sum_tools.get_boe_summary({
                        "date": recent_date,
                        "max_items": 5
                    })
                    for result in results:
                        text = result.text
                        if len(text) > 1000:
                            text = text[:1000] + "...\n[Contenido truncado]"
                        print(text)
                
                elif choice == "3":
                    search = input("Buscar departamentos (o Enter para todos): ").strip()
                    print(f"\n🏛️ Buscando departamentos...")
                    args = {"limit": 10}
                    if search:
                        args["search_term"] = search
                    
                    results = await aux_tools.get_departments_table(args)
                    for result in results:
                        text = result.text
                        if len(text) > 800:
                            text = text[:800] + "...\n[Contenido truncado]"
                        print(text)
                
                elif choice == "4":
                    code = input("Ingresa código a buscar (ej: 7723): ").strip()
                    if code:
                        print(f"\n🔍 Buscando código '{code}'...")
                        results = await aux_tools.get_code_description({
                            "code": code
                        })
                        for result in results:
                            print(result.text)
                
                elif choice == "5":
                    print("\n👋 ¡Hasta luego!")
                    break
                
                else:
                    print("\n❌ Opción inválida. Por favor elige 1-5.")
            
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrumpido. ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


async def connectivity_test():
    """Prueba básica de conectividad."""
    print("🔧 Prueba de conectividad con la API del BOE")
    print("=" * 50)
    
    try:
        async with BOEHTTPClient(timeout=10) as client:
            print("1. Probando conexión básica...")
            
            # Test básico
            health = await client.health_check()
            if health:
                print("   ✅ Conectividad: OK")
            else:
                print("   ❌ Conectividad: FALLO")
                return
            
            # Test de búsqueda simple
            print("2. Probando búsqueda simple...")
            result = await client.search_legislation(limit=1)
            if result and result.get('data'):
                print("   ✅ Búsqueda: OK")
            else:
                print("   ❌ Búsqueda: FALLO")
                return
            
            print("\n🎉 ¡Todas las pruebas pasaron! El MCP debería funcionar correctamente.")
    
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")


# ============================================================================
# UTILIDADES PARA TESTING
# ============================================================================

def print_separator(title: str):
    """Imprime un separador visual con título."""
    width = 80
    padding = (width - len(title) - 2) // 2
    print("=" * width)
    print(f"{'=' * padding} {title} {'=' * padding}")
    print("=" * width)


async def quick_test():
    """Prueba rápida de funcionalidades básicas."""
    print_separator("PRUEBA RÁPIDA DEL MCP BOE")
    
    try:
        async with BOEHTTPClient() as client:
            # Test 1: Conectividad
            print("\n1️⃣ Probando conectividad...")
            health = await client.health_check()
            print(f"   Resultado: {'✅ OK' if health else '❌ FALLO'}")
            
            if not health:
                print("   ⚠️ Sin conectividad. Saltando otras pruebas.")
                return
            
            # Test 2: Búsqueda simple
            print("\n2️⃣ Probando búsqueda de legislación...")
            try:
                tools = LegislationTools(client)
                results = await tools.search_consolidated_legislation({
                    "query": "Constitución",
                    "limit": 1
                })
                print(f"   Resultado: ✅ Encontrados {len(results)} resultados")
            except Exception as e:
                print(f"   Resultado: ❌ Error - {e}")
            
            # Test 3: Tablas auxiliares
            print("\n3️⃣ Probando tablas auxiliares...")
            try:
                aux_tools = AuxiliaryTools(client)
                results = await aux_tools.get_code_description({
                    "code": "7723"
                })
                print(f"   Resultado: ✅ Código encontrado")
            except Exception as e:
                print(f"   Resultado: ❌ Error - {e}")
            
            print(f"\n{'='*30} FIN DE PRUEBAS {'='*30}")
    
    except Exception as e:
        print(f"❌ Error general: {e}")


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def main():
    """Función principal del script de ejemplos."""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        # Mostrar menú interactivo
        print("🚀 Ejemplos del MCP BOE")
        print("=" * 30)
        print("1. Ejecutar todos los ejemplos")
        print("2. Demo interactivo")
        print("3. Prueba de conectividad")
        print("4. Prueba rápida")
        print("5. Salir")
        
        choice = input("\nElige una opción (1-5): ").strip()
        mode_map = {
            "1": "all",
            "2": "interactive", 
            "3": "connectivity",
            "4": "quick",
            "5": "exit"
        }
        mode = mode_map.get(choice, "exit")
    
    if mode == "all":
        print("🚀 Ejecutando todos los ejemplos...")
        asyncio.run(run_all_examples())
    
    elif mode == "interactive":
        print("🎮 Iniciando demo interactivo...")
        asyncio.run(interactive_demo())
    
    elif mode == "connectivity":
        print("🔧 Ejecutando prueba de conectividad...")
        asyncio.run(connectivity_test())
    
    elif mode == "quick":
        print("⚡ Ejecutando prueba rápida...")
        asyncio.run(quick_test())
    
    elif mode == "exit":
        print("👋 ¡Hasta luego!")
        return
    
    else:
        # Modos específicos por línea de comandos
        mode_functions = {
            "search": example_search_legislation,
            "details": example_get_law_details,
            "structure": example_get_law_structure,
            "summary": example_get_boe_summary,
            "recent": example_search_recent_boe,
            "departments": example_get_departments,
            "ranges": example_get_legal_ranges,
            "auxiliary": example_search_auxiliary,
            "code": example_get_code_description,
        }
        
        if mode in mode_functions:
            print(f"🔍 Ejecutando ejemplo: {mode}")
            asyncio.run(mode_functions[mode]())
        else:
            print(f"❌ Modo desconocido: {mode}")
            print("Modos disponibles: all, interactive, connectivity, quick")
            print("O ejemplos específicos: search, details, structure, summary, recent, departments, ranges, auxiliary, code")


if __name__ == "__main__":
    main()