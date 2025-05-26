# Proyek Riset Turath dengan AI

## ⚠️ PERINGATAN PENTING ⚠️

Harap perhatikan dengan seksama sebelum menggunakan sistem ini:

1.  **Keterbatasan AI & Potensi Halusinasi:** Kemampuan AI dan sistem *query* saat ini **MASIH TERBATAS** dan **BELUM BISA DIANDALKAN SEPENUHNYA**. Ada risiko signifikan AI menghasilkan informasi yang tidak akurat atau "berhalusinasi" (memberikan jawaban yang terdengar meyakinkan namun salah atau tidak berdasarkan data).

2.  **WAJIB VERIFIKASI ULANG (RECHECK):** Selalu lakukan verifikasi silang dan pengecekan ulang terhadap setiap informasi yang dihasilkan oleh AI dengan merujuk langsung ke **SUMBER DATA ASLI / KITAB REFERENSI** yang ada di database. Jangan pernah menganggap output AI sebagai kebenaran mutlak tanpa pengecekan.

3.  **Gunakan dengan Bijak (WISE USE):** Sistem ini adalah alat bantu, bukan pengganti keahlian dan penelitian mendalam. Gunakan secara bijak dan kritis.

4.  **Pentingnya Bahasa Arab:** Untuk pemahaman yang akurat dan mendalam terhadap teks-teks Turath, penguasaan Bahasa Arab yang baik adalah fundamental. Teruslah belajar dan tingkatkan kemampuan Bahasa Arab Anda.

**Kesimpulan: Sistem ini adalah alat bantu awal. Kehati-hatian, verifikasi, dan pemahaman konteks dari sumber asli adalah kunci.**

## Quick Start

1. **Setup Environment**
   ```bash
   cp config/env.example .env
   # Edit .env with your API keys
   ```

2. **Run with Docker**
   ```bash
   # Using helper script (recommended)
   ./docker-compose-helper.sh up -d
   
   # Or from deployment directory
   cd deployment && docker-compose up -d
   ```

## Project Structure

```
/
├── README.md                    # This file
├── main.py                     # Main application entry
├── pyproject.toml              # Python project config
├── 
├── deployment/                 # Docker & deployment files
├── services/                   # Service implementations
├── data/                       # Database files
├── config/                     # Configuration templates
├── src/                        # Source code
├── scripts/                    # Utility scripts
├── _test_/                     # Test files
└── _documentation_/            # Documentation
```

For detailed deployment instructions, see `deployment/README.md`.
