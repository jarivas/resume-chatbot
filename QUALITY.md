# Estándares de Calidad

## Checklist de Desarrollo
- [ ] **Atomicidad:** Las operaciones de escritura deben ser atómicas entre SQLite y ChromaDB (usar patrón Unit of Work).
- [ ] **Type Safety:** Uso de `typing` (List, Optional, Dict) en todas las capas.
- [ ] **Async:** Todo método que interactúe con DB, Disco o LLM debe ser `async`.
- [ ] **Docstrings:** Seguir formato Google Style para cada endpoint.

## Estrategia de RAG
- **Embedding:** Usar `text-embedding-3-small` (o similar eficiente).
- **Chunking:** Aplicar una estrategia de chunking basada en la entidad (Work/Education) antes de enviar al vector store.