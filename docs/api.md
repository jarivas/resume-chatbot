# Documentación API de Resume Chatbot

## Introducción

Esta documentación describe los endpoints REST disponibles en la API de Resume Chatbot para la gestión de currículums vitae (CV).

## Esquema de Datos

La API sigue el estándar [JSON Resume](https://jsonresume.org/) para la representación de currículum vitae.

## Autenticación

Actualmente no se implementa autenticación. Para usar la API, necesitarás configurar la variable de entorno:

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## Endpoints Disponibles

### Work (`/work`)

Endpoints para gestionar experiencias de trabajo.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/work` | Crear experiencia laboral |
| GET | `/work/{id}` | Obtener experiencia por ID |
| GET | `/work` | Obtener todas las experiencias |
| PATCH | `/work/{id}` | Actualizar experiencia parcialmente |
| DELETE | `/work/{id}` | Eliminar experiencia |

#### Ejemplo: Crear experiencia laboral

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

### Education (`/education`)

Endpoints para gestionar educación.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/education` | Crear educación |
| GET | `/education/{id}` | Obtener educación por ID |
| GET | `/education` | Obtener todas las educaciones |
| PATCH | `/education/{id}` | Actualizar educación parcialmente |
| DELETE | `/education/{id}` | Eliminar educación |

#### Ejemplo: Crear educación

```bash
curl -X POST http://localhost:8000/education \
  -H "Content-Type: application/json" \
  -d '{
    "institution": "MIT",
    "area": "Computer Science",
    "study_type": "Bachelor",
    "start_date": "2018-09",
    "end_date": "2022-05",
    "score": "3.8",
    "courses": ["Estructuras de Datos", "Algoritmos"]
  }'
```

### Skills (`/skills`)

Endpoints para gestionar habilidades.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/skills` | Crear habilidad |
| GET | `/skills/{id}` | Obtener habilidad por ID |
| GET | `/skills` | Obtener todas las habilidades |
| PATCH | `/skills/{id}` | Actualizar habilidad parcialmente |
| DELETE | `/skills/{id}` | Eliminar habilidad |

#### Ejemplo: Crear habilidad

```bash
curl -X POST http://localhost:8000/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python",
    "level": "Expert",
    "keywords": ["programación", "desarrollo", "IA"]
  }'
```

### Volunteer (`/volunteer`)

Endpoints para gestionar experiencia de voluntariado.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/volunteer` | Crear experiencia de voluntariado |
| GET | `/volunteer/{id}` | Obtener experiencia por ID |
| GET | `/volunteer` | Obtener todas las experiencias |
| PATCH | `/volunteer/{id}` | Actualizar experiencia parcialmente |
| DELETE | `/volunteer/{id}` | Eliminar experiencia |

### Awards (`/awards`)

Endpoints para gestionar premios y reconocimientos.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/awards` | Crear premio |
| GET | `/awards/{id}` | Obtener premio por ID |
| GET | `/awards` | Obtener todos los premios |
| PATCH | `/awards/{id}` | Actualizar premio parcialmente |
| DELETE | `/awards/{id}` | Eliminar premio |

### Certificates (`/certificates`)

Endpoints para gestionar certificaciones.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/certificates` | Crear certificación |
| GET | `/certificates/{id}` | Obtener certificación por ID |
| GET | `/certificates` | Obtener todas las certificaciones |
| PATCH | `/certificates/{id}` | Actualizar certificación parcialmente |
| DELETE | `/certificates/{id}` | Eliminar certificación |

### Publications (`/publications`)

Endpoints para gestionar publicaciones.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/publications` | Crear publicación |
| GET | `/publications/{id}` | Obtener publicación por ID |
| GET | `/publications` | Obtener todas las publicaciones |
| PATCH | `/publications/{id}` | Actualizar publicación parcialmente |
| DELETE | `/publications/{id}` | Eliminar publicación |

### Languages (`/languages`)

Endpoints para gestionar idiomas.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/languages` | Crear idioma |
| GET | `/languages/{id}` | Obtener idioma por ID |
| GET | `/languages` | Obtener todas las idiomas |
| PATCH | `/languages/{id}` | Actualizar idioma parcialmente |
| DELETE | `/languages/{id}` | Eliminar idioma |

### Interests (`/interests`)

Endpoints para gestionar intereses.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/interests` | Crear interés |
| GET | `/interests/{id}` | Obtener interés por ID |
| GET | `/interests` | Obtener todos los intereses |
| PATCH | `/interests/{id}` | Actualizar interés parcialmente |
| DELETE | `/interests/{id}` | Eliminar interés |

### References (`/references`)

Endpoints para gestionar referencias.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/references` | Crear referencia |
| GET | `/references/{id}` | Obtener referencia por ID |
| GET | `/references` | Obtener todas las referencias |
| PATCH | `/references/{id}` | Actualizar referencia parcialmente |
| DELETE | `/references/{id}` | Eliminar referencia |

### Projects (`/projects`)

Endpoints para gestionar proyectos.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/projects` | Crear proyecto |
| GET | `/projects/{id}` | Obtener proyecto por ID |
| GET | `/projects` | Obtener todos los proyectos |
| PATCH | `/projects/{id}` | Actualizar proyecto parcialmente |
| DELETE | `/projects/{id}` | Eliminar proyecto |

### Chat (`/chat`)

Endpoint para consultas conversacionales con IA.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/chat` | Consulta el CV con IA |

#### Ejemplo: Consultar el CV

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué experiencia tienes en desarrollo de software?"
  }'
```

## Códigos de Estado HTTP

- `200 OK` - Solicitud exitosa
- `201 Created` - Recurso creado exitosamente
- `204 No Content` - Recurso eliminado exitosamente
- `400 Bad Request` - Solicitud inválida
- `404 Not Found` - Recurso no encontrado
- `422 Unprocessable Entity` - Error de validación
- `500 Internal Server Error` - Error del servidor

## Errores Comunes

### Error 404 Not Found

```json
{
  "detail": "Work experience with id 123 not found"
}
```

### Error 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "name"
      ],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Error 500 Internal Server Error

```json
{
  "detail": "Failed to create work experience: Database connection failed"
}
```

## Paginación

Actualmente no se implementa paginación. Los endpoints `GET /{model}` devuelven todos los registros existentes.

## Filtros

Actualmente no se implementan filtros adicionales más allá de la búsqueda por ID.

## Ordenamiento

Los resultados se devuelven en el orden en que fueron creados (por `created_at`).

## Campos de Fecha

Los campos de fecha siguen el formato `YYYY-MM` (ej: `2023-12`) o `YYYY-MM-DD` (ej: `2023-12-25`).

## Campos de Listas

Los campos que son listas en el esquema JSON (como `highlights`, `keywords`, `courses`) se almacenan como strings separadas por `pipe` (`|`) en la base de datos y se convierten a listas en la respuesta API.

## Campos Opcionales

Todos los campos son opcionales excepto los especificados como requeridos en cada endpoint.
