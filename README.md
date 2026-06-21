# RESUME CHATBOT

API REST de alto rendimiento para la gestión, almacenamiento y consulta inteligente de un Currículum Vitae, basada en el estándar [JSON Resume](https://jsonresume.org/).

## Descripción

Este proyecto implementa una solución de backend moderna para gestionar un CV individual utilizando una arquitectura de persistencia relacional optimizada y un sistema de recuperación de información (RAG) para consultas conversacionales mediante IA.

### Características Técnicas

- **Contract-First:** Validación estricta de entrada basada en el JSON Schema oficial de JSON Resume.
- **Persistencia Híbrida:** 
    - **SQLite:** Para almacenamiento estructurado de entidades (Work, Education, Skills, etc.), minimizando el tráfico y permitiendo actualizaciones granulares (`PATCH`).
    - **ChromaDB:** Base de datos vectorial embebida para búsquedas semánticas eficientes en el contenido del CV.
- **Arquitectura Asíncrona:** Construido sobre FastAPI para maximizar la concurrencia.
- **RAG Granular:** Estrategia de indexación por entidad para mejorar la precisión de las respuestas del asistente de chat.
- **MCP Servers:** 11 servidores MCP (Model Context Protocol) para acceso programático a los datos del CV.

## Stack Tecnológico

- **Lenguaje:** Python 3.12+
- **Framework API:** FastAPI
- **Validación:** Pydantic v2
- **ORM:** SQLAlchemy (SQLite)
- **Vector Store:** ChromaDB
- **LLM Orchestration:** LangChain
- **MCP Protocol:** Model Context Protocol v1.28.0

## Instalación

1. **Clonar el repositorio:**
    ```bash
    git clone https://github.com/jarivas/resume-chatbot
    cd resume-chatbot
    ```

2. **Instalar dependencias:**
    ```bash
    poetry install
    ```

3. **Instalar MCP (opcional):**
    ```bash
    poetry run pip install mcp
    ```

4. **Configurar variables de entorno:**
    ```bash
    export OPENAI_API_KEY="your-openai-api-key"
    ```

## Estructura del Proyecto

```
resume-chatbot/
├── app/
│   ├── api/                    # Endpoints REST por modelo
│   │   ├── work.py
│   │   ├── education.py
│   │   ├── skills.py
│   │   ├── volunteer.py
│   │   ├── awards.py
│   │   ├── certificates.py
│   │   ├── publications.py
│   │   ├── languages.py
│   │   ├── interests.py
│   │   ├── references.py
│   │   ├── projects.py
│   │   └── chat.py
│   ├── db/                     # Modelos SQLAlchemy
│   │   ├── base.py
│   │   ├── session.py          # Gestión de sesiones
│   │   └── models/
│   │       ├── work.py
│   │       ├── education.py
│   │       ├── skill.py
│   │       └── ...
│   ├── models/                  # Esquemas Pydantic
│   │   ├── work.py
│   │   ├── education.py
│   │   ├── skill.py
│   │   └── ...
│   └── services/               # Lógica de negocio
│       ├── work_service.py
│       ├── education_service.py
│       ├── skill_service.py
│       └── ...
├── mcp_servers/               # Servidores MCP
│   ├── work_server.py
│   ├── education_server.py
│   ├── skills_server.py
│   ├── volunteer_server.py
│   ├── awards_server.py
│   ├── certificates_server.py
│   ├── publications_server.py
│   ├── languages_server.py
│   ├── interests_server.py
│   ├── references_server.py
│   └── projects_server.py
├── tests/
│   ├── api/                    # Tests de endpoints HTTP (88 tests)
│   ├── models/                 # Tests de lógica de negocio (88 tests)
│   ├── services/               # Tests de servicios (88 tests)
)
│   └── mcp/                   # Tests de MCP servers (77 tests)
├── docs/                      # Documentación
│   ├── api.md
│   ├── tests.md
│   └── mcp_servers.md
└── pyproject.toml
```

## API Endpoints

### CRUD por Modelo

Cada modelo expone los siguientes endpoints:

#### Work (`/work`)
- `POST /work` - Crear experiencia laboral
- `GET /work/{id}` - Obtener por ID
- `GET /work` - Obtener todas
- `PATCH /work/{id}` - Actualizar parcialmente
- `DELETE /work/{id}` - Eliminar

#### Education (`/education`)
- `POST /education` - Crear educación
- `GET /education/{id}` - Obtener por ID
- `GET /education` - Obtener todas
- `PATCH /education/{id}` - Actualizar parcialmente
- `DELETE /education/{id}` - Eliminar

#### Skills (`/skills`)
- `POST /skills` - Crear habilidad
- `GET /skills/{id}` - Obtener por ID
- `GET /skills` - Obtener todas
- `PATCH /skills/{id}` - Actualizar parcialmente
- `DELETE /skills/{id}` - Eliminar

#### Volunteer (`/volunteer`)
- `POST /volunteer` - Crear experiencia de voluntariado
- `GET /volunteer/{id}` - Obtener por ID
- `GET /volunteer` - Obtener todas
- `PATCH /volunteer/{id}` - Actualizar parcialmente
- `DELETE /volunteer/{id}` - Eliminar

#### Awards (`/awards`)
- `POST /awards` - Crear premio
- `GET /awards/{id}` - Obtener por ID
- `GET /awards` - Obtener todas
- `PATCH /awards/{id}` - Actualizar parcialmente
- `DELETE /awards/{id}` - Eliminar

#### Certificates (`/certificates`)
- `POST /certificates` - Crear certificado
- `GET /certificates/{id}` - Obtener por ID
- `GET /certificates` - Obtener todas
- `PATCH /certificates/{id}` - Actualizar parcialmente
- `DELETE /certificates/{id}` - Eliminar

#### Publications (`/publications`)
- `POST /publications` - Crear publicación
- `GET /publications/{id}` - Obtener por ID
- `GET /publications` - Obtener todas
- `PATCH /publications/{id}` - Actualizar parcialmente
- `DELETE /publications/{id}` - Eliminar

#### Languages (`/languages`)
- `POST /languages` - Crear idioma
- `GET /languages/{id}` - Obtener por ID
- `GET /languages` - Obtener todas
- `PATCH /languages/{id}` - Actualizar parcialmente
- `DELETE /languages/{id}` - Eliminar

#### Interests (`/interests`)
- `POST /interests` - Crear interés
- `GET /interests/{id}` - Obtener por ID
- `GET /interests` - Obtener todas
- `PATCH /interests/{id}` - Actualizar parcialmente
- `DELETE /interests/{id}` - Eliminar

#### References (`/references`)
- `POST /references` - Crear referencia
- `GET /references/{id}` - Obtener por ID
- `GET /references` - Obtener todas
- `PATCH /references/{id}` - Actualizar parcialmente
- `DELETE /references/{id}` - Eliminar

#### Projects (`/projects`)
- `POST /projects` - Crear proyecto
- `GET /projects/{id}` - Obtener por ID
- `GET /projects` - Obtener todas
- `PATCH /projects/{id}` - Actualizar parcialmente
- `DELETE /projects/{id}` - Eliminar

### Chat (`/chat`)
- `POST /chat` - Consulta conversacional con IA

## MCP Servers

El proyecto incluye 11 servidores MCP para acceso programático a los datos del CV:

### Servidores Disponibles

- **work_server.py** - Experiencia laboral
- **education_server.py** - Educación
- **skills_server.py** - Habilidades
- **volunteer_server.py** - Voluntariado
- **awards_server.py** - Premios
- **certificates_server.py** - Certificados
- **publications_server.py** - Publicaciones
- **languages_server.py** - Idiomas
- **interests_server.py** - Intereses
- **references_server.py** - Referencias
- **projects_server.py** - Proyectos

### Herramientas por Servidor

Cada servidor MCP proporciona 3 herramientas:
- `get_{model}_by_id` - Obtener por ID
- `get_all_{model}` - Obtener todos
- `search_{model}` - Buscar por campos relevantes

### Ejecutar un Servidor MCP

```bash
python mcp_servers/work_server.py
python mcp_servers/education_server.py
# ... etc
```

### Configuración de Cliente MCP

```json
{
  "mcpServers": {
    "resume-work": {
      "command": "python",
      "args": ["mcp_servers/work_server.py"]
    },
    "resume-education": {
      "command": "python",
      "args": ["mcp_servers/education_server.py"]
    }
  }
}
```

## Ejemplos de Uso

### Crear Experiencia Laboral

```bash
curl -X POST http://localhost:8000/work \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Corp",
    "position": "Software Engineer",
    "summary": "Desarrollé software escalable",
    "highlights": ["Arquitectura de microservicios", "Optimización de rendimiento"]
  }'
```

### Consultar el CV con IA

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué experiencia tienes en desarrollo de software?"
  }'
```

### Usar MCP Server

```python
# Ejemplo de uso de MCP server
from mcp_servers.work_server import call_tool
import json

result = await call_tool("get_work_by_id", {"id": 1})
data = json.loads(result[0].text)
print(data)
```

## Tests

El proyecto incluye una suite completa de tests:

```bash
# Ejecutar todos los tests
poetry run pytest

# Ejecutar tests específicos
poetry run pytest tests/api/
poetry run pytest tests/models/
poetry run pytest tests/services/
poetry run pytest tests/mcp/

# Con coverage
poetry run pytest --cov=app --cov-report=html
```

### Cobertura de Tests

- **Total de tests:** 341 tests
    - **Tests de API:** 88 tests (11 endpoints × 8 tests)
    - **Tests de modelos:** 88 tests (11 modelos × 8 tests)
    - **Tests de servicios:** 88 tests (11 servicios × 8 tests)
    - **Tests de MCP:** 77 tests (11 servidores × 7 tests)
    - **Tests integrales:** 21 tests (chat y CV service)

## Comandos de Desarrollo

- **Instalar dependencias:** `poetry install`
- **Ejecutar tests:** `poetry run pytest`
- **Linting:** `poetry run ruff check`
- **Formato:** `poetry run ruff format`
- **Type checking:** `poetry run mypy app/`

## Convenciones

- **Async:** Todo método que interactúe con DB, Disco o LLM debe ser `async`.
- **Atomicidad:** Las operaciones de escritura son atómicas entre SQLite y ChromaDB.
- **Type Safety:** Uso de `typing` (List, Optional, Dict) en todas las capas.
- **Docstrings:** Seguir formato Google Style para cada endpoint.
- **Embedding:** Usar `text-embedding-3-small` (o similar eficiente).
- **Chunking:** Aplicar una estrategia de chunking basada en la entidad antes de enviar al vector store.

## Documentación

- **[API Documentation](docs/api.md)** - Documentación completa de la API REST
- **[Tests Documentation](docs/tests.md)** - Guía de tests y patrones
- **[MCP Servers Documentation](docs/mcp_servers.md)** - Documentación de servidores MCP

## Contribución

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Hacer tus cambios
4. Ejecutar los tests (`poetry run pytest`)
5. Hacer un Pull Request

## Licencia

MIT License - ver archivo LICENSE para más detalles.
