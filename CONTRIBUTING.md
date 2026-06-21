# Contributing to Resume Chatbot

## Coding Standards

### Principles
- **Self-documenting code:** Write code so clear that it doesn't need comments explaining what basic operations do
- **Domain semantics:** Use variable and function names based on the domain (e.g., resume, work_entry, vector_store_client)
- **Readability over brevity:** Use explicit variable names
- **Structure:** Follow strict separation: `api/` (endpoints) -> `services/` (logic) -> `db/` (persistence)

### Documentation
- **Google Style Docstrings:** Every function must include:
  - Brief description
  - Args: (type and description)
  - Returns: (type and description)
  - Raises: (possible exceptions)

### Type Safety
- **Type hints:** Mandatory use of type hints
- **Modern Python:** Use `X | Y` syntax instead of `Optional[X]` where appropriate

### Logging
- **Structured logging:** Use `structlog.get_logger(__name__)` instead of print statements

### Error Handling
- **No empty try-except blocks:** Log the error and re-raise a custom exception or return a clear error object

### Async
- **Database/IO operations:** All methods interacting with DB, disk, or LLM must be async

### Atomicity
- **Unit of Work:** Write operations must be atomic between SQLite and ChromaDB

## Testing

Generate integration tests using pytest and httpx in tests/test_api.py. Tests must validate:

1. POST to /work creates entry in database
2. Specific questions via /chat retrieve correct fragments from ChromaDB and respond coherently

### Staff Engineer Tip
When reviewing code, check synchronization logic (SQLAlchemy -> ChromaDB). If too simple, request Unit of Work pattern to prevent orphaned vector indices if database fails.