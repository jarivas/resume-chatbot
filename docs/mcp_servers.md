# MCP Servers Documentation

## Overview

The Resume Chatbot project includes 11 MCP (Model Context Protocol) servers that provide read-only access to all database models. These servers enable MCP-compatible clients to query resume data programmatically.

## Server List

| Server | File | Tools Available |
|--------|------|------------------|
| Work | `work_server.py` | get_work_by_id, get_all_work, search_work |
| Education | `education_server.py` | get_education_by_id, get_all_education, search_education |
| Skills | `skills_server.py` | get_skill_by_id, get_all_skills, search_skills |
| Volunteer | `volunteer_server.py` | get_volunteer_by_id, get_all_volunteer, search_volunteer |
| Awards | `awards_server.py` | get_award_by_id, get_all_awards, search_awards |
| Certificates | `certificates_server.py` | get_certificate_by_id, get_all_certificates, search_certificates |
| Publications | `publications_server.py` | get_publication_by_id, get_all_publications, search_publications |
| Languages | `languages_server.py` | get_language_by_id, get_all_languages, search_languages |
| Interests | `interests_server.py` | get_interest_by_id, get_all_interests, search_interests |
| References | `references_server.py` | get_reference_by_id, get_all_references, search_references |
| Projects | `projects_server.py` | get_project_by_id, get_all_projects, search_projects |

## Tool Specifications

### Common Pattern

All servers follow the same pattern with 3 tools:

1. **get_{model}_by_id**: Retrieve a single entity by its ID
2. **get_all_{model}**: Retrieve all entities of that type
3. **search_{model}**: Search entities by relevant fields

### Work Server Tools

#### get_work_by_id
- **Description**: Get work experience by ID
- **Input**: `{"id": integer}`
- **Output**: Work experience object with fields: id, company, position, summary, highlights, start_date, end_date, url, location

#### get_all_work
- **Description**: Get all work experiences
- **Input**: `{}`
- **Output**: Array of work experience objects

#### search_work
- **Description**: Search work experiences by company or position
- **Input**: `{"query": string}`
- **Output**: Array of matching work experience objects

### Education Server Tools

#### get_education_by_id
- **Description**: Get education by ID
- **Input**: `{"id": integer}`
- **Output**: Education object with fields: id, institution, area, study_type, start_date, end_date, score, courses, url

#### get_all_education
- **Description**: Get all education entries
- **Input**: `{}`
- **Output**: Array of education objects

#### search_education
- **Description**: Search education by institution or area
- **Input**: `{"query": string}`
- **Output**: Array of matching education objects

### Skills Server Tools

#### get_skill_by_id
- **Description**: Get skill by ID
- **Input**: `{"id": integer}`
- **Output**: Skill object with fields: id, name, level, keywords

#### get_all_skills
- **Description**: Get all skills
- **Input**: `{}`
- **Output**: Array of skill objects

#### search_skills
- **Description**: Search skills by name
- **Input**: `{"query": string}`
- **Output**: Array of matching skill objects

### Volunteer Server Tools

#### get_volunteer_by_id
- **Description**: Get volunteer experience by ID
- **Input**: `{"id": integer}`
- **Output**: Volunteer object with fields: id, organization, position, summary, highlights, start_date, end_date, url

#### get_all_volunteer
- **Description**: Get all volunteer experiences
- **Input**: `{}`
- **Output**: Array of volunteer objects

#### search_volunteer
- **Description**: Search volunteer experiences by organization
- **Input**: `{"query": string}`
- **Output**: Array of matching volunteer objects

### Awards Server Tools

#### get_award_by_id
- **Description**: Get award by ID
- **Input**: `{"id": integer}`
- **Output**: Award object with fields: id, title, date, awarder, summary, url

#### get_all_awards
- **Description**: Get all awards
- **Input**: `{}`
- **Output**: Array of award objects

#### search_awards
- **Description**: Search awards by title
- **Input**: `{"query": string}`
- **Output**: Array of matching award objects

### Certificates Server Tools

#### get_certificate_by_id
- **Description**: Get certificate by ID
- **Input**: `{"id": integer}`
- **Output**: Certificate object with fields: id, name, date, issuer, url

#### get_all_certificates
- **Description**: Get all certificates
- **Input**: `{}`
- **Output**: Array of certificate objects

#### search_certificates
- **Description**: Search certificates by name
- **Input**: `{"query": string}`
- **Output**: Array of matching certificate objects

### Publications Server Tools

#### get_publication_by_id
- **Description**: Get publication by ID
- **Input**: `{"id": integer}`
- **Output**: Publication object with fields: id, name, publisher, release_date, url, summary

#### get_all_publications
- **Description**: Get all publications
- **Input**: `{}`
- **Output**: Array of publication objects

#### search_publications
- **Description**: Search publications by title
- **Input**: `{"query": string}`
- **Output**: Array of matching publication objects

### Languages Server Tools

#### get_language_by_id
- **Description**: Get language by ID
- **Input**: `{"id": integer}`
- **Output**: Language object with fields: id, language, fluency

#### get_all_languages
- **Description**: Get all languages
- **Input**: `{}`
- **Output**: Array of language objects

#### search_languages
- **Description**: Search languages by name
- **Input**: `{"query": string}`
- **Output**: Array of matching language objects

### Interests Server Tools

#### get_interest_by_id
- **Description**: Get interest by ID
- **Input**: `{"id": integer}`
- **Output**: Interest object with fields: id, name, keywords

#### get_all_interests
- **Description**: Get all interests
- **Input**: `{}`
- **Output**: Array of interest objects

#### search_interests
- **Description**: Search interests by name
- **Input**: `{"query": string}`
- **Output**: Array of matching interest objects

### References Server Tools

#### get_reference_by_id
- **Description**: Get reference by ID
- **Input**: `{"id": integer}`
- **Output**: Reference object with fields: id, name, reference, relationship, email, phone, location

#### get_all_references
- **Description**: Get all references
- **Input**: `{}`
- **Output**: Array of reference objects

#### search_references
- **Description**: Search references by name
- **Input**: `{"query": string}`
- **Output**: Array of matching reference objects

### Projects Server Tools

#### get_project_by_id
- **Description**: Get project by ID
- **Input**: `{"id": integer}`
- **Output**: Project object with fields: id, name, description, highlights, start_date, end_date, url, type, entity, roles

#### get_all_projects
- **Description**: Get all projects
- **Input**: `{}`
- **Output**: Array of project objects

#### search_projects
- **Description**: Search projects by name
- **Input**: `{"query": string}`
- **Output**: Array of matching project objects

## Installation

### Install MCP Library

```bash
poetry run pip install mcp
```

## Configuration

### Client Configuration

Configure your MCP client to connect to the desired servers:

```json
{
  "mcpServers": {
    "resume-work": {
      "command": "python",
      "args": ["mcp_servers/work_server.py"],
      "env": {
        "DATABASE_URL": "sqlite:///resume.db"
      }
    },
    "resume-education": {
      "command": "python",
      "args": ["mcp_servers/education_server.py"],
      "env": {
 {
        "DATABASE_URL": "sqlite:///resume.db"
      }
    },
    "resume-skills": {
      "command": "python",
      "args": ["mcp_servers/skills_server.py"],
      "env": {
        "DATABASE_URL": "sqlite:///resume.db"
      }
    }
  }
}
```

## Usage Examples

### Example 1: Get Work Experience by ID

```python
# MCP client code
result = await client.call_tool("resume-work", "get_work_by_id", {"id": 1})
print(result)
```

### Example 2: Search Education

```python
# MCP client code
result = await client.call_tool("resume-education", "search_education", {"query": "computer"})
print(result)
```

### Example 3: Get All Skills

```python
# MCP client code
result = await client.call_tool("resume-skills", "get_all_skills", {})
print(result)
```

## Response Format

### Success Response

```json
{
  "id": 1,
  "name": "Python",
  "level": "Expert",
  "keywords": ["programming", "development", "AI"]
}
```

### List Response

```json
{
  "skills": [
    {
      "id": 1,
      "name": "Python",
      "level": "Expert",
      "keywords": ["programming", "development", "AI"]
    },
    {
      "id": 2,
      "name":": "JavaScript",
      "level": "Advanced",
      "keywords": ["web", "frontend"]
    }
  ]
}
```

### Error Response

```json
{
  "error": "Skill not found"
}
```

## Technical Details

### Architecture

- **Protocol**: Model Context Protocol (MCP)
- **Transport**: stdio (standard input/output)
- **Database**: SQLite via SQLAlchemy async
- **Serialization**: JSON

### Performance Considerations

- **Connection Pooling**: Each server creates its own database connection
- **Async Operations**: All database operations are async
- **Query Optimization**: Uses indexed fields for searches

### Security

- **Read-Only**: All servers are read-only by design
- **No Authentication**: Currently no authentication (add for production)
- **SQL Injection**: Protected by SQLAlchemy parameterized queries

## Testing

The project includes comprehensive tests for all MCP servers:

```bash
# Run all MCP tests
poetry run pytest tests/mcp/

# Run specific server tests
poetry run pytest tests/mcp/test_work_server.py
poetry run pytest tests/mcp/test_education_server.py
# ... etc
```

### Test Coverage

- **Total MCP tests**: 77 tests
- **Tests per server**: 7 tests
- **Coverage**: 100% of all server functionality

### Test Patterns

Each server has 7 tests:
1. `test_{model}_server_list_tools` - Verify available tools
2. `test_{model}_server_get_by_id` - Test retrieval by ID
3. `test_{model}_server_get_by_id_not_found` - Test 404 error
4. `test_{model}_server_get_all` - Test retrieval of all entities
5. `test_{model}_server_search` - Test search functionality
6. `test_{model}_server_unknown_tool` - Test unknown tool error
7. `test_{model}_server_empty_{list_field}` - Test empty list fields

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure DATABASE `URL` is set correctly
   - Check that the database file exists

2. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python path configuration

3. **Server Not Starting**
   - Check Python version (3.12+ required)
   - Verify MCP library is installed

## Future Enhancements

Potential improvements:
- Add write operations with authentication
- Implement pagination
- Add advanced filtering
- Support for complex queries
- Add caching layer
- Implement rate limiting
- Add metrics and monitoring
- Support for batch operations
- Implement webhooks for data changes
