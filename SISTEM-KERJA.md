# Sistem Kerja

Dokumen ini menjelaskan cara kerja internal program: peta file, alur enkripsi dan
dekripsi, format token, alasan metadata wajib, serta perbedaan skrip dinamis dan
statis. Untuk perintah menjalankan program, lihat
[`CARA-MENJALANKAN.md`](CARA-MENJALANKAN.md).

## 1. Peta file dan hubungan skrip

| File | Peran |
|---|---|
| `myszkowski_dynamic_shift.py` | Berisi seluruh algoritma (normalisasi, ranking, matriks, shift, baca kolom, enkripsi, dekripsi, metadata) sekaligus CLI interaktif dengan keyword dan mode yang dapat diisi pengguna. |
| `myszkowski_static_key.py` | CLI tipis yang mengimpor fungsi dari modul di atas. Tidak menyalin algoritma; hanya menetapkan keyword, mode, dan padding tetap. |
| ` play_fair.py` | Program terpisah untuk Super Cipher (Playfair + Zigzag). Cabang menu Myszkowski di dalamnya rusak (lihat catatan di bawah). |
| `test_myszkowski_dynamic_shift.py` | 51 test `unittest` untuk modul Myszkowski. |

Hubungan pemanggilan:

```text
myszkowski_static_key.py
        |  import: encrypt, decrypt_token, MyszkowskiError,
        |          DEFAULT_MODE, DEFAULT_PADDING, print_header
        v
myszkowski_dynamic_shift.py
        |  encrypt() / decrypt() / encrypt_token() / decrypt_token()
        v
normalisasi -> ranking -> matriks -> padding -> shift -> baca kolom
```

`myszkowski_static_key.py` menetapkan konfigurasi berikut, lalu memanggil
`encrypt(plaintext, KEYWORD, padding_character=PADDING, mode=MODE)` atau
`decrypt_token(token, KEYWORD)`:

```python
KEYWORD = "BOROBUDUR"
MODE = DEFAULT_MODE        # "strict"
PADDING = DEFAULT_PADDING  # "X"
```

Karena memakai fungsi yang sama, hasil enkripsi kedua skrip identik untuk
plaintext dan konfigurasi yang sama. Yang berbeda hanya permukaan konfigurasi
dan menu, bukan algoritmanya.

Catatan ` play_fair.py`: cabang Myszkowski-nya memakai nama seperti
`DEFAULT_MODE`, `encrypt_token`, `decrypt_token`, dan `MyszkowskiError` tanpa
mendefinisikan atau mengimpor nama tersebut, sehingga berakhir dengan
`NameError`. File itu tidak memakai modul `myszkowski_dynamic_shift`.

## 2. Pipeline enkripsi

Fungsi `encrypt()` menjalankan urutan berikut. `N` adalah panjang plaintext
setelah normalisasi dan `K` adalah panjang keyword.

### 2.1 Normalisasi plaintext

`normalize_text()` melakukan tiga hal:

1. Membuang semua whitespace (`"".join(text.split())`), bukan hanya spasi di
   awal/akhir.
2. Mengubah sisa teks menjadi huruf kapital.
3. Menangani karakter selain A-Z:
   - mode `strict`: ditolak dengan `MyszkowskiError` yang menyebut karakter
     bermasalah dan menyarankan `mode='strip'`;
   - mode `strip`: karakter tersebut dibuang.

Nilai `N` dihitung dari hasil langkah ini, sehingga spasi tidak ikut dihitung.

### 2.2 Validasi keyword

`validate_key()` membuang whitespace, mengubah ke huruf kapital, menolak keyword
kosong, dan menolak karakter selain A-Z. `K` adalah panjang keyword setelah
normalisasi ini.

### 2.3 Ranking huruf keyword

`generate_key_ranking()` mengambil huruf unik, mengurutkannya secara alfabetis,
memberi ranking mulai dari 1, lalu memetakan ranking itu ke posisi asli setiap
huruf. Huruf kembar mendapat ranking sama. Contoh `BOROBUDUR`:

| Posisi | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| Huruf | B | O | R | O | B | U | D | U | R |
| Ranking | 1 | 3 | 4 | 3 | 1 | 5 | 2 | 5 | 4 |

### 2.4 Pengelompokan kolom

`group_columns_by_rank()` mengelompokkan indeks kolom (0-based) menurut ranking,
urut dari ranking terkecil. Untuk `BOROBUDUR` hasilnya
`[[0, 4], [6], [1, 3], [2, 8], [5, 7]]`.

### 2.5 Pembentukan matriks

`create_matrix()` menyusun teks horizontal dari kiri ke kanan dengan jumlah
kolom `K`. Jumlah baris:

```text
R = ceil(N / K)
```

Sel yang belum terisi dibiarkan kosong pada tahap ini.

### 2.6 Padding

`apply_padding()` mengisi setiap sel kosong dengan karakter padding (default
`X` dari CLI) dan menghitung berapa sel yang diisi. Jumlah padding disimpan di
metadata, meskipun nanti tidak dipakai untuk memotong hasil dekripsi.

### 2.7 Dynamic Row Shift

`dynamic_row_shift()` menggeser baris ke-i ke kanan sejauh `i` posisi secara
melingkar, dengan indeks baris mulai dari 0 (ekuivalen dengan `i - 1` pada
penomoran PDF). Rumusnya:

```text
matriks_baru[i][j] = matriks_lama[i][(j - i) mod K]
```

Baris pertama tidak bergeser. Matriks baru dibentuk tanpa mengubah matriks
masukan.

### 2.8 Pembacaan kolom Myszkowski

`read_myszkowski_columns()` membaca matriks hasil shift sesuai kelompok ranking:

- kelompok berisi satu kolom: dibaca vertikal dari baris atas ke bawah;
- kelompok berisi beberapa kolom: dibaca horizontal per baris, kolom kiri ke
  kanan.

Semua karakter digabungkan menjadi ciphertext.

### 2.9 Contoh satu putaran penuh

Plaintext `PASUKAN SIAP BERANGKAT SEKARANG JUGA` (N = 32 setelah normalisasi)
dengan keyword `BOROBUDUR` (K = 9) menghasilkan matriks 4 baris sebelum shift:

```text
P A S U K A N S I
A P B E R A N G K
A T S E K A R A N
G J U G A X X X X
```

Setelah shift (baris 0 tetap, baris 1 geser 1, baris 2 geser 2, baris 3
geser 3):

```text
P A S U K A N S I
K A P B E R A N G
A N A T S E K A R
X X X G J U G A X
```

Pembacaan per kelompok menghasilkan ciphertext
`PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA`. Metadata yang menyertainya:
`original_length=32`, `key_length=9`, `padding_character=X`,
`padding_count=4`, `normalization_mode=strict`, `rows=4`.

Keluaran CLI mencetak **METADATA**, lalu **TOKEN**, lalu **HASIL ENKRIPSI**
(ciphertext mentah di baris terakhir). Token adalah gabungan ciphertext dan
metadata dalam satu string.

## 3. Pipeline dekripsi

`decrypt()` membalik urutan enkripsi. `decrypt_token()` lebih dulu memecah token
menjadi ciphertext dan objek `Metadata`, lalu memanggil `decrypt()`.

### 3.1 Membaca token

`Metadata.unpack()` memecah token pada karakter `|`. Token harus terdiri dari
tepat 8 bagian dan bagian pertama harus `MDRS1`; jika tidak,
`MyszkowskiError` dengan pesan `Token tidak valid. Format: ...` dilempar.
Field yang hilang saat membentuk metadata juga ditolak
(`Metadata tidak lengkap: field ... tidak ditemukan.`).

### 3.2 Validasi keyword dan ukuran

1. Keyword dinormalisasi seperti saat enkripsi.
2. Panjang keyword harus sama dengan `key_length` di metadata. Jika tidak:
   `Panjang keyword (n) tidak cocok dengan metadata (m).`
3. Ranking dan kelompok kolom dihitung ulang dari keyword.
4. Matriks berukuran `rows x key_length`. Jika
   `rows * key_length != len(ciphertext)`, metadata dianggap tidak konsisten.
5. `original_length` tidak boleh melebihi panjang ciphertext.

Pemeriksaan ini mendeteksi metadata yang tidak konsisten, tetapi tidak
mendeteksi perubahan oleh pihak ketiga (lihat bagian 7).

### 3.3 Rekonstruksi matriks hasil shift

`reconstruct_shifted_matrix()` membuat matriks kosong `rows x key_length` lalu
mengisi sel mengikuti urutan baca Myszkowski yang sama dengan enkripsi. Hasilnya
adalah matriks tepat setelah Dynamic Row Shift.

### 3.4 Inverse shift, penggabungan, dan pemotongan

1. `inverse_row_shift()` menggeser setiap baris ke kiri sejauh indeks barisnya:
   `matriks_asli[i][j] = matriks_shift[i][(j + i) mod K]`.
2. Semua baris digabung horizontal menjadi satu string.
3. String dipotong sepanjang `original_length`, sehingga padding terbuang dan
   karakter `X` asli di akhir plaintext tetap aman.

Dari enam field metadata, `decrypt()` memakai `original_length`, `key_length`,
dan `rows`. `padding_character`, `padding_count`, dan `normalization_mode`
hanya dibawa sebagai informasi/audit dan tidak dibaca oleh `decrypt()`.

## 4. Format token dan arti field

Token adalah satu baris dengan pemisah `|`:

```text
MDRS1|<ciphertext>|<original_length>|<key_length>|<padding_character>|<padding_count>|<mode>|<rows>
```

Contoh:

```text
MDRS1|PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA|32|9|X|4|strict|4
```

| Bagian | Field | Arti | Dipakai saat dekripsi |
|---|---|---|---|
| 1 | `MDRS1` | Penanda versi/format token. | Ya, harus sama persis. |
| 2 | `ciphertext` | Hasil enkripsi; panjangnya `rows x key_length`. | Ya. |
| 3 | `original_length` | Panjang plaintext setelah normalisasi (kapital, tanpa spasi). | Ya, untuk memotong padding. |
| 4 | `key_length` | Jumlah kolom matriks. | Ya, dicek terhadap panjang keyword. |
| 5 | `padding_character` | Karakter padding yang dipakai saat enkripsi. | Tidak. |
| 6 | `padding_count` | Jumlah karakter padding. | Tidak. |
| 7 | `mode` | Mode normalisasi (`strict`/`strip`). | Tidak. |
| 8 | `rows` | Jumlah baris matriks. | Ya, untuk menyusun matriks. |

Karena plaintext hanya berisi A-Z, ciphertext tidak mengandung `|`. Field lain
berisi angka, satu karakter padding, atau nama mode; token yang dihasilkan CLI
memakai padding `X`, sehingga pemisah aman untuk format ini.

## 5. Mengapa metadata wajib

Ciphertext saja tidak cukup untuk memulihkan plaintext. Bukti sederhana memakai
keyword `KEY`, plaintext `HALO` dan `HALOX`:

| Plaintext | `original_length` | Matriks setelah padding | Ciphertext | Setelah inverse shift | Hasil akhir |
|---|---|---:|---|---|---|
| `HALO` | 4 | `HAL` / `OXX` | `AOHXLX` | `HALOXX` | `HALO` |
| `HALOX` | 5 | `HAL` / `OXX` | `AOHXLX` | `HALOXX` | `HALOX` |

Kedua plaintext menghasilkan ciphertext yang sama, `AOHXLX`, karena `X` asli
pada `HALOX` menempati sel yang sama dengan karakter padding. Tanpa
`original_length`, hasil gabungan keduanya sama-sama `HALOXX` dan tidak ada cara
membedakan mana `X` asli dan mana padding. Dengan metadata, pemotongan 4
karakter menghasilkan `HALO`, sedangkan 5 karakter menghasilkan `HALOX`.

`decrypt()` bahkan menolak dipanggil tanpa metadata:
`Metadata wajib disertakan saat dekripsi (butuh original_length).` Karena itu
token selalu membawa metadata, dan ciphertext mentah saja tidak bisa didekripsi
lewat menu.

## 6. Perbandingan skrip dinamis dan statis

Keduanya memakai algoritma dan fungsi yang sama. Perbedaannya hanya pada apa
yang dapat diubah pengguna.

| Aspek | `myszkowski_dynamic_shift.py` | `myszkowski_static_key.py` |
|---|---|---|
| Sumber algoritma | Modul lengkap. | Mengimpor modul yang sama. |
| Keyword | Diketik pengguna. | Tetap `BOROBUDUR` (9 huruf). |
| Mode normalisasi | Diketik `strict`/`strip`; nilai lain jatuh ke `strict`. | Tetap `strict`. |
| Padding dari CLI | Tetap `X`. | Tetap `X`. |
| Input saat enkripsi | Plaintext, keyword, mode. | Hanya plaintext. |
| Input saat dekripsi | Token dan keyword. | Hanya token. |
| Menu | `1` enkripsi, `2` dekripsi. | `1` enkripsi, `2` dekripsi, `0` keluar. |
| Header | `MYSZKOWSKI + DYNAMIC ROW SHIFT` | `MYSZKOWSKI + DYNAMIC ROW SHIFT (STATIC KEY)` |
| Token yang bisa didekripsi | Semua token; hasil benar bila keyword yang diketik sama. | Hanya token dengan `key_length` 9; panjang keyword berbeda menghasilkan error. |
| Urutan keluaran enkripsi | METADATA -> TOKEN -> HASIL ENKRIPSI. | METADATA -> TOKEN -> HASIL ENKRIPSI. |

Catatan penting: pemeriksaan dekripsi hanya membandingkan **panjang** keyword
dengan `key_length`. Token yang dibuat dengan keyword lain tetapi panjangnya
sama (misalnya sesama 9 huruf) tidak memicu error; hasilnya hanya berupa
plaintext yang salah karena ranking kolomnya berbeda. Metadata tidak diautentikasi.

## 7. Batasan keamanan

- Ini transposisi murni: karakter hanya dipindah, tidak diganti. Distribusi
  frekuensi huruf tidak berubah, sehingga analisis frekuensi tetap berlaku.
- Ruang kunci sangat kecil (bergantung pada keyword dan polanya), sehingga
  brute-force praktis.
- Metadata dan token tidak diautentikasi (tidak ada MAC/tanda tangan).
  Pemeriksaan dekripsi hanya menilai konsistensi ukuran, bukan keaslian. Token
  dapat diubah dan tetap diproses selama ukurannya konsisten.
- Karena itu metode ini tidak setara AES dan tidak layak untuk melindungi data
  sensitif atau menjaga integritas. Untuk pemakaian nyata gunakan AES-GCM atau
  ChaCha20-Poly1305 sebagai lapisan utama; algoritma ini hanya untuk
  eksperimen/penelitian.
