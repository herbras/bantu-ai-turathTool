import asyncio
import httpx
from typing import Optional, Annotated
from pydantic import Field
import json
import sqlite3
import os

from fastmcp import FastMCP

TURATH_API_BASE_URL = "https://api.turath.io"
DB_PATH = os.path.join(os.path.dirname(__file__), "turath_metadata.db")

http_client = httpx.AsyncClient(base_url=TURATH_API_BASE_URL)


def _query_local_db_sync(query: str, params: tuple = ()):
    """Synchronous helper to connect, query, and close the local SQLite DB."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.commit()
        return results
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
        print(f"Query: {query} | Params: {params}")
        return None
    finally:
        if conn:
            conn.close()


async def query_local_db(query: str, params: tuple = ()):
    """Asynchronously queries the local SQLite DB using a thread."""
    return await asyncio.to_thread(_query_local_db_sync, query, params)


async def shutdown_event():
    """Menutup HTTP client secara baik-baik saat server dimatikan."""
    print("MCP Server: Menutup HTTP client...")
    await http_client.aclose()
    print("MCP Server: HTTP client berhasil ditutup.")


mcp_server = FastMCP(name="TurathMCPServer", on_shutdown=[shutdown_event])


@mcp_server.tool()
async def get_filter_ids(
    category_name: Annotated[
        Optional[str],
        Field(
            description="Nama kategori untuk dicari ID-nya (misalnya, 'Fiqih', 'Aqidah', 'Mazhab Syafi'i')."
        ),
    ] = None,
    author_name: Annotated[
        Optional[str], Field(description="Nama penulis untuk dicari ID-nya.")
    ] = None,
) -> dict:
    """
    Mencari ID kategori dan/atau penulis dari database lokal berdasarkan nama.
    Mengembalikan dictionary dengan 'category_ids' dan/atau 'author_ids' (berupa string ID yang dipisahkan koma).
    """
    results = {"category_ids": None, "author_ids": None}
    found_something = False

    if category_name:
        cat_query_param = f"%{category_name}%"
        cat_rows = await query_local_db(
            "SELECT id FROM cats WHERE name LIKE ?", (cat_query_param,)
        )
        if cat_rows:
            results["category_ids"] = ",".join([str(row[0]) for row in cat_rows])
            found_something = True
            print(
                f"MCP Server: ID kategori ditemukan \'{results['category_ids']}\' untuk nama \'{category_name}\'"
            )
        else:
            print(f"MCP Server: Tidak ada ID kategori ditemukan untuk nama \'{category_name}\'")

    if author_name:
        author_query_param = f"%{author_name}%"
        author_rows = await query_local_db(
            "SELECT id FROM authors WHERE name LIKE ?", (author_query_param,)
        )
        if author_rows:
            results["author_ids"] = ",".join([str(row[0]) for row in author_rows])
            found_something = True
            print(
                f"MCP Server: ID penulis ditemukan \'{results['author_ids']}\' untuk nama \'{author_name}\'"
            )
        else:
            print(f"MCP Server: Tidak ada ID penulis ditemukan untuk nama \'{author_name}\'")

    if not found_something:
        return {
            "message": "Tidak ada ID yang ditemukan untuk nama kategori atau penulis yang diberikan."
        }

    return results


@mcp_server.tool()
async def get_book_details(
    book_id: Annotated[int, Field(description="The ID of the book to retrieve.")],
    include: Annotated[
        Optional[str],
        Field(description='Specifies additional data to include (e.g., "indexes").'),
    ] = None,
    ver: Annotated[Optional[int], Field(description="API version, typically 3.")] = 3,
) -> dict:
    """Fetches detailed information for a specific book, enriching with local DB data."""
    params = {"id": book_id, "ver": ver}
    if include:
        params["include"] = include

    api_result = {}
    try:
        response = await http_client.get("/book", params=params)
        response.raise_for_status()
        api_result = response.json()
    except httpx.HTTPStatusError as exc:
        api_result = {
            "error": f"API Error: {exc.response.status_code}",
            "details": str(exc),
        }
    except httpx.RequestError as exc:
        api_result = {
            "error": "Request Error: Failed to connect to Turath API.",
            "details": str(exc),
        }
    except Exception as e:
        api_result = {
            "error": "An unexpected error occurred during API call.",
            "details": str(e),
        }

    if "error" not in api_result:
        api_meta = api_result.get("meta")
        if isinstance(api_meta, dict):
            pdf_links_from_api = api_meta.get("pdf_links")
            if (
                isinstance(pdf_links_from_api, dict)
                and pdf_links_from_api.get("files")
                and pdf_links_from_api.get("root")
            ):
                pdf_links_json_str = json.dumps(pdf_links_from_api)
                update_query = (
                    "UPDATE books SET pdf_links = ?, has_pdf = 1 WHERE id = ?"
                )
                await query_local_db(update_query, (pdf_links_json_str, book_id))
                print(
                    f"MCP Server: Link PDF lokal untuk book_id {book_id} telah diperbarui/dikonfirmasi dari API."
                )
            else:
                update_query = (
                    "UPDATE books SET pdf_links = NULL, has_pdf = 0 WHERE id = ?"
                )
                await query_local_db(update_query, (book_id,))
                print(
                    f"MCP Server: Tidak ada link PDF valid dari API untuk book_id {book_id}. DB Lokal telah diperbarui."
                )

        local_data = await query_local_db(
            "SELECT name, author_id, cat_id, pdf_links, info_long, printed, size FROM books WHERE id = ?",
            (book_id,),
        )
        if local_data:
            book_info = local_data[0]
            api_result["local_book_name"] = book_info[0]
            api_result["local_pdf_links"] = book_info[3]
            api_result["local_info_long"] = book_info[4]
            api_result["local_printed"] = book_info[5]
            api_result["local_size_mb"] = book_info[6]

            author_id = book_info[1]
            cat_id = book_info[2]

            if author_id:
                author_info = await query_local_db(
                    "SELECT name, death FROM authors WHERE id = ?", (author_id,)
                )
                if author_info:
                    api_result["local_author_name"] = author_info[0][0]
                    api_result["local_author_death"] = author_info[0][1]

            if cat_id:
                cat_info = await query_local_db(
                    "SELECT name FROM cats WHERE id = ?", (cat_id,)
                )
                if cat_info:
                    api_result["local_category_name"] = cat_info[0][0]
        else:
            api_result["local_db_status"] = "Book ID tidak ditemukan di DB lokal."

    return api_result


@mcp_server.tool()
async def get_page_content(
    book_id: Annotated[int, Field(description="The ID of the book.")],
    pg: Annotated[int, Field(description="The page number to retrieve.")],
    ver: Annotated[Optional[int], Field(description="API version, typically 3.")] = 3,
) -> dict:
    """Fetches the text content of a specific page within a book."""
    params = {"book_id": book_id, "pg": pg, "ver": ver}
    try:
        response = await http_client.get("/page", params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        return {"error": f"API Error: {exc.response.status_code}", "details": str(exc)}
    except httpx.RequestError as exc:
        return {
            "error": "Request Error: Failed to connect to Turath API.",
            "details": str(exc),
        }
    except Exception as e:
        return {"error": "An unexpected error occurred.", "details": str(e)}


@mcp_server.tool()
async def search_library(
    q: Annotated[
        str, Field(description="The search query string (expected in Arabic).")
    ],
    ver: Annotated[Optional[int], Field(description="API version, typically 3.")] = 3,
    page: Annotated[
        Optional[int], Field(description="Page number for paginated results.")
    ] = None,
    book: Annotated[
        Optional[str],
        Field(description="Comma-separated list of book IDs to filter by."),
    ] = None,
    author: Annotated[
        Optional[str],
        Field(description="Comma-separated list of author IDs to filter by."),
    ] = None,
    cat: Annotated[
        Optional[str],
        Field(description="Comma-separated list of category IDs to filter by."),
    ] = None,
    printed: Annotated[
        Optional[str], Field(description='Filter by print status (e.g., "1,2").')
    ] = None,
    type: Annotated[
        Optional[str], Field(description='Filter by content type (e.g., "1" for كتاب).')
    ] = None,
    death: Annotated[
        Optional[str],
        Field(
            description='Filter by author death year range (e.g., ",700", "600,750", "700,").'
        ),
    ] = None,
    non_author: Annotated[
        Optional[int],
        Field(
            description="Include non-author text (1 for true, 0 for false).", ge=0, le=1
        ),
    ] = 1,
    sort: Annotated[
        Optional[str],
        Field(description="Sort order.", pattern=r"^(default|death|page_id)$"),
    ] = "default",
    precision: Annotated[
        Optional[int],
        Field(
            description="Search precision (0: some, 1: all, 2: consecutive).",
            ge=0,
            le=2,
        ),
    ] = 2,
    stem: Annotated[
        Optional[int],
        Field(description="Enable stemming (1 for true, 0 for false).", ge=0, le=1),
    ] = 1,
) -> dict:
    """Performs a search across the library based on query and filters. Expects query in Arabic. Enriches results with local DB."""
    params = {
        "q": q,
        "ver": ver,
        "non_author": non_author,
        "precision": precision,
    }
    if sort != "default":
        params["sort"] = sort
    if stem != 1:
        params["stem"] = stem
    if page is not None:
        params["page"] = page
    if book is not None:
        params["book"] = book
    if author is not None:
        params["author"] = author
    if cat is not None:
        params["cat"] = cat
    if printed is not None:
        params["printed"] = printed
    if type is not None:
        params["type"] = type
    if death is not None:
        params["death"] = death

    print("--- MCP Server: Memulai search_library ---")
    print(f"MCP Server: Mengirim parameter ke API: {params}")

    try:
        print(f"MCP Server: Membuat permintaan ke {TURATH_API_BASE_URL}/search")
        response = await http_client.get("/search", params=params)
        print(f"MCP Server: Menerima status kode respons: {response.status_code}")
        response.raise_for_status()
        result_json = response.json()

        if "data" in result_json and isinstance(result_json["data"], list):
            enrichment_error = await asyncio.to_thread(
                _enrich_search_results_sync, result_json["data"], DB_PATH
            )
            if enrichment_error:
                result_json["enrichment_error"] = enrichment_error
        # --- MODIFICATION END ---

        print("MCP Server: Berhasil memproses permintaan dan memperkaya referensi.")
        return result_json
    except httpx.HTTPStatusError as exc:
        error_details = f"Kesalahan API: {exc.response.status_code}. URL: {exc.request.url}"
        response_text = ""
        try:
            response_text = exc.response.text
            print(f"MCP Server: Kesalahan Status HTTP: {error_details}")
            print(f"MCP Server: Isi Respons Error: {response_text}")
        except Exception as log_err:
            print(
                f"MCP Server: Kesalahan Status HTTP: {error_details}. Tidak dapat membaca isi respons: {log_err}"
            )

        return {
            "error": error_details,
            "details": str(exc),
            "response_text": response_text,
        }
    except httpx.RequestError as exc:
        error_details = (
            f"Kesalahan Permintaan: Gagal terhubung ke API Turath. URL: {exc.request.url}"
        )
        print(f"MCP Server: {error_details} - Pengecualian: {exc}")
        return {
            "error": error_details,
            "details": str(exc),
        }
    except Exception as e:
        import traceback

        print(f"MCP Server: Kesalahan tak terduga di search_library: {e}")
        print(traceback.format_exc())
        return {
            "error": "Terjadi kesalahan tak terduga di MCP server search_library.",
            "details": str(e),
        }
    finally:
        print("--- MCP Server: search_library selesai ---")


@mcp_server.tool()
async def get_author_bio(
    author_id: Annotated[int, Field(description="The ID of the author.", alias="id")],
    ver: Annotated[Optional[int], Field(description="API version, typically 3.")] = 3,
) -> dict:
    """Fetches biographical information for a specific author, enriching with local DB data."""
    params = {"id": author_id, "ver": ver}
    api_result = {}
    try:
        response = await http_client.get("/author", params=params)
        response.raise_for_status()
        api_result = response.json()
    except httpx.HTTPStatusError as exc:
        api_result = {
            "error": f"API Error: {exc.response.status_code}",
            "details": str(exc),
        }
    except httpx.RequestError as exc:
        api_result = {
            "error": "Request Error: Failed to connect to Turath API.",
            "details": str(exc),
        }
    except Exception as e:
        api_result = {
            "error": "An unexpected error occurred during API call.",
            "details": str(e),
        }

    # --- Enrich with Local DB Data ---
    if "error" not in api_result:
        local_data = await query_local_db(
            "SELECT name, death, death_inexact_label FROM authors WHERE id = ?",
            (author_id,),
        )
        if local_data:
            author_info = local_data[0]
            api_result["local_author_name"] = author_info[0]
            api_result["local_author_death"] = author_info[1]
            api_result["local_author_death_label"] = author_info[2]
        else:
            api_result["local_db_status"] = "Author ID tidak ditemukan di DB lokal."
    # --- End Enrichment ---

    return api_result


def _enrich_search_results_sync(
    data_list: list, db_path_for_thread: str
) -> Optional[str]:
    """
    Synchronously enriches search result items with local DB data.
    Modifies items in data_list in-place.
    Returns an error message string if a SQLite error occurs, otherwise None.
    """
    conn_enrich = None
    try:
        conn_enrich = sqlite3.connect(db_path_for_thread)
        cursor = conn_enrich.cursor()

        for item in data_list:
            book_id_api = item.get("book_id")
            local_book_name = None
            local_author_name = None
            local_cat_name = None
            local_pdf_links = None
            local_info_long = None

            if book_id_api:
                cursor.execute(
                    """
                    SELECT b.name, a.name, c.name, b.pdf_links, b.info_long
                    FROM books b
                    LEFT JOIN authors a ON b.author_id = a.id
                    LEFT JOIN cats c ON b.cat_id = c.id
                    WHERE b.id = ?
                """,
                    (book_id_api,),
                )
                local_details = cursor.fetchone()

                if local_details:
                    (
                        local_book_name,
                        local_author_name,
                        local_cat_name,
                        local_pdf_links,
                        local_info_long,
                    ) = local_details
                    item["local_book_name"] = local_book_name
                    item["local_author_name"] = local_author_name
                    item["local_category_name"] = local_cat_name
                    item["local_pdf_links"] = local_pdf_links
                    item["local_info_long"] = local_info_long
                else:
                    item["local_db_status"] = (
                        f"Book ID {book_id_api} not found locally."
                    )

            reference_parts = []
            meta_str = item.get("meta")
            vol = None
            page_num = None
            if meta_str:
                try:
                    meta_data = json.loads(meta_str)
                    vol = meta_data.get("vol")
                    page_num = meta_data.get("page")
                except json.JSONDecodeError:
                    print(
                        f"MCP Server: Peringatan - Tidak dapat mem-parse meta JSON untuk buku {book_id_api}: {meta_str}"
                    )

            if local_book_name:
                reference_parts.append(f"Kitab: {local_book_name}")
            elif (
                meta_str
            ):  # Safely attempt to access nested keys only if meta_str is not None
                try:
                    meta_data_for_book_name = json.loads(meta_str)
                    if meta_data_for_book_name.get("book_name"):
                        reference_parts.append(
                            f"Kitab: {meta_data_for_book_name.get('book_name')}"
                        )
                except json.JSONDecodeError:
                    pass  # Already logged warning

            if local_author_name:
                reference_parts.append(f"Penulis: {local_author_name}")
            elif meta_str:  # Safely attempt to access nested keys
                try:
                    meta_data_for_author_name = json.loads(meta_str)
                    if meta_data_for_author_name.get("author_name"):
                        reference_parts.append(
                            f"Penulis: {meta_data_for_author_name.get('author_name')}"
                        )
                except json.JSONDecodeError:
                    pass  # Already logged warning

            if local_cat_name:  # Add category if found locally
                reference_parts.append(f"Kategori: {local_cat_name}")

            if vol:
                reference_parts.append(f"Jilid: {vol}")
            if page_num:
                reference_parts.append(f"Halaman: {page_num}")

            page_id_ref = None
            if meta_str:  # Ensure meta_data is defined before accessing .get
                try:
                    # Re-parse meta_str to ensure meta_data is available in this scope if not set before
                    # This is a bit redundant if vol/page_num parsing already defined it
                    # but ensures safety if those blocks weren't entered.
                    current_meta_data = json.loads(meta_str)
                    if isinstance(current_meta_data, dict):
                        page_id_ref = current_meta_data.get("page_id")
                except json.JSONDecodeError:
                    pass  # Warning already printed

            if book_id_api:
                base_url = "https://shamela.ws"
                if page_id_ref:
                    reference_parts.append(
                        f"Link: {base_url}/book/{book_id_api}/{page_id_ref}"
                    )
                else:
                    reference_parts.append(f"Link: {base_url}/book/{book_id_api}")

            if not reference_parts:
                reference_parts.append("Detail referensi tidak tersedia.")

            item["reference_info"] = "Sumber: " + ", ".join(reference_parts)
        return None  # Success
    except sqlite3.Error as db_err:
        print(f"Kesalahan SQLite saat threaded enrichment: {db_err}")
        return str(db_err)  # Return error message
    finally:
        if conn_enrich:
            conn_enrich.close()


@mcp_server.tool()
async def list_all_categories() -> dict:
    """Mengambil semua kategori dari database lokal.
    Mengembalikan dictionary dengan key 'categories' yang berisi list of dictionaries (id, name).
    """
    query = "SELECT id, name FROM cats ORDER BY name ASC"
    categories_rows = await query_local_db(query)
    if categories_rows is None:  # Error saat query DB
        return {"error": "Database query failed for categories."}

    categories_list = [{"id": row[0], "name": row[1]} for row in categories_rows]
    return {"categories": categories_list}


@mcp_server.tool()
async def list_all_authors() -> dict:
    """Mengambil semua penulis dari database lokal.
    Mengembalikan dictionary dengan key 'authors' yang berisi list of dictionaries (id, name, death, death_inexact_label).
    """
    query = "SELECT id, name, death, death_inexact_label FROM authors ORDER BY name ASC"
    authors_rows = await query_local_db(query)
    if authors_rows is None:  # Error saat query DB
        return {"error": "Database query failed for authors."}

    authors_list = [
        {"id": row[0], "name": row[1], "death": row[2], "death_inexact_label": row[3]}
        for row in authors_rows
    ]
    return {"authors": authors_list}


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database SQLite tidak ditemukan di {DB_PATH}")
        print("Mohon pastikan file database ada di lokasi yang benar.")
        exit(1)
    else:
        print(f"Database SQLite ditemukan di: {DB_PATH}")

    port = 8001
    print(f"Memulai Turath MCP Server dengan SSE di http://localhost:{port}/sse")
    mcp_server.run(transport="sse", port=port)
