"""
Ejemplos unificados del framework R5.

Este módulo contiene ejemplos de uso para:
- IoC (Dependency Injection)
- Background (Task execution)
- Http (HTTP client)

Ejecutar con: uv run python examples.py
"""
import asyncio
import time
from dataclasses import dataclass
import logging

from R5.background import Background
from R5.http import Http
from R5.ioc import singleton, inject, factory


logging.basicConfig(level=logging.INFO)
# ============================================================================
# SERVICIOS DE EJEMPLO
# ============================================================================

@factory
class EmailService:
    async def send(self, to: str, subject: str) -> None:
        print(f"[EmailService] Enviando a {to}: {subject}")
        await asyncio.sleep(0.1)
        print("[EmailService] Email enviado")


@singleton
class LogService:
    def log(self, message: str) -> None:
        print(f"[LogService] {message}")


@singleton
class CacheService:
    def clear(self, prefix: str = "temp") -> None:
        print(f"[CacheService] Limpiando caché: {prefix}")
        time.sleep(0.05)
        print("[CacheService] Caché limpiado")


@dataclass
class UserDTO:
    id: int
    name: str
    email: str
    username: str


# ============================================================================
# EJEMPLOS: IoC (DEPENDENCY INJECTION)
# ============================================================================

async def demo_ioc_basic():
    """Ejemplo básico de inyección de dependencias."""
    print("\n" + "="*60)
    print("DEMO IoC: Básico")
    print("="*60 + "\n")
    
    @inject
    async def service_user(log: LogService, email: EmailService):
        log.log("Iniciando proceso")
        await email.send("user@example.com", "Bienvenido")
    
    await service_user()  # type: ignore
    print("\n✅ Inyección automática de servicios\n")


async def demo_ioc_advanced():
    """Ejemplo avanzado con múltiples servicios."""
    print("\n" + "="*60)
    print("DEMO IoC: Avanzado")
    print("="*60 + "\n")
    
    @inject
    async def complex_operation(
        log: LogService,
        email: EmailService,
        cache: CacheService
    ):
        log.log("Operación compleja iniciada")
        cache.clear("user_data")
        await email.send("admin@example.com", "Reporte generado")
        log.log("Operación completada")
    
    await complex_operation()  # type: ignore
    print("\n✅ Múltiples servicios inyectados\n")


# ============================================================================
# EJEMPLOS: BACKGROUND (TASK EXECUTION)
# ============================================================================

async def demo_background_basic():
    """Ejemplo básico de ejecución en background."""
    
    @inject
    async def process_tasks(bg: Background):
        await bg.add(lambda: print("[Task 1] Ejecutada"))
        await bg.add(lambda: print("[Task 2] Ejecutada"))
        await asyncio.sleep(0.2)
    
    await process_tasks()  # type: ignore


async def demo_background_with_ioc():
    """Ejemplo de Background con inyección IoC."""
    print("\n" + "="*60)
    print("DEMO Background: Con IoC")
    print("="*60 + "\n")
    
    @inject
    def task_with_log(log: LogService, message: str):
        log.log(f"Background task: {message}")
    
    @inject
    async def process_with_services(bg: Background):
        await bg.add(task_with_log, message="Tarea 1")
        await bg.add(task_with_log, message="Tarea 2")
        await asyncio.sleep(0.2)
    
    await process_with_services()  # type: ignore
    print("\n✅ Background con inyección IoC\n")


async def demo_background_concurrent():
    """Ejemplo de tareas concurrentes."""
    print("\n" + "="*60)
    print("DEMO Background: Concurrente")
    print("="*60 + "\n")
    
    @inject
    async def concurrent_tasks(bg: Background):
        start = time.time()
        print("Lanzando 5 tareas en paralelo...")
        
        for i in range(5):
            await bg.add(
                lambda n: time.sleep(0.2) or print(f"[Task-{n}] Completada"),
                i
            )
        
        await asyncio.sleep(1.5)
        elapsed = time.time() - start
        print(f"\n✅ 5 tareas en {elapsed:.2f}s (concurrencia)")
    
    await concurrent_tasks()  # type: ignore
    print()


# ============================================================================
# EJEMPLOS: HTTP (HTTP CLIENT)
# ============================================================================

async def demo_http_basic():
    """Ejemplo básico de HTTP client."""
    print("\n" + "="*60)
    print("DEMO Http: Básico")
    print("="*60 + "\n")
    
    @inject
    async def fetch_user(http: Http):
        result = await http.get("https://jsonplaceholder.typicode.com/users/1")
        user = result.to(UserDTO)
        
        if user:
            print(f"✅ Usuario: {user.name} ({user.email})")
    
    await fetch_user()  # type: ignore
    print()


async def demo_http_with_handlers():
    """Ejemplo de HTTP con handlers."""
    print("\n" + "="*60)
    print("DEMO Http: Con Handlers")
    print("="*60 + "\n")
    
    @inject
    async def fetch_with_handlers(http: Http):
        result = await http.get(
            "https://jsonplaceholder.typicode.com/users/999",
            on_status={
                404: lambda: print("⚠️  Usuario no encontrado"),
                200: lambda: print("✅ Usuario encontrado")
            }
        )
        print(f"Status: {result.status}")
    
    await fetch_with_handlers()  # type: ignore
    print()


async def demo_http_retry():
    """Ejemplo de HTTP con retry."""
    print("\n" + "="*60)
    print("DEMO Http: Con Retry")
    print("="*60 + "\n")
    
    @inject
    async def fetch_with_retry(http: Http):
        result = await http.retry(
            attempts=3,
            delay=0.5,
            when_status=(500, 502, 503)
        ).get("https://jsonplaceholder.typicode.com/posts/1")
        
        if result.status == 200:
            print(f"✅ Request exitosa: Status {result.status}")
    
    await fetch_with_retry()  # type: ignore
    print()


# ============================================================================
# EJEMPLOS: INTEGRACIÓN (IoC + Background + Http)
# ============================================================================

async def demo_integration_complete():
    """Ejemplo completo integrando todos los módulos."""
    print("\n" + "="*60)
    print("DEMO Integración: Completa")
    print("="*60 + "\n")
    
    @inject
    async def complete_workflow(
        bg: Background,
        http: Http,
        log: LogService,
        email: EmailService
    ):
        log.log("Iniciando workflow completo")
        
        # HTTP request
        result = await http.get("https://jsonplaceholder.typicode.com/users/1")
        user = result.to(UserDTO)
        
        if user:
            log.log(f"Usuario obtenido: {user.name}")
            
            # Background tasks
            await bg.add(
                lambda: log.log(f"Procesando datos de {user.name}")
            )
            
            async def send_email_task(u):
                await email.send(u.email, "Datos actualizados")
            
            await bg.add(send_email_task, user)
            
            await asyncio.sleep(0.3)
        
        log.log("Workflow completado")
    
    await complete_workflow()  # type: ignore
    print("\n✅ Integración completa funcionando\n")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Función principal que ejecuta todos los demos."""
    print("\n" + "="*70)
    print("EJEMPLOS UNIFICADOS - FRAMEWORK R5")
    print("="*70)
    print("\nMódulos demostrados:")
    print("  • IoC: Inyección de dependencias automática")
    print("  • Background: Ejecución de tareas en paralelo")
    print("  • Http: Cliente HTTP con pooling y retry")
    print("\n")
    
    # IoC Examples
    await demo_ioc_basic()
    await demo_ioc_advanced()
    
    # Background Examples
    await demo_background_basic()
    await demo_background_with_ioc()
    await demo_background_concurrent()
    
    # Http Examples
    await demo_http_basic()
    await demo_http_with_handlers()
    await demo_http_retry()
    
    # Integration Example
    await demo_integration_complete()
    
    print("\n" + "="*70)
    print("DEMOS COMPLETADOS")
    print("="*70)
    print("\n💡 Framework R5 - Simple, Ligero, Poderoso")
    print("  • Inyección IoC automática con @inject")
    print("  • Background tasks con anyio")
    print("  • HTTP client con pooling y retry")
    print("  • Todo integrado y fácil de usar")
    print()


if __name__ == "__main__":
    asyncio.run(main())
