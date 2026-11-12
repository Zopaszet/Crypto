# Cara Menjalankan Proyek

Panduan ini menjelaskan cara menyiapkan lingkungan, menjalankan kedua skrip, dan
menjalankan test suite di repositori ini. Semua perintah dijalankan dari
direktori root repositori.

## Isi repositori

| File | Isi |
|---|---|
| `myszkowski_dynamic_shift.py` | Modul Myszkowski + Dynamic Row Shift beserta CLI interaktif (enkripsi/dekripsi). |
| ` play_fair.py` | Menu "Kryptos": Super Cipher (Playfair + Zigzag) dan entri Myszkowski. **Nama file diawali satu spasi.** |
| `test_myszkowski_dynamic_shift.py` | 51 test `unittest` untuk modul Myszkowski. |
| `br.md` | Spesifikasi/rancangan algoritma (acuan implementasi). |
| `IMPLEMENTASI.md` | Catatan implementasi dan hasil pengujian. |

## 1. Prasyarat

- Python 3.7 atau lebih baru. Kode memakai `dataclasses` dan
  `from __future__ import annotations`, keduanya tersedia sejak Python 3.7.
- Tidak ada dependensi pihak ketiga. Impor yang dipakai hanya pustaka standar:
  `math`, `string`, `dataclasses`, `typing` (modul utama) dan `unittest` (test).
- Tidak ada `requirements.txt`, `pyproject.toml`, `setup.py`, maupun konfigurasi
  paket lain, jadi tidak perlu `pip install`, virtualenv, atau koneksi internet.
- Terminal sebaiknya mendukung UTF-8 karena program mencetak karakter kotak
  (`┌`, `│`, `└`).

Masuk ke root repositori:

```bash
cd /home/zet/Projects/kripto
```

## 2. Menjalankan `myszkowski_dynamic_shift.py`

Skrip ini sepenuhnya interaktif: seluruh input dibaca lewat `input()`. Skrip
tidak menerima argumen posisi atau flag apa pun (`_main()` menerima parameter
`argv` tetapi tidak pernah memakainya).

```bash
python3 myszkowski_dynamic_shift.py
```

Setelah header kotak, tampil menu:

```text
[+] Pilih menu
    Pilihan (1/2):
```

### 2.1 Enkripsi (pilih `1`)

Program menanyakan tiga hal:

| Prompt | Isi |
|---|---|
| `Plaintext : ` | Teks yang akan dienkripsi. |
| `Keyword   : ` | Hanya huruf A-Z. Spasi diabaikan dan huruf kecil diubah ke kapital. |
| `Mode [strict/strip] (tekan Enter untuk default 'strict'): ` | Ketik `strict` atau `strip`; kosongkan (Enter) untuk `strict`. |

Perilaku mode:

- `strict` (default): plaintext yang setelah spasi dihapus masih mengandung
  karakter selain A-Z akan ditolak dengan pesan error.
- `strip`: karakter selain A-Z dibuang, spasi tetap dihapus.
- Nilai lain (misalnya `STRICT` atau salah ketik) tidak memunculkan error;
  program diam-diam memakai `strict`.

Spasi selalu dihapus saat normalisasi, sehingga `HELLO WORLD` menjadi
`HELLOWORLD`.

Contoh sesi lengkap:

```text
[+] Pilih menu
    Pilihan (1/2): 1

[+] Masukkan data untuk Enkripsi
   Plaintext : PASUKAN SIAP BERANGKAT SEKARANG JUGA
   Keyword   : BOROBUDUR
   Mode [strict/strip] (tekan Enter untuk default 'strict'):

  HASIL ENKRIPSI:
  PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA

  METADATA:
    original_length    : 32
    key_length         : 9
    padding_character  : X
    padding_count      : 4
    normalization_mode : strict
    rows               : 4

  TOKEN (untuk menu Dekripsi):
  MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4
```

Keluaran enkripsi menampilkan ciphertext mentah sebagai hasil utama, diikuti
metadata dari objek `Metadata`, lalu token portabel pada baris terakhir. Token
inilah yang dipakai untuk dekripsi. Formatnya:

```text
MDRS1|<ciphertext>|<original_length>|<key_length>|<padding_character>|<padding_count>|<mode>|<rows>
```

Pada contoh di atas: ciphertext 36 karakter, panjang plaintext ternormalisasi 32,
keyword 9 huruf, padding `X` sebanyak 4, mode `strict`, matriks 4 baris.
Karakter padding di CLI selalu `X` (tidak bisa diubah dari menu).

### 2.2 Dekripsi (pilih `2`)

Dekripsi membutuhkan **token lengkap** (ciphertext + metadata) dan keyword yang
sama seperti saat enkripsi. Ciphertext mentah tanpa metadata tidak bisa
didekripsi lewat menu ini.

```text
[+] Pilih menu
    Pilihan (1/2): 2

[+] Masukkan data untuk Dekripsi
   Token     : MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4
   Keyword   : BOROBUDUR

  HASIL PLAINTEXT:
  PASUKANSIAPBERANGKATSEKARANGJUGA
```

Hasil dekripsi selalu dalam bentuk ternormalisasi: huruf kapital dan tanpa
spasi. Spasi asli tidak dapat dikembalikan karena tidak disimpan.

### 2.3 Error dan kode keluar

- Input tidak valid: pesan `[ERROR] ...` dicetak ke stderr, proses berhenti
  dengan kode keluar `2`.
- Pilihan menu selain `1`/`2`: pesan `[!] Pilihan menu tidak valid.`, kode
  keluar `0`.

Contoh penolakan mode `strict`:

```bash
printf '1\nHALO123\nKEY\n\n' | python3 myszkowski_dynamic_shift.py
```

```text
[ERROR] Plaintext mengandung karakter yang tidak didukung: '1', '2', '3'. Gunakan hanya A-Z dan spasi, atau pilih mode='strip'.
```

## 3. Menjalankan `" play_fair.py"`

Nama file diawali satu spasi. Path **wajib dikutip**, jika tidak shell akan
mencari `play_fair.py` (tanpa spasi) dan gagal.

```bash
python3 " play_fair.py"
```

Bentuk lain yang setara: `python3 ./" play_fair.py"`. Saat memakai tab
completion, ketik `python3 ./` lalu Tab agar shell mengutip nama file otomatis.

Menu yang muncul:

```text
[+] Pilih program
    Pilihan (0-2):
```

| Pilihan | Isi |
|---|---|
| `1` | Super Cipher (Playfair + Zigzag 3 rail) |
| `2` | Myszkowski Columnar Transposition + Dynamic Row Shift |
| `0` | Keluar |

Catatan penting:

- Pilihan `2` **tidak berfungsi** pada file ini. Cabang tersebut memakai
  `DEFAULT_MODE`, `encrypt_token`, `decrypt_token`, dan `MyszkowskiError` yang
  tidak didefinisikan maupun diimpor di ` play_fair.py`, sehingga setelah
  plaintext, keyword, dan mode diisi program berhenti dengan `NameError`. Untuk
  Myszkowski, gunakan `myszkowski_dynamic_shift.py`.
- Pilihan `1` berjalan lokal tanpa dependensi. Tabel Playfair di sini berukuran
  10x10 dengan alfabet 100 karakter (huruf besar, huruf kecil, angka, tanda
  baca, beberapa simbol, dan spasi), bukan 5x5 klasik.
- Tidak ada normalisasi input pada pilihan `1`. Karakter di luar alfabet 100
  karakter tersebut menyebabkan `KeyError`, dan karakter keyword yang tidak ada
  di alfabet diabaikan.
- Saat mengenkripsi, pasangan huruf kembar dan panjang ganjil diisi `X`.
  Dekripsi tidak membuang `X` sisipan itu. Panjang ciphertext yang dimasukkan
  harus genap.

Contoh pilihan `1` (enkripsi `AB` dengan keyword `KEY`):

```bash
printf '1\n1\nAB\nKEY\n' | python3 " play_fair.py"
```

```text
  HASIL CIPHERTEXT:
  BC
```

## 3.1 Menjalankan `myszkowski_static_key.py`

Versi ringkas yang sama sekali tidak menanyakan keyword, mode, atau padding:
keyword dipatok `BOROBUDUR`, mode `strict`, dan padding `X`, sehingga pengguna
hanya mengetik plaintext (enkripsi) atau token (dekripsi). Token hanya bisa
didekripsi bila dibuat dengan keyword tersebut.

```bash
python3 myszkowski_static_key.py
```

Menu yang muncul:

```text
[+] Pilih menu
    Pilihan (1/2/0):
```

| Pilihan | Isi |
|---|---|
| `1` | Enkripsi (Plaintext -> Token) |
| `2` | Dekripsi (Token -> Plaintext) |
| `0` | Keluar |

Contoh enkripsi (hanya satu input, yaitu plaintext):

```bash
printf '1\nPASUKAN SIAP BERANGKAT SEKARANG JUGA\n' | python3 myszkowski_static_key.py
```

```text
  HASIL ENKRIPSI:
  PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA

  METADATA:
    original_length    : 32
    key_length         : 9
    padding_character  : X
    padding_count      : 4
    normalization_mode : strict
    rows               : 4

  TOKEN (untuk menu Dekripsi):
  MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4
```

Pada menu `2`, cukup tempel token; hasilnya dicetak sebagai
`HASIL PLAINTEXT:` diikuti teks ternormalisasi (kapital, tanpa spasi).
Pilihan `0` keluar dengan kode `0`, pilihan tak dikenal mencetak
`[!] Pilihan menu tidak valid.` dan juga keluar dengan kode `0`, sedangkan
input tidak valid mencetak `[ERROR] ...` ke stderr dan keluar dengan kode `2`.

## 4. Menjalankan test suite

Test memakai `unittest` bawaan Python (tidak ada `pytest`), dan file test punya
blok `if __name__ == "__main__"`. Ada 51 test. Jalankan dari root repositori:

```bash
python3 -m unittest -v test_myszkowski_dynamic_shift
```

Alternatif yang setara:

```bash
python3 test_myszkowski_dynamic_shift.py
```

Untuk menjalankan satu kelas test saja:

```bash
python3 -m unittest -v test_myszkowski_dynamic_shift.TestRoundTrip
```

Akhir keluaran jika semua lulus (durasi berbeda tiap mesin):

```text
----------------------------------------------------------------------
Ran 51 tests in 0.0xx s

OK
```

Jika muncul `ModuleNotFoundError: No module named 'myszkowski_dynamic_shift'`,
berarti perintah dijalankan di luar root repositori.

## 5. Contoh kerja: enkripsi lalu dekripsi

Contoh ini memakai plaintext dan keyword yang sama dengan fixture
`TestPDFExample` di file test, sehingga hasilnya bisa dicocokkan.

Langkah 1, enkripsi non-interaktif dengan mengalirkan input:

```bash
printf '1\nPASUKAN SIAP BERANGKAT SEKARANG JUGA\nBOROBUDUR\n\n' | python3 myszkowski_dynamic_shift.py
```

Empat baris input berurutan adalah: pilihan menu, plaintext, keyword, dan mode
(kosong berarti `strict`). Karena stdin berupa pipe, prompt `input()` tetap
dicetak tetapi tidak diikuti baris baru, jadi beberapa prompt terlihat menyatu.
Baris hasilnya:

```text
  HASIL ENKRIPSI:
  PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA

  METADATA:
    original_length    : 32
    key_length         : 9
    padding_character  : X
    padding_count      : 4
    normalization_mode : strict
    rows               : 4

  TOKEN (untuk menu Dekripsi):
  MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4
```

Langkah 2, dekripsi token tersebut:

```bash
printf '2\nMDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4\nBOROBUDUR\n' | python3 myszkowski_dynamic_shift.py
```

```text
  HASIL PLAINTEXT:
  PASUKANSIAPBERANGKATSEKARANGJUGA
```

Langkah 3, cek cepat lewat API Python:

```bash
python3 -c 'from myszkowski_dynamic_shift import decrypt_token; print(decrypt_token("MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4", "BOROBUDUR"))'
```

```text
PASUKANSIAPBERANGKATSEKARANGJUGA
```

Langkah 4, jalankan seluruh test (bagian 4). Jika berakhir dengan `OK`, setup
sudah benar.

## 6. Catatan dan troubleshooting

| Gejala | Penyebab dan solusi |
|---|---|
| `can't open file .../play_fair.py` | Nama file diawali spasi. Gunakan `python3 " play_fair.py"`. |
| `NameError` saat memilih menu `2` di ` play_fair.py` | Cabang Myszkowski memakai nama yang tidak didefinisikan (`DEFAULT_MODE`, `encrypt_token`, `decrypt_token`, `MyszkowskiError`). Gunakan `python3 myszkowski_dynamic_shift.py`. |
| `[ERROR] Plaintext mengandung karakter yang tidak didukung: ...` | Mode `strict` menolak karakter selain A-Z. Hapus karakter tersebut atau pilih mode `strip`. |
| `[ERROR] Plaintext tidak boleh kosong.` | Plaintext kosong; isi minimal satu karakter A-Z. |
| `[ERROR] Plaintext kosong setelah normalisasi ...` | Mode `strip` membuang semua karakter yang dimasukkan. |
| `[ERROR] Keyword hanya boleh berisi huruf A-Z.` | Keyword mengandung angka/tanda baca. Gunakan huruf saja. |
| `[ERROR] Keyword tidak boleh kosong.` | Keyword kosong atau hanya spasi. |
| `[ERROR] Token tidak valid.` | Yang dimasukkan bukan token lengkap (misalnya hanya ciphertext). Salin seluruh token hasil enkripsi. |
| `[ERROR] Panjang keyword (...) tidak cocok dengan metadata (...)` | Keyword dekripsi harus sama panjang dengan keyword saat enkripsi. |
| `[ERROR] Metadata tidak konsisten: ...` | Token rusak/terpotong (misalnya pemisah antar-field hilang). Enkripsi ulang. |
| Mode yang diketik salah ketik tetap berjalan sebagai `strict` | Perilaku normal: hanya `strip` yang dikenali selain default. |

Hal lain yang perlu diketahui:

- `IMPLEMENTASI.md` memuat contoh seperti
  `python3 myszkowski_dynamic_shift.py encrypt "..." BOROBUDUR`. Bentuk itu
  **tidak berlaku** untuk skrip saat ini karena skrip hanya membaca input dari
  prompt interaktif; argumen posisi diabaikan dan menu akan menunggu input.
- Algoritma ini murni transposisi (memindahkan posisi karakter, bukan
  menggantinya), sehingga tidak layak untuk melindungi data sensitif. Gunakan
  algoritma terstandar seperti AES-GCM untuk keperluan nyata.
