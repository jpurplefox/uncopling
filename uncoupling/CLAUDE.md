# Uncoupling - Project Architecture & Coding Standards

Este proyecto sigue principios SOLID con énfasis en arquitectura por capas, DIP (Dependency Inversion) e ISP (Interface Segregation).

## Guías Rápidas al Escribir Código

### Arquitectura por Capas

**Dominio (models.py)**
- ✅ Solo lógica basada en `self` (validaciones, transformaciones)
- ❌ NO: `.save()`, `.objects.*`, llamadas a APIs, formateo UI

**Dependencias (repositories.py, gateways.py, clients.py)**
- ✅ Abstracciones técnicas (DB, APIs, archivos)
- ✅ Definir Protocol primero, luego implementación
- ✅ Retornar modelos Pydantic, NO diccionarios crudos
- ❌ NO: Exponer `response.json()` directamente

**Servicios (services.py)**
- ✅ Lógica de negocio y orquestación
- ✅ Depender de Protocols, NO de implementaciones concretas
- ✅ Usar dependency injection
- ❌ NO: Instanciar dependencias directamente

**Entrypoints (views.py, signals.py, tasks.py)**
- ✅ Validar input, llamar servicio, formatear output
- ✅ Recibir dependencias vía `@inject` decorator
- ❌ NO: Lógica de negocio en entrypoints

### Dependency Inversion (DIP)

```python
# 1. Definir Protocol (abstracción)
class QuestionRepository(Protocol):
    def save_or_update(...) -> Question: ...
    def get_by_user(self, user: MeliUser) -> list[Question]: ...

# 2. Implementación concreta
class DBQuestionRepository:
    def save_or_update(...) -> Question:
        # Django ORM aquí

# 3. Servicio depende de abstracción
class QuestionSyncService:
    def __init__(self, repository: QuestionRepository):  # ✅ Protocol
        self.repository = repository
```

### Interface Segregation (ISP)

- ✅ Protocols pequeños (1 responsabilidad, max 5-7 métodos)
- ✅ Segregar por caso de uso
- ❌ NO crear "mega-protocols" con muchos métodos

```python
# ✅ CORRECTO - Segregado
class MeliQuestionGateway(Protocol):
    def get_questions(...) -> list[MeliQuestion]: ...

class MeliOrderGateway(Protocol):
    def get_orders(...) -> list[Order]: ...

# ❌ INCORRECTO - Todo en uno
class MeliClient(Protocol):
    def get_questions(...): ...
    def get_orders(...): ...
    def get_items(...): ...
    # ... 10 métodos más
```

### Dependency Injection

```python
# Container (containers.py)
class QuestionContainer(containers.DeclarativeContainer):
    meli_container = providers.Container(MeliContainer)  # Reutilizar
    question_repository = providers.Singleton(DBQuestionRepository)
    meli_gateway = providers.Singleton(
        MeliQuestionAPIGateway,
        meli_client=meli_container.meli_client
    )

# Entrypoint (views.py, signals.py)
@inject
def questions_list(
    request,
    repository: QuestionRepository = Provide[QuestionContainer.question_repository]
):
    questions = repository.get_by_user(request.user.meliuser)
    # ...

# Wiring (apps.py)
def ready(self):
    import questions.signals  # noqa: F401
    from questions.containers import question_container
    question_container.wire(modules=['questions.views', 'questions.signals'])
```

### Testing

```python
# Implementación en memoria para tests
class InMemoryQuestionRepository:
    def __init__(self):
        self._questions = {}

# Mock con validación de Protocol
from unittest.mock import create_autospec

@pytest.fixture
def mock_gateway():
    return create_autospec(MeliQuestionGateway, instance=True)

# Test rápido (sin DB, sin API)
def test_sync_questions(question_repository, mock_gateway, sample_token):
    # Arrange - datos inline para legibilidad
    meli_user = MeliUser(id=12345, ...)
    service = QuestionSyncService(question_repository, mock_gateway)

    # Act & Assert
    # Test corre en <0.1s
```

### Manejo de Excepciones

- ❌ NO usar `try/except Exception` genérico
- ✅ Dejar que Django maneje las excepciones (se loguea y muestra 500)
- ✅ Solo catchear excepciones específicas si vas a hacer algo útil con ellas

```python
# ❌ INCORRECTO
try:
    service.do_something()
except Exception as e:  # Demasiado genérico
    logger.error(f"Error: {e}")

# ✅ CORRECTO - Dejar escalar
def sync_questions(...):
    questions = self.meli_gateway.get_questions(token)  # Puede fallar
    # Django maneja la excepción automáticamente
```

### Fixtures en Tests

- ✅ Fixtures para infraestructura: repositories, mocks, tokens
- ❌ NO crear fixtures de datos de dominio
- ✅ Datos inline en tests para mejor legibilidad

```python
# ✅ CORRECTO - Fixture de infraestructura
@pytest.fixture
def sample_token():
    return MeliToken(user_id=12345, access_token='test', ...)

# ✅ CORRECTO - Datos inline en test
def test_sync_questions(sample_token):
    meli_user = MeliUser(id=12345, user=User(...))  # Inline
    question = MeliQuestion(**{  # Inline
        'id': 111,
        'text': '¿Tiene garantía?',
        # ...
    })
```

## Código Legacy

El proyecto tiene código legacy que no sigue estos estándares. Está bien. **El código nuevo debe seguir estas prácticas**. Al refactorizar código existente, aplicar estos principios cuando sea apropiado.

## Ejemplos en el Proyecto

- `my_auth/`: Implementación completa de DIP + ISP + DI
- `questions/`: Implementación completa de DIP + ISP + DI
- Usar estos módulos como referencia para nuevos módulos

## Patrón General para Nuevo Módulo

1. Definir Protocols para dependencias externas
2. Crear implementaciones concretas (DB, API)
3. Crear implementaciones en memoria (tests)
4. Crear container de DI
5. Wire container en apps.py
6. Escribir tests con in-memory implementations
