# Roles de IA para el Proyecto resume-chatbot

Como asistente de codificación, debes aplicar estos principios estrictos:

- **Data Strategy:** Prioriza la normalización relacional (SQLite) sobre el almacenamiento de blobs. El esquema JSON Resume se usa solo como contrato de entrada.
- **RAG Granular:** No indexar el CV completo. Cada entidad (Work, Education, Skills) debe ser un documento independiente en ChromaDB con metadatos asociados para permitir filtrado preciso.
- **API Design:** Implementar endpoints RESTful con soporte para `PATCH` a nivel de entidad.
- **Error Handling:** Validación estricta usando Pydantic v2. Si el esquema no coincide, devolver `422 Unprocessable Entity` detallando el error.
- **Testing:** Todo endpoint requiere tests de integración que validen:
    1. La persistencia en SQLite.
    2. La actualización del índice vectorial en ChromaDB.

## Comandos de Desarrollo

- **Instalar dependencias:** `poetry install`
- **Ejecutar tests:** `poetry run pytest`
- **Linting:** `poetry run ruff check`
- **Formato:** `poetry run ruff format`
- **Generar modelos desde JSON Schema:** `poetry run datamodel-codegen --input <schema.json> --output app/models/`

## Convenciones

- **Async:** Todo método que interactúe con DB, Disco o LLM debe ser `async`.
- **Atomicidad:** Las operaciones de escritura deben ser atómicas entre SQLite y ChromaDB (usar patrón Unit of Work).
- **Type Safety:** Uso de `typing` (List, Optional, Dict) en todas las capas.
- **Docstrings:** Seguir formato Google Style para cada endpoint.
- **Embedding:** Usar `text-embedding-3-small` (o similar eficiente).
- **Chunking:** Aplicar una estrategia de chunking basada en la entidad (Work/Education) antes de enviar al vector store.