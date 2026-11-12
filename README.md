# Kripto — Myszkowski + Dynamic Row Shift

Implementasi referensi akademik untuk sandi transposisi kolom Myszkowski yang
ditambah *Dynamic Row Shift*, yaitu pergeseran melingkar setiap baris matriks
sejauh indeks barisnya. Repositori berisi dua CLI Myszkowski, satu test suite, dan
dokumentasi berbahasa Indonesia. Kode hanya memakai pustaka standar Python 3.7+,
tanpa dependensi pihak ketiga.

## Mulai cepat

```bash
python3 myszkowski_static_key.py
python3 -m unittest -v test_myszkowski_dynamic_shift
```

Skrip pertama memakai keyword tetap `BOROBUDUR`, mode `strict`, dan padding `X`.
Contoh keluaran enkripsi (dipotong) untuk plaintext
`PASUKAN SIAP BERANGKAT SEKARANG JUGA`:

```text
  TOKEN (untuk menu Dekripsi):
  MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4

  HASIL ENKRIPSI:
  PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA
```

Test suite berisi 51 test dan berakhir dengan `OK`.

## Skrip

| Perintah | Fungsi |
|---|---|
| `python3 myszkowski_dynamic_shift.py` | CLI interaktif penuh: enkripsi meminta plaintext, keyword, dan mode (`strict`/`strip`); dekripsi meminta token dan keyword. |
| `python3 myszkowski_static_key.py` | CLI ringkas: keyword `BOROBUDUR`, mode `strict`, padding `X`; enkripsi hanya meminta plaintext, dekripsi hanya token; menu `1/2/0`. |
| `python3 " play_fair.py"` | Demo terpisah Playfair + Zigzag. Nama file diawali satu spasi, jadi path wajib dikutip. |

## Struktur repositori

| File | Peran |
|---|---|
| `myszkowski_dynamic_shift.py` | Modul algoritma lengkap sekaligus CLI interaktif. |
| `myszkowski_static_key.py` | CLI tipis di atas modul tersebut dengan konfigurasi tetap. |
| `test_myszkowski_dynamic_shift.py` | 51 test `unittest` untuk modul Myszkowski. |
| `br.md` | Spesifikasi dan rancangan algoritma (acuan implementasi). |
| `IMPLEMENTASI.md` | Catatan implementasi, API, hasil pengujian, dan kompleksitas. |
| `SISTEM-KERJA.md` | Penjelasan pipeline, format token, dan perbandingan dinamis vs statis. |
| `CARA-MENJALANKAN.md` | Panduan menjalankan program, contoh sesi, dan troubleshooting. |
| ` play_fair.py` | Program terpisah Super Cipher (Playfair + Zigzag). |
| `README.md` | Halaman masuk repositori ini. |

## Dokumentasi

- [`CARA-MENJALANKAN.md`](CARA-MENJALANKAN.md) — cara pakai, prompt, contoh sesi, dan troubleshooting.
- [`SISTEM-KERJA.md`](SISTEM-KERJA.md) — algoritma, format token, serta perbandingan skrip dinamis dan statis.
- [`br.md`](br.md) — spesifikasi dan rancangan algoritma.
- [`IMPLEMENTASI.md`](IMPLEMENTASI.md) — catatan implementasi dan hasil pengujian.

## Catatan

- Metadata wajib saat dekripsi: plaintext `HALO` dan `HALOX` dengan keyword `KEY`
  sama-sama menghasilkan ciphertext `AOHXLX`; hanya `original_length` (4 vs 5)
  yang membedakan hasilnya.
- Menu `2` pada ` play_fair.py` tidak berfungsi karena memakai nama yang tidak
  didefinisikan (`NameError`); gunakan salah satu skrip Myszkowski di atas.
- Ini transposisi klasik dengan metadata tanpa autentikasi, bukan untuk rahasia
  nyata; gunakan AES-GCM untuk keperluan sungguhan.

Belum ada lisensi.
