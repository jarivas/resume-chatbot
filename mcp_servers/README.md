# MCP Servers for Resume Chatbot

This directory contains MCP (Model Context Protocol) servers for read-only access to all database models in the Resume Chatbot application.

## Available Servers

### Work Server (`work_server.py`)
Provides tools for accessing work experience data:
- `get_work_by_id` - Get work experience by ID
- `get_all_work` - Get all work experiences
- `search_work` - Search work experiences by company or position

### Education Server (`education_server.py`)
Provides tools for accessing education data:
- `get_education_by_id` - Get education by ID
- `get_all_education` - Get all education entries
- `search_education` - Search education by institution or area

### Skills Server (`skills_server.py`)
Provides tools for accessing skills data:
- `get_skill_by_id` - Get skill by ID
- `get_all_skills` - Get all skills
- `search_skills` - Search skills by name

### Volunteer Server (`volunteer_server.py`)
Provides tools for accessing volunteer experience data:
- `get_volunteer_by_id` - Get volunteer experience by ID
- `get_all_volunteer` - Get all volunteer experiences
- `search_volunteer` - Search volunteer experiences by organization

### Awards Server (`awards_server.py`)
Provides tools for accessing awards data:
- `get_award_by_id` - Get award by ID
- `get_all_awards` - Get all awards
- `search_awards` - Search awards by title

### Certificates Server (`certificates_server.py`)
Provides tools for accessing certificates data:
- `get_certificate_by_id` - Get certificate by ID
- `get_all_certificates` - Get all certificates
- `search_certificates` - Search certificates by name

### Publications Server (`publications_server.py`)
Provides tools for accessing publications data:
- `get_publication_by_id` - Get publication by ID
- `get_all_publications` - Get all publications
- `search_publications` - Search publications by title

### Languages Server (`languages_server.py`)
Provides tools for accessing languages data:
- `get_language_by_id` - Get language by ID
- `get_all_languages` - Get all languages
- `search_languages` - Search languages by name

### Interests Server (`interests_server.py`)
Provides tools for accessing interests data:
- `get_interest_by_id` - Get interest by ID
- `get_all_interests` - Get all interests
- `search_interests` - Search interests by name

### References Server (`references_server.py`)
Provides tools for accessing references data:
- `get_reference_by_id` - Get reference by ID
- `get_all_references` - Get all references
- `search_references` - Search references by name

### Projects Server (`projects_server.py`)
Provides tools for accessing projects data:
- `get_project_by_id` - Get project by ID
- `get_all_projects` - Get all projects
- `search_projects` - Search projects by name

## Usage

### Running a Server

Each server can be run as a standalone MCP server:

```bash
python mcp_servers/work_server.py
python mcp_servers/education_server.py
python mcp_servers/skills_server.py
# ... etc
```

### Connecting from MCP Client

Configure your MCP client to connect to the desired server. The servers use stdio for communication.

Example configuration for an MCP client:

```json
{
  "mcpServers": {
    "resume-work": {
      "command": "python",
      "args": ["mcp_servers/work_server.py"]
    },
    "resume"education": {
      "command": "python",
      "args": ["mcp_servers/education_server.py"]
    }
  }
}
```

## Architecture

Each MCP server follows the same pattern:

1. **Server Initialization**: Creates an MCP server instance with a unique name
2. **Tool Registration**: Registers 3 tools (get by ID, get all, search)
3. **Tool Execution**: Handles tool calls and returns JSON-formatted results
4. **Database Access**: Uses SQLAlchemy async sessions to query the database
5. **Data Transformation**: Converts database models to JSON format

## Data Format

All servers return data in JSON format with the following structure:

### Single Entity Response
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2"
}
```

### List Response
```json
{
  "entities": [
    {
      "id": 1,
      "field1": "value1"
    },
    {
      "id": 2,
      "field1": "value2"
    }
  ]
}
```

### Error Response
```json
{
  "error": "Entity not found"
}
```

## Error Handling

- **404 Not Found**: When an entity with the specified ID doesn't exist
- **Unknown Tool**: When an invalid tool name is called
- **Database Errors**: Handled gracefully with appropriate error messages

## Dependencies

- `mcp`: Model Context Protocol library
- `sqlalchemy`: Database ORM
- `pydantic`: Data validation (used by models)

## Security Considerations

- These servers are **read-only** and do not provide write operations
- All database access is through SQLAlchemy async sessions
- No authentication is implemented (add as needed for production use)
- SQL injection is prevented through SQLAlchemy's parameterized queries

## Future Enhancements

Potential improvements:
- Add write operations (create, update, delete) with proper authentication
- Implement pagination for list operations
- Add filtering capabilities
- Support for complex queries
- Rate limiting
- Authentication and authorization
- Caching layer for frequently accessed data
- Connection pooling optimization
