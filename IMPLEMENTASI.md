# Implementasi: Transposisi Kolom Myszkowski + Dynamic Row Shift

Implementasi dari spesifikasi `br.md`. File:

| File | Isi |
|---|---|
| `myszkowski_dynamic_shift.py` | Implementasi lengkap + CLI |
| `test_myszkowski_dynamic_shift.py` | 51 test (unittest, tanpa dependensi) |

```bash
python3 -m unittest -v test_myszkowski_dynamic_shift   # 51 test, OK
python3 myszkowski_dynamic_shift.py encrypt "PASUKAN SIAP BERANGKAT SEKARANG JUGA" BOROBUDUR
python3 myszkowski_dynamic_shift.py decrypt "<token>" BOROBUDUR
```

## Keputusan desain (br.md §3 — bukan ketentuan PDF)

| Aspek | Keputusan | Cara mengubah |
|---|---|---|
| Kapitalisasi | plaintext & keyword → huruf kapital | — |
| Spasi | dihapus saat normalisasi | — |
| Non A-Z | **ditolak** dengan pesan jelas (mode `strict`) | `mode="strip"` untuk membuang |
| Padding | `X` | parameter `padding_character` |
| Pergeseran | `shift = indeks_baris`, ke kanan, melingkar | sesuai PDF, tidak dikonfigurasi |
| Keyword kosong | ditolak (`MyszkowskiError`) | — |

## API

```python
from myszkowski_dynamic_shift import encrypt, decrypt, encrypt_token, decrypt_token

ct, meta = encrypt("PASUKAN SIAP BERANGKAT SEKARANG JUGA", "BOROBUDUR")
pt = decrypt(ct, "BOROBUDUR", meta)          # -> "PASUKANSIAPBERANGKATSEKARANGJUGA"

token = encrypt_token("HELLO WORLD", "SECRET")   # ciphertext + metadata, 1 string
pt = decrypt_token(token, "SECRET")
```

Fungsi modular sesuai br.md §5: `normalize_text`, `validate_key`,
`generate_key_ranking`, `group_columns_by_rank`, `create_matrix`,
`apply_padding`, `dynamic_row_shift`, `read_myszkowski_columns`, `encrypt`,
`reconstruct_shifted_matrix`, `inverse_row_shift`, `decrypt`.

## Metadata (br.md §7)

`original_length`, `key_length`, `padding_character`, `padding_count`,
`normalization_mode`, `rows`. Dikembalikan sebagai dataclass `Metadata`
(`.to_dict()` / `Metadata.from_dict()` / `.pack(ct)` / `.unpack(token)`).

Metadata **wajib** saat dekripsi: tanpa `original_length`, `X` asli di akhir
plaintext tidak bisa dibedakan dari padding.

## Hasil pengujian

### Ranking (br.md §9.1)
`BOROBUDUR` → `[1, 3, 4, 3, 1, 5, 2, 5, 4]` ✅

### Kelompok kolom (br.md §9.3)
`[[0,4], [6], [1,3], [2,8], [5,7]]` — sama dengan kolom 1&5, 7, 2&4, 3&9, 6&8 ✅

### Dynamic Row Shift (br.md §9.2)
```
ABCD      ABCD
EFGH  ->  HEFG
IJKL      KLIJ
```
✅

### Konsistensi contoh PDF (br.md §9.5)

Ciphertext slide PDF **berhasil direproduksi persis** — jadi ciphertext pada
PDF memang konsisten dengan aturan yang didokumentasikan (bukan asumsi):

```
plaintext : PASUKAN SIAP BERANGKAT SEKARANG JUGA
matriks   : PASUKANSI / APBERANGK / ATSEKARAN / GJUGAXXXX
ciphertext: PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA
pdf       : PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA   MATCH ✅
```

### Round-trip (br.md §9.4)

`decrypt(encrypt(pt)) == normalize_text(pt)` untuk: 1 karakter, lebih pendek
dari keyword, tepat kelipatan keyword, butuh padding, keyword berulang
(`BOROBUDUR`), `X` di akhir, semua `X`, serta **brute-force seluruh string
panjang 1–5 dari alfabet {A,B,X}** dengan keyword `BOROBUDUR`.

### Validasi (br.md §8)

11 kasus ditangani dengan `MyszkowskiError` + pesan jelas (bukan `KeyError`
atau `IndexError`): plaintext kosong, keyword kosong, keyword non-alfabet,
plaintext hanya spasi, ciphertext kosong, metadata hilang/tidak lengkap/
tidak konsisten, panjang keyword tidak cocok, padding char tidak valid,
token rusak.

## Kompleksitas (br.md §10)

N = panjang plaintext, K = panjang keyword, R = ceil(N/K).

| Tahap | Kompleksitas |
|---|---|
| `normalize_text` | O(N) |
| `generate_key_ranking` | O(K log K) |
| `create_matrix` + `apply_padding` | O(N + K) |
| `dynamic_row_shift` | O(N) |
| `read_myszkowski_columns` | O(N) |
| `reconstruct_shifted_matrix` | O(N) |
| `inverse_row_shift` | O(N) |

Total **O(N + K log K)** — linear terhadap panjang teks, konsisten dengan klaim
PDF. Terukur (rata-rata 3 run):

| N | encrypt (ms) | decrypt (ms) | ns/char |
|---:|---:|---:|---:|
| 1 000 | 0,36 | 0,22 | 581 |
| 2 000 | 0,83 | 0,45 | 642 |
| 4 000 | 1,69 | 0,86 | 638 |
| 8 000 | 2,68 | 1,86 | 567 |
| 16 000 | 5,33 | 3,72 | 566 |
| 32 000 | 11,67 | 7,60 | 602 |

`ns/char` datar → linear terkonfirmasi (bukan kuadratik).

## Batasan keamanan (br.md §11)

Ini **transposisi murni**: karakter hanya dipindah, tidak diganti. Karena itu:

- Analisis frekuensi tetap bekerja — distribusi huruf tidak berubah sama sekali.
- Ruang kunci = panjang keyword × pola; sangat kecil, brute-force praktis.
- **Tidak setara AES.** Jangan gunakan untuk data sensitif.
- Untuk sistem nyata: AES-GCM atau ChaCha20-Poly1305 sebagai perlindungan
  utama; metode ini hanya eksperimen/lapisan tambahan.
- Kompleksitas waktu O(N) **tidak** menyatakan kekuatan kriptografis.
