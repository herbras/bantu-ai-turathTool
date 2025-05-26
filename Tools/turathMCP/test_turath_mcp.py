import pytest
from fastmcp import Client
import httpx  # Untuk membuat mock HTTP response
import json

# Import mcp_server dari file turath-mcp.py
# Pastikan test_turath_mcp.py berada di direktori yang sama dengan turath-mcp.py
from Tools.turathMCP.turath_mcp import mcp_server

# Pytest akan otomatis menemukan dan menjalankan fungsi tes yang diawali dengan 'test_'
# dan kelas tes yang diawali dengan 'Test'.


@pytest.mark.asyncio
async def test_get_filter_ids_category_found(mocker):
    """
    Tes get_filter_ids ketika nama kategori ditemukan di DB.
    """
    # Mock fungsi query_local_db yang dipanggil oleh get_filter_ids
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")

    # Simulasikan DB mengembalikan satu ID kategori
    mock_query_db.return_value = [(123,)]

    async with Client(mcp_server) as client:
        # Panggil tool 'get_filter_ids' dengan parameter category_name
        result_tuple = await client.call_tool(
            "get_filter_ids", {"category_name": "Fiqih"}
        )

    # client.call_tool mengembalikan tuple, hasil tool ada di elemen pertama
    actual_result = result_tuple[0]

    expected_result = {"category_ids": "123", "author_ids": None}
    assert actual_result == expected_result

    # Verifikasi bahwa query_local_db dipanggil dengan parameter yang benar
    mock_query_db.assert_called_once_with(
        "SELECT id FROM cats WHERE name LIKE ?", ("%Fiqih%",)
    )


@pytest.mark.asyncio
async def test_get_filter_ids_author_found(mocker):
    """
    Tes get_filter_ids ketika nama penulis ditemukan di DB.
    """
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")
    mock_query_db.return_value = [
        (456,)
    ]  # Simulasikan DB mengembalikan satu ID penulis

    async with Client(mcp_server) as client:
        result_tuple = await client.call_tool(
            "get_filter_ids", {"author_name": "Al-Ghazali"}
        )

    actual_result = result_tuple[0]
    expected_result = {"category_ids": None, "author_ids": "456"}
    assert actual_result == expected_result
    mock_query_db.assert_called_once_with(
        "SELECT id FROM authors WHERE name LIKE ?", ("%Al-Ghazali%",)
    )


@pytest.mark.asyncio
async def test_get_filter_ids_not_found(mocker):
    """
    Tes get_filter_ids ketika kategori maupun penulis tidak ditemukan.
    """
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")
    # Simulasikan DB tidak mengembalikan apa-apa (None atau list kosong)
    mock_query_db.return_value = []

    async with Client(mcp_server) as client:
        result_tuple = await client.call_tool(
            "get_filter_ids", {"category_name": "NonExistent", "author_name": "Unknown"}
        )

    actual_result = result_tuple[0]
    expected_message = {
        "message": "Tidak ada ID yang ditemukan untuk nama kategori atau penulis yang diberikan."
    }
    assert actual_result == expected_message

    # Harusnya dipanggil dua kali, sekali untuk kategori, sekali untuk penulis
    assert mock_query_db.call_count == 2


@pytest.mark.asyncio
async def test_get_book_details_success_with_pdf_links(mocker):
    """
    Tes get_book_details berhasil, API mengembalikan link PDF, dan data diperkaya dari DB lokal.
    """
    mock_http_get = mocker.patch("Tools.turathMCP.turath_mcp.http_client.get")
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")

    book_id_to_test = 23622  # From databuku.json

    # Mock respons dari API Turath.io, based on databuku.json
    api_pdf_links_data = {
        "files": ["mnaia.pdf"],
        "root": "علوم القرآن/مسائل نافع بن الأزرق عن ابن عباس - ت الدالي - ط الجفان والجابي"
    }
    mock_api_response_json = {
        "id": book_id_to_test,
        "name": "مسائل نافع بن الأزرق = غريب القرآن في شعر العرب", # API field
        "meta": {
            "id": book_id_to_test, # meta.id from databuku.json
            "name": "مسائل نافع بن الأزرق = غريب القرآن في شعر العرب", # meta.name from databuku.json
            "author_id": 263, # from databuku.json
            "cat_id": 4, # from databuku.json
            "pdf_links": api_pdf_links_data
        }
        # Add other fields from api_result if they are directly used by the tool before enrichment
    }
    mock_http_response = httpx.Response(200, json=mock_api_response_json)
    mock_http_get.return_value = mock_http_response

    # Mock respons dari query_local_db
    # Urutan pemanggilan query_local_db dalam get_book_details:
    # 1. UPDATE books SET pdf_links = ?, has_pdf = 1 WHERE id = ? (untuk menyimpan link PDF dari API)
    # 2. SELECT name, author_id, cat_id, pdf_links, info_long, printed, size FROM books WHERE id = ?
    # 3. SELECT name, death FROM authors WHERE id = ? (jika author_id ada)
    # 4. SELECT name FROM cats WHERE id = ? (jika cat_id ada)

    # Data buku lokal yang akan dikembalikan oleh query_local_db (panggilan ke-2)
    local_book_data = (
        "Local Book Name",
        101,
        202,
        json.dumps(api_pdf_links_data),
        "Local long info",
        "Yes",
        10.5,
    )
    # Data penulis lokal (panggilan ke-3)
    local_author_data = ("Local Author Name", "750 H")
    # Data kategori lokal (panggilan ke-4)
    local_category_data = ("Local Category Name",)

    mock_query_db.side_effect = [
        None,  # Hasil dari UPDATE query (tidak terlalu penting untuk asserstion hasil akhir)
        [local_book_data],  # list of tuples
        [local_author_data],  # list of tuples
        [local_category_data],  # list of tuples
    ]

    async with Client(mcp_server) as client:
        result_tuple = await client.call_tool(
            "get_book_details", {"book_id": book_id_to_test}
        )

    actual_result = result_tuple[0]

    # Verifikasi hasil
    assert "error" not in actual_result
    assert actual_result.get("id") == book_id_to_test  # Dari API (top level)
    assert actual_result.get("name") == "مسائل نافع بن الأزرق = غريب القرآن في شعر العرب" # Dari API (top level)
    assert actual_result.get("meta").get("pdf_links") == api_pdf_links_data # API meta passed through
    assert actual_result.get("local_book_name") == "Local Book Name"
    assert actual_result.get("local_author_name") == "Local Author Name"
    assert actual_result.get("local_category_name") == "Local Category Name"
    assert actual_result.get("local_pdf_links") == json.dumps(
        api_pdf_links_data
    )  # Disimpan dari API, lalu dibaca lagi
    assert actual_result.get("local_info_long") == "Local long info"

    # Verifikasi mock calls
    mock_http_get.assert_called_once_with(
        "/book", params={"id": book_id_to_test, "ver": 3}
    )

    assert mock_query_db.call_count == 4
    # Verifikasi panggilan update pdf_links ke DB
    update_db_call = mock_query_db.call_args_list[0]
    assert (
        update_db_call.args[0]
        == "UPDATE books SET pdf_links = ?, has_pdf = 1 WHERE id = ?"
    )
    assert update_db_call.args[1] == (json.dumps(api_pdf_links_data), book_id_to_test)


@pytest.mark.asyncio
async def test_get_book_details_api_error(mocker):
    """
    Tes get_book_details ketika panggilan API gagal.
    """
    mock_http_get = mocker.patch("Tools.turathMCP.turath_mcp.http_client.get")

    # Simulasikan HTTPStatusError dari httpx
    mock_http_get.side_effect = httpx.HTTPStatusError(
        "API Error",
        request=mocker.Mock(url="http://fakeurl/book"),
        response=httpx.Response(status_code=500, json={"detail": "Server error"}),
    )

    # query_local_db tidak akan dipanggil jika API error sebelum blok enrichment
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")

    async with Client(mcp_server) as client:
        result_tuple = await client.call_tool("get_book_details", {"book_id": 999})

    actual_result = result_tuple[0]

    assert "error" in actual_result
    assert actual_result["error"] == "API Error: 500"
    mock_query_db.assert_not_called()  # Pastikan DB tidak diquery jika API gagal


@pytest.mark.asyncio
async def test_get_book_details_success_no_pdf_links_from_api(mocker):
    """
    Tes get_book_details berhasil, API TIDAK mengembalikan link PDF.
    Pastikan DB lokal diupdate (has_pdf=0, pdf_links=NULL) dan hasil akhir merefleksikannya.
    """
    mock_http_get = mocker.patch("Tools.turathMCP.turath_mcp.http_client.get")
    mock_query_db = mocker.patch("Tools.turathMCP.turath_mcp.query_local_db")

    book_id_to_test = 2

    # Mock respons dari API Turath.io - meta ada, tapi pdf_links kosong/tidak valid
    mock_api_response_json = {
        "id": book_id_to_test,
        "title_api": "Book Title No PDF from API",
        "meta": {
            "some_meta": "value",
            # "pdf_links": {} # Tidak ada pdf_links atau pdf_links tidak valid
        }
    }
    mock_http_response = httpx.Response(200, json=mock_api_response_json)
    mock_http_get.return_value = mock_http_response

    # Mock respons dari query_local_db
    # Urutan pemanggilan query_local_db:
    # 1. UPDATE books SET pdf_links = NULL, has_pdf = 0 WHERE id = ?
    # 2. SELECT name, author_id, cat_id, pdf_links, info_long, printed, size FROM books WHERE id = ?
    # 3. SELECT name, death FROM authors WHERE id = ? (jika author_id ada)
    # 4. SELECT name FROM cats WHERE id = ? (jika cat_id ada)

    # Data buku lokal yang akan dikembalikan (pdf_links harusnya None setelah update)
    local_book_data_no_pdf = ("Local Book Name (No PDF)", 102, 203, None, "Local long info no PDF", "No", 5.0)
    local_author_data = ("Local Author Name", "800 H")
    local_category_data = ("Local Category Name",)

    mock_query_db.side_effect = [
        None,  # Hasil dari UPDATE query
        [local_book_data_no_pdf],
        [local_author_data],
        [local_category_data]
    ]

    async with Client(mcp_server) as client:
        result_tuple = await client.call_tool("get_book_details", {"book_id": book_id_to_test})

    actual_result = result_tuple[0]

    # Verifikasi hasil
    assert "error" not in actual_result
    assert actual_result.get("id") == book_id_to_test
    assert actual_result.get("title_api") == "Book Title No PDF from API"
    assert actual_result.get("local_book_name") == "Local Book Name (No PDF)"
    assert actual_result.get("local_author_name") == "Local Author Name"
    assert actual_result.get("local_category_name") == "Local Category Name"
    assert actual_result.get("local_pdf_links") is None # Penting!
    assert actual_result.get("local_info_long") == "Local long info no PDF"

    # Verifikasi mock calls
    mock_http_get.assert_called_once_with("/book", params={"id": book_id_to_test, "ver": 3})
    
    assert mock_query_db.call_count == 4 # 1 update, 3 select
    
    # Verifikasi panggilan update pdf_links ke DB (untuk mengosongkannya)
    update_db_call = mock_query_db.call_args_list[0]
    assert update_db_call.args[0] == "UPDATE books SET pdf_links = NULL, has_pdf = 0 WHERE id = ?"
    assert update_db_call.args[1] == (book_id_to_test,)


# Kamu bisa menambahkan lebih banyak tes untuk tool lain seperti:
# - get_page_content
# - search_library (ini akan lebih kompleks karena banyak parameter dan interaksi DB di _enrich_search_results_sync)
# - get_author_bio
#
# Serta berbagai skenario untuk setiap tool (misalnya, data tidak ditemukan di DB lokal,
# API mengembalikan pdf_links kosong, dll.)
