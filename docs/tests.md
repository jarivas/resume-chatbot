# Documentación de Tests de Resume Chatbot

## Cobertura de Tests

El proyecto tiene una suite completa de tests que cubren todos los endpoints, servicios y servidores MCP.

## Estructura de Tests

```
tests/
├── api/                      # Tests de endpoints HTTP (88 tests)
│   ├── test_work.py
│   ├── test_education.py
│   ├── test_skills.py
│   ├── test_volunteer.py
│   ├── test_awards.py
│   ├── test_certificates.py
│   ├── test_publications.py
│   ├── test_languages.py
│   ├── test_interests.py
│   ├── test_references.py
│   └── test_projects.py
├── models/                    # Tests de lógica de negocio (88 tests)
│   ├── test_work.py
│   ├── test_education.py
│   ├── test_skills.py
│   ├── test_volunteer.py
│   ├── test_awards.py
│   ├── test_certificates.py
│   ├── test_publications.py
│   ├── test_languages.py
│   ├── test_interests.py
│   ├── test_references.py
│   └── test_projects.py
├── services/                  # Tests de servicios (88 tests)
│   ├── test_work_service.py
│   ├── test_education_service.py
│   ├── test_skill_service.py
│   ├── test_volunteer_service.py
│   ├── test_award_service.py
│   ├── test_certificate_service.py
│   ├── test_publication_service.py
│   ├── test_language_service.py
│   ├── test_interest_service.py
│   ├── test_reference_service.py
│   └── test_project_service.py
├── mcp/                       # Tests de servidores MCP (77 tests)
│   ├── test_work_server.py
│   ├── test_education_server.py
│   ├── test_skills_server.py
│   ├── test_volunteer_server.py
│   ├── test_awards_server.py
│   ├── test_certificates_server.py
│   ├── test_publications_server.py
│   ├── test_languages_server.py
│   ├── test_interests_server.py
│   ├── test_references_server.py
│   └── test_projects_server.py
├── test_all_endpoints.py    # Tests integrales (7 tests)
├── test_api.py               # Tests de API complejos (5 tests)
├── test_chat.py              # Tests de chat (4 tests)
└── test_cv_service.py        # Tests de servicio legacy (4 tests)
```

## Tests por Categoría

### Tests de API (`tests/api/`)

Cada archivo contiene 8 tests por endpoint:

1. **test_{model}_post_endpoint** - Prueba POST /{model}
2. **test_{model}_get_by_id_endpoint** - Prueba GET /{model}/{id}
3. **test_{model}_get_all_endpoint** - Prueba GET /{model}
4. **test_{model}_patch_endpoint** - Prueba PATCH /{model}/{id}
5. **test_{model}_delete_endpoint** - Prueba DELETE /{model}/{id}
6. **test_{model}_get_not_found_endpoint** - Prueba 404 al obtener inexistente
7. **test_{model}_patch_not_found_endpoint** - Prueba 404 al actualizar inexistente
8. **test_{model}_delete_not_found_endpoint** - Prueba 404 al eliminar inexistente

### Tests de Modelos (`tests/models/`)

Cada archivo contiene 8 tests por entidad:

1. **test_create_{model}** - Prueba creación de entidad
2. **test_get_{model}** - Prueba obtención por ID
3. **test_get_all_{model}** - Prueba obtención de todos
4. **test_update_{model}** - Prueba actualización
5. **test_delete_{model}** - Prueba eliminación
6. **test_get_{model}_not_found** - Prueba error 404 al obtener inexistente
7. **test_update_{model}_not_found** - Prueba error 404 al actualizar inexistente
8. **test_delete_{model}_not_found** - Prueba error 404 al eliminar inexistente

### Tests de Servicios (`tests/services/`)

Cada archivo contiene 8 tests porser servicio:

1. **test_{model}_service_create** - Prueba creación
2. **test_{model}_service_get** - Prueba obtención por ID
3. **test_{model}_service_get_all** - Prueba obtención de todos
4. **test_{model}_service_update** - Prueba actualización
5. **test_{model}_service_delete** - Prueba eliminación
6. **test_{model}_service_indexing** - Prueba indexado en ChromaDB
7. **test_{model}_service_delete_indexing** - Prueba eliminación del índice

### Tests de MCP (`tests/mcp/`)

Cada archivo contiene 7 tests por servidor MCP:

1. **test_{model}_server_list_tools** - Verifica herramientas disponibles
2. **test_{model}_server_get_by_id** - Prueba obtención por ID
3. **test_{model}_server_get_by_id_not_found** - Prueba error 404
4. **test_{model}_server_get_all** - Prueba obtención de todos
5. **test_{model}_server_search** - Prueba búsqueda
6. **test_{model}_server_unknown_tool** - Prueba error de herramienta desconocida
7. **test_{model}_server_empty_{list_field}** - Prueba campos de lista vacíos

## Ejecutar Tests

### Ejecutar todos los tests

```bash
poetry run pytest
```

### Ejecutar tests por categoría

```bash
# Tests de API
poetry run pytest tests/api/

# Tests de modelos
poetry run pytest tests/models/

# Tests de servicios
poetry run pytest tests/services/

# Tests de MCP
poetry run pytest tests/mcp/

# Tests integrales
poetry run pytest tests/test_all_endpoints.py
```

### Ejecutar tests específicos

```bash
# Tests de Work
poetry run pytest tests/api/test_work.py
poetry run pytest tests/models/test_work.py
poetry run pytest tests/services/test_work_service.py
poetry run pytest tests/mcp/test_work_server.py

# Tests de Education
poetry run pytest tests/api/test_education.py
poetry run pytest tests/models/test_education.py
poetry run pytest tests/services/test_education_service.py
poetry run pytest tests/mcp/test_education_server.py
```

### Ejecutar tests con verbosidad

```bash
poetry run pytest -v                    # Verbose
poetry run pytest -s                    # Short output
poetry run pytest --tb=short          # Traceback corto
poetry run pytest --cov=app --cov-report=html  # Coverage
```

## Cobertura

- **Total de tests:** 341 tests
- **Tests de API:** 88 tests (11 endpoints × 8 tests)
- **Tests de modelos:** 88 tests (11 modelos × 8 tests)
- **Tests de servicios:** 88 tests (11 servicios × 8 tests)
- **Tests de MCP:** 77 tests (11 servidores × 7 tests)
- **Tests integrales:** 21 tests

## Fixtures Comunes

Los tests utilizan fixtures comunes para configurar el entorno:

- **db_session:** Crea una base de datos SQLite en memoria
- **mock_chroma:** Mock de ChromaDB con métodos async
- **mock_embeddings:** Mock de embeddings de OpenAI
- **{model}_service:** Servicio del modelo específico
- **test_client:** Cliente HTTP async para pruebas de API

## Convenciones de Tests

1. **Atomicidad:** Las operaciones de escritura son atómicas entre SQLite y ChromaDB
2. **Aislamiento:** Se usan mocks para aislar la lógica de negocio de las dependencias externas
3. **Validación:** Se verifican los códigos de estado HTTP (200, 201, 204, 404, 422, 500)
4. **Datos:** Se verifican que los datos se persistan correctamente y se pueden recuperar
5. **Indexado:** Se verifica que ChromaDB es llamado correctamente para indexar y eliminar

## Patrones de Tests

### Patrón de Test CRUD

```python
@pytest.mark.asyncio
async def test_create_{model}(test_client: AsyncClient):
    data = {...}
    response = await test_client.post("/{model}", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["field"] == expected_value

@pytest.mark.asyncio
async def test_get_{model}(test_client: AsyncClient):
    response = await test_client.get("/{model}/{id}")
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == id

@pytest.mark.asyncio
async def test_update_{model}(test_client: AsyncClient):
    update_data = {...}
    response = await test_client.patch("/{model}/{id}", json=update_data)
    assert response.status_code == 200
    result = response.json()
    assert result["field"] == updated_value

@pytest.mark.asyncio
async def test_delete_{model}(test_client: AsyncClient):
    response = await test_client.delete("/{model}/{id}")
    assert response.status_code == 204
```

### Patrón de Test de Servicio

```python
@pytest.mark.asyncio
async def test_{model}_service_create(service: {Model}Service):
    data = {Model}Item(...)
    created = await service.create_{model}(data)
    assert created is not None
    assert created.field == expected_value

@pytest.mark.asyncio
async def test_{model}_service_indexing(service: {Model}Service, mock_chroma):
    data = {Model}Item(...)
    created = await service.create_{model}(data)
    assert mock_chroma.aadd_texts.called
```

### Patrón de Test de MCP

```python
@pytest.mark.asyncio
async def test_{model}_server_get_by_id():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_entity = Model(id=1, field="value")
    mock_result.scalar_one_or_none.return_value = mock_entity
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.{model}_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.{model}_server import call_tool
        
        result = await call_tool("get_{model}_by_id", {"id": 1})
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["field"] == "value"
```

## Errores Esperados

Los tests verifican los siguientes escenarios:

1. **Creación exitosa:** POST devuelve 201 y datos correctos
2. **Lectura exitosa:** GET por ID devuelve 200 y datos correctos
3. **Lectura de todos:** GET devuelve 200 y lista de datos
4. **Actualización exitosa:** PATCH devuelve 200 y datos actualizados
5. **Eliminación exitosa:** DELETE devuelve 204
6. **Error 404:** Recursos inexistentes devuelven 404
7. **Error 422:** Datos inválidos devuelven 422
8. **Indexado ChromaDB:** Se llama aadd_texts al crear
9. **Eliminación ChromaDB:** Se llama adelete al eliminar
10. **Persistencia SQLite:** Los datos se guardan correctamente en SQLite
11. **Herramientas MCP:** Los servidores MCP listan las herramientas correctas
12. **Búsqueda MCP:** Las búsquedas funcionan correctamente

## Testing MCP Servers

Los tests de MCP utilizan un patrón especial de mocking para simular la conexión a la base de datos:

```python
# Crear mock de sesión
mock_session = AsyncMock(spec=AsyncSession)

# Crear mock de resultado
mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = mock_entity
mock_session.execute.return_value = mock_result

# Crear generador async para mocking
async def mock_get_async_session():
    yield mock_session

# Aplicar patch
with patch('mcp_servers.{model}_server.get_async_session', side_effect=mock_get_async_session):
    from mcp_servers.{model}_server import call_tool
    
    result = await call_tool("get_{model}_by_id", {"id": 1})
    # Validar resultado
```

## Ejemplos de Tests

### Test de API

```python
@pytest.mark.asyncio
async def test_work_post_endpoint(test_client: AsyncClient):
    data = {
        "name": "Tech Corp",
        "position": "Software Engineer",
        "summary": "Developed software",
        "highlights": ["Python", "FastAPI"]
    }
    response = await test_client.post("/work", json=data)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Tech Corp"
    assert result["position"] == "Software Engineer"
```

### Test de Servicio

```python
@pytest.mark.asyncio
async def test_work_service_create(work_service: WorkService, mock_chroma):
    data = WorkItem(
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights=["Python", "FastAPI"]
    )
    created = await work_service.create_work(data)
    assert created is not None
    assert created.name == "Tech Corp"
    assert mock_chroma.aadd_texts.called
```

### Test de MCP

```python
@pytest.mark.asyncio
async def test_work_server_get_by_id():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_work = Work(
        id=1,
        name="Tech Corp",
        position="Software Engineer",
        summary="Developed software",
        highlights="Python|FastAPI",
        start_date="2020-01",
        end_date="2023-12"
    )
    mock_result.scalar_one_or_none.return_value = mock_work
    mock_session.execute.return_value = mock_result
    
    async def mock_get_async_session():
        yield mock_session
    
    with patch('mcp_servers.work_server.get_async_session', side_effect=mock_get_async_session):
        from mcp_servers.work_server import call_tool
        
        result = await call_tool("get_work_by_id", {"id": 1})
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["company"] == "Tech Corp"
        assert isinstance(data["highlights"], list)
        assert len(data["highlights"]) == 2
```

## Troubleshooting

### Issues Comunes

1. **DeprecationWarning de httpx**
   - Solución: Usar `ASGITransport(app=...)` en lugar de `AsyncClient(app=...)`

2. **ImportError de MCP**
   - Solución: Instalar MCP con `poetry run pip install mcp`

3. **Database session errors**
   - Solución: Crear generador async para mocking de sesiones

4. **Async mocking issues**
   - Solución: Usar `AsyncMock` de `unittest.mock` para objetos async
