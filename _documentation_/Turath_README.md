# Unofficial Turath MCP Server

## Overview

The Turath MCP (Machine-readable Cataloging Protocol) Server provides a programmatic interface to the Turath.io API, an online digital repository for classical Islamic manuscripts. This server, built with FastMCP, enriches the data retrieved from the Turath API with additional information агрегированной from a local SQLite database (`turath_metadata.db`).

https://app.turath.io/

The primary goal of this server is to offer enhanced and more context-rich access to the Turath library, facilitating complex queries and data retrieval for applications and research.

## Location of Components

-   **Server Script:** `turathMCP/turath-mcp.py`
-   **Local Database:** `turathMCP/turath_metadata.db`

## Features

-   **Asynchronous Operations:** Utilizes `httpx.AsyncClient` for non-blocking HTTP requests to the Turath API and `asyncio` for database operations.
-   **Local Data Enrichment:** Augments API responses with data from a local SQLite database, including:
    -   Local book names, author names, and category names.
    -   PDF links (if available locally).
    -   Extended information décès about books and authors.
    -   Formatted reference strings for search results.
-   **Graceful Shutdown:** Ensures the HTTP client is properly closed on server shutdown.
-   **SSE (Server-Sent Events) Support:** Runs on SSE for real-time communication.

## Provided MCP Tools

The server exposes the following tools callable by an MCP client:

1.  **`get_filter_ids(category_name: Optional[str], author_name: Optional[str]) -> dict`**
    *   Searches the local database for category and/or author IDs based on their names.
    *   Uses `LIKE` for flexible name matching.
    *   Returns a dictionary with `category_ids` and/or `author_ids` (comma-separated strings).

2.  **`get_book_details(book_id: int, include: Optional[str], ver: Optional[int] = 3) -> dict`**
    *   Fetches detailed information for a specific book from the Turath API.
    *   Enriches the API response with local data for the book, its author, and category.

3.  **`get_page_content(book_id: int, pg: int, ver: Optional[int] = 3) -> dict`**
    *   Retrieves the text content of a specific page within a book from the Turath API.

4.  **`search_library(...) -> dict`**
    *   Performs a comprehensive search across the Turath library.
    *   Accepts various filters: query string (Arabic), book IDs, author IDs, category IDs, print status, content type, author death year range, etc.
    *   Enriches search results with local database information, providing `local_book_name`, `local_author_name`, `local_category_name`, and a formatted `reference_info` string for each result.

5.  **`get_author_bio(author_id: int, ver: Optional[int] = 3) -> dict`**
    *   Fetches biographical information for a specific author from the Turath API.
    *   Enriches the API response with local author data (name, death year, death label).

## Local Database: `turath_metadata.db`

This SQLite database is crucial for the data enrichment capabilities of the server.

**Schema Overview:**

*   **`authors` Table:**
    *   `id` (INTEGER PK): Author ID.
    *   `name` (TEXT NOT NULL): Author name.
    *   `death` (INTEGER): Death year (Hijri).
    *   `death_inexact_label` (TEXT): Label for inexact death year (e.g., "circa 700 H").
*   **`cats` (Categories) Table:**
    *   `id` (INTEGER PK): Category ID.
    *   `name` (TEXT NOT NULL): Category name.
    *   `books` (TEXT): JSON array of book IDs belonging to this category.
*   **`books` Table:**
    *   `id` (INTEGER PK): Book ID (corresponds to Turath.io book ID).
    *   `name` (TEXT NOT NULL): Local book name.
    *   `author_id` (INTEGER FK -> authors.id): Author of the book.
    *   `cat_id` (INTEGER FK -> cats.id): Category of the book.
    *   `size` (REAL): Book size (e.g., MB).
    *   `has_pdf` (INTEGER): Boolean (0/1) indicating PDF availability.
    *   `printed` (TEXT): Print status.
    *   `pdf_links` (TEXT): JSON string of PDF links.
    *   `info` (TEXT): Short information.
    *   `info_long` (TEXT): Long/detailed information.
    *   ... and other metadata fields, often stored as JSON TEXT.

**Purpose of the Local Database:**
    -   Cache supplementary data not directly available or conveniently queryable from the Turath API endpoints.
    -   Provide localized or alternative naming for entities.
    -   Store links to local resources (e.g., PDFs).
    -   Enhance search results with readily available contextual information.

## Setup and Running

1.  **Prerequisites:**
    *   Python 3.x
    *   Required Python packages (see `requirements.txt` if available, or install `fastmcp`, `httpx`, `pydantic`, `uvicorn` - FastMCP typically brings its own server like uvicorn).
    *   The `turath_metadata.db` SQLite database file must be present in the `turathMCP/` directory.

2.  **Running the Server:**
    Navigate to the `turathMCP` directory and run the Python script:
    ```bash
    cd Tools/turathMCP
    python turath-mcp.py
    ```
    The server will start, typically on `http://localhost:8001`. The SSE endpoint will be available at `http://localhost:8001/sse`.

    Output upon successful start:
    ```
    SQLite database found at: turathMCP/turath_metadata.db
    Starting Turath MCP Server with SSE on http://localhost:8001/sse
    ```

3.  **Ensure Database Exists:**
    The server will check for `turath_metadata.db` at startup. If not found, it will print an error and exit.

    ```
    ERROR: SQLite database not found at turathMCP/turath_metadata.db
    Please ensure the database file exists in the correct location.
    ```

## Interacting with the Server

The server can be interacted with using any MCP-compliant client by connecting to its exposed endpoint (e.g., `http://localhost:8001/sse` for Server-Sent Events). The client can then call the tools defined above.
