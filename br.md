from pathlib import Path

content = r"""# Spesifikasi Implementasi
## Pengembangan Transposisi Kolom Myszkowski dengan Dynamic Row Shift

Dokumen ini menjadi panduan untuk membangun program berdasarkan PDF **Pengembangan Transposisi Kolom Myszkowski: Peningkatan Difusi Sandi Berbasis Dynamic Row Shift**.

Dokumen ini berisi rancangan, aturan algoritma, pembagian fungsi, alur enkripsi dan dekripsi, serta rencana pengujian. Dokumen ini **belum berisi implementasi kode program**.

---

## 1. Tujuan program

Membangun program yang dapat:

1. Menerima plaintext dan keyword.
2. Mengubah keyword menjadi ranking alfabet.
3. Menyusun plaintext ke dalam matriks.
4. Menggeser setiap baris secara dinamis.
5. Membaca matriks menggunakan aturan transposisi kolom Myszkowski.
6. Menghasilkan ciphertext.
7. Melakukan dekripsi untuk merekonstruksi plaintext.
8. Menguji apakah proses dekripsi mengembalikan plaintext sesuai aturan normalisasi yang dipilih.

Fokus pengembangan adalah penambahan **Dynamic Row Shift** sebelum proses pembacaan kolom Myszkowski.

## 2. Dasar metode dari PDF

PDF menjelaskan tiga langkah utama:

1. **Matriks Grid**: teks disusun secara horizontal dari kiri ke kanan.
2. **Dynamic Row Shift**: baris ke-i digeser ke kanan sebanyak `i - 1` posisi.
3. **Baca Myszkowski**: kolom dibaca berdasarkan ranking keyword. Kolom dengan ranking sama dibaca secara horizontal antarkolom dalam kelompok tersebut.

PDF menggunakan keyword contoh:

`BOROBUDUR`

Ranking yang ditampilkan:

| Posisi kolom | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Huruf | B | O | R | O | B | U | D | U | R |
| Ranking | 1 | 3 | 4 | 3 | 1 | 5 | 2 | 5 | 4 |

Dengan demikian, kelompok kolom berdasarkan ranking adalah:

| Ranking | Kolom (indeks mulai dari 1) |
|---:|---|
| 1 | 1 dan 5 |
| 2 | 7 |
| 3 | 2 dan 4 |
| 4 | 3 dan 9 |
| 5 | 6 dan 8 |

## 3. Ketentuan dan keputusan desain

PDF belum menetapkan seluruh detail implementasi. Agar program konsisten, gunakan keputusan awal berikut dan jadikan sebagai konfigurasi yang mudah diubah.

| Aspek | Keputusan awal yang disarankan | Status |
|---|---|---|
| Kapitalisasi | Ubah huruf menjadi kapital | Perlu dikonfirmasi |
| Spasi | Hapus spasi saat enkripsi | Perlu dikonfirmasi |
| Karakter selain A-Z | Tolak atau tetapkan aturan normalisasi khusus | Belum ditentukan PDF |
| Padding | Gunakan `X` untuk mengisi sel terakhir yang kosong | Contoh PDF menggunakan X |
| Pergeseran baris | Baris pertama 0, baris kedua 1, baris ketiga 2, dan seterusnya | Sesuai PDF |
| Arah pergeseran | Ke kanan dan melingkar (circular shift) | Sesuai ilustrasi PDF |
| Panjang plaintext asli | Simpan sebagai metadata agar padding dapat dibuang secara tepat | Rancangan implementasi |
| Keyword kosong | Tolak sebagai input tidak valid | Validasi program |

**Penting:** PDF tidak menjelaskan cara mempertahankan spasi, angka, tanda baca, maupun panjang plaintext asli. Jangan menganggap keputusan pada tabel sebagai ketentuan asli PDF. Dokumentasikan keputusan final pada program.

## 4. Alur umum program

### 4.1 Alur enkripsi

`Plaintext + Keyword`
→ normalisasi plaintext
→ validasi keyword
→ ranking keyword
→ pembentukan matriks
→ padding
→ Dynamic Row Shift
→ pembacaan Myszkowski
→ ciphertext.

### 4.2 Alur dekripsi

`Ciphertext + Keyword + metadata yang diperlukan`
→ validasi input
→ ranking keyword
→ hitung ukuran matriks
→ rekonstruksi matriks hasil shift berdasarkan urutan baca Myszkowski
→ inverse Dynamic Row Shift
→ gabungkan baris
→ buang padding berdasarkan panjang plaintext asli
→ plaintext hasil dekripsi.

Dekripsi membutuhkan informasi panjang plaintext asli atau metadata setara. Tanpa informasi tersebut, karakter `X` asli di akhir plaintext tidak dapat dibedakan secara pasti dari karakter padding.

## 5. Rancangan fungsi

Buat program secara modular. Nama fungsi berikut merupakan usulan, bukan ketentuan dari PDF.

| No. | Fungsi | Tanggung jawab | Masukan | Keluaran |
|---:|---|---|---|---|
| 1 | `normalize_text()` | Menormalisasi plaintext sesuai kebijakan program | Plaintext | Plaintext normal |
| 2 | `validate_key()` | Memastikan keyword valid dan tidak kosong | Keyword | Keyword valid atau kesalahan |
| 3 | `generate_key_ranking()` | Menghasilkan ranking setiap karakter keyword | Keyword | Daftar ranking |
| 4 | `group_columns_by_rank()` | Mengelompokkan indeks kolom berdasarkan ranking | Daftar ranking | Kelompok kolom terurut |
| 5 | `create_matrix()` | Menyusun plaintext secara horizontal | Plaintext, jumlah kolom | Matriks |
| 6 | `apply_padding()` | Melengkapi matriks ke ukuran persegi panjang | Matriks, karakter padding | Matriks lengkap dan jumlah padding |
| 7 | `dynamic_row_shift()` | Menggeser baris ke kanan sesuai indeks baris | Matriks | Matriks hasil shift |
| 8 | `read_myszkowski_columns()` | Membaca matriks berdasarkan kelompok ranking | Matriks, kelompok kolom | Ciphertext |
| 9 | `encrypt()` | Mengatur seluruh proses enkripsi | Plaintext, keyword | Ciphertext dan metadata |
| 10 | `reconstruct_shifted_matrix()` | Mengisi matriks hasil shift dari ciphertext sesuai urutan baca | Ciphertext, ranking, ukuran matriks | Matriks hasil shift |
| 11 | `inverse_row_shift()` | Membatalkan Dynamic Row Shift | Matriks hasil shift | Matriks sebelum shift |
| 12 | `decrypt()` | Mengatur seluruh proses dekripsi | Ciphertext, keyword, metadata | Plaintext |

## 6. Aturan algoritma secara rinci

### 6.1 Ranking keyword

Tujuan: setiap huruf yang sama mendapat ranking yang sama.

Langkah:

1. Ubah keyword menjadi kapital.
2. Ambil huruf unik.
3. Urutkan huruf unik secara alfabetis.
4. Berikan ranking mulai dari 1 berdasarkan urutan alfabetis.
5. Petakan ranking setiap huruf ke posisi aslinya pada keyword.

Contoh:

- Keyword: `BOROBUDUR`
- Huruf unik terurut: `B, D, O, R, U`
- Pemetaan: `B=1, D=2, O=3, R=4, U=5`
- Hasil ranking: `[1, 3, 4, 3, 1, 5, 2, 5, 4]`

Kriteria benar: hasil ranking harus sama dengan daftar di atas.

### 6.2 Pembentukan matriks

Misalkan:

- `N` = jumlah karakter plaintext setelah normalisasi.
- `K` = panjang keyword.
- `R` = jumlah baris matriks.

Jumlah baris:

`R = ceil(N / K)`

Susun karakter plaintext dari kiri ke kanan dan lanjut ke baris berikutnya. Jika sel terakhir belum penuh, isi dengan karakter padding yang telah ditentukan.

Contoh struktur untuk keyword 9 karakter:

```text
P A S U K A N S I
A P B E R A N G K
A T S E K A R A N
G J U G A X X X X
```

Contoh tersebut menggambarkan matriks yang ditampilkan pada PDF sebelum atau dalam konteks ilustrasi pergeseran. Implementasi harus membedakan matriks sebelum shift dan sesudah shift.

### 6.3 Dynamic Row Shift

Aturan PDF:

- Baris pertama digeser 0 posisi.
- Baris kedua digeser 1 posisi ke kanan.
- Baris ketiga digeser 2 posisi ke kanan.
- Baris keempat digeser 3 posisi ke kanan.
- Pola berlanjut dengan jumlah pergeseran `i - 1`.

Gunakan indeks program yang dimulai dari nol:

`shift = indeks_baris`

Pergeseran bersifat melingkar. Untuk lebar matriks `K`, posisi sumber dapat dihitung dengan:

`indeks_sumber = (indeks_kolom_baru - shift) mod K`

Sehingga:

`matriks_baru[i][j] = matriks_lama[i][(j - i) mod K]`

Pastikan implementasi menggunakan matriks baru atau salinan agar perubahan satu posisi tidak merusak karakter yang belum diproses.

### 6.4 Pembacaan Myszkowski

Langkah:

1. Urutkan ranking dari nilai terkecil ke terbesar.
2. Untuk setiap ranking, ambil semua indeks kolom yang memiliki ranking tersebut.
3. Jika hanya ada satu kolom, baca kolom dari baris pertama sampai terakhir.
4. Jika ada beberapa kolom dengan ranking sama, baca secara horizontal per baris, mengikuti urutan kolom dari kiri ke kanan.
5. Gabungkan semua karakter menjadi ciphertext.

Contoh kelompok untuk `BOROBUDUR`:

- Ranking 1: kolom 1 dan 5.
- Ranking 2: kolom 7.
- Ranking 3: kolom 2 dan 4.
- Ranking 4: kolom 3 dan 9.
- Ranking 5: kolom 6 dan 8.

Perhatikan perbedaan aturan pembacaan:
- Satu kolom: vertikal dari atas ke bawah.
- Beberapa kolom dengan ranking sama: horizontal per baris, dari kolom terkecil ke terbesar.

### 6.5 Rekonstruksi matriks saat dekripsi

Dekripsi harus membalik urutan pembacaan secara tepat.

Langkah:

1. Tentukan jumlah baris dan kolom berdasarkan metadata plaintext asli dan keyword.
2. Buat matriks kosong dengan ukuran tersebut.
3. Susun kembali kelompok kolom menggunakan ranking keyword.
4. Untuk ranking tunggal, isi sel dari atas ke bawah.
5. Untuk ranking ganda, isi sel per baris dan per kolom dalam kelompok tersebut.
6. Setelah semua karakter ciphertext ditempatkan, matriks yang diperoleh harus sama dengan matriks setelah Dynamic Row Shift pada proses enkripsi.

Jangan mengisi matriks dekripsi dengan asumsi semua kolom dibaca vertikal. Aturan kelompok ranking yang sama harus tetap horizontal per baris.

### 6.6 Inverse Dynamic Row Shift

Untuk membatalkan pergeseran ke kanan, geser setiap baris ke kiri sebanyak indeks barisnya.

Dengan indeks mulai dari nol:

`matriks_asli[i][j] = matriks_shift[i][(j + i) mod K]`

Setelah inverse shift, gabungkan baris secara horizontal.

Potong hasil sesuai panjang plaintext asli yang disimpan dalam metadata. Langkah ini mencegah karakter padding ikut masuk ke plaintext akhir.

## 7. Metadata yang disarankan

Agar dekripsi dapat mengembalikan teks secara tepat, fungsi enkripsi sebaiknya menghasilkan ciphertext dan metadata.

Metadata minimal:

| Field | Kegunaan |
|---|---|
| `original_length` | Panjang plaintext setelah normalisasi |
| `key_length` | Jumlah kolom |
| `padding_character` | Karakter yang dipakai sebagai padding |
| `padding_count` | Jumlah karakter padding |
| `normalization_mode` | Aturan kapitalisasi dan penghapusan spasi |

Metadata ini merupakan rancangan teknis untuk mendukung dekripsi. PDF tidak menentukan format metadata.

Jika program akan dipakai untuk pertukaran data, metadata harus disimpan atau dikirim bersama ciphertext dengan format yang disepakati.

## 8. Validasi input dan penanganan kasus khusus

Program harus menangani kondisi berikut:

1. Plaintext kosong.
2. Keyword kosong.
3. Keyword hanya berisi karakter yang tidak didukung.
4. Panjang plaintext lebih pendek daripada panjang keyword.
5. Panjang plaintext tepat habis dibagi panjang keyword.
6. Plaintext membutuhkan padding.
7. Keyword memiliki huruf berulang.
8. Keyword memiliki satu jenis huruf saja.
9. Ciphertext kosong.
10. Metadata dekripsi tidak tersedia atau tidak sesuai.
11. Karakter plaintext berada di luar alfabet yang didukung.

Tentukan kebijakan untuk setiap kasus. Program sebaiknya memberikan pesan kesalahan yang jelas dan tidak berhenti dengan error yang tidak informatif.

## 9. Rencana pengujian

### 9.1 Pengujian ranking

Input:

`BOROBUDUR`

Ekspektasi:

`[1, 3, 4, 3, 1, 5, 2, 5, 4]`

### 9.2 Pengujian Dynamic Row Shift

Gunakan matriks kecil agar mudah diperiksa:

```text
A B C D
E F G H
I J K L
```

Dengan aturan shift ke kanan sebesar indeks baris, hasilnya:

```text
A B C D
H E F G
K L I J
```

### 9.3 Pengujian kelompok kolom

Pastikan `BOROBUDUR` menghasilkan kelompok:

```text
Ranking 1: kolom 1, 5
Ranking 2: kolom 7
Ranking 3: kolom 2, 4
Ranking 4: kolom 3, 9
Ranking 5: kolom 6, 8
```

### 9.4 Pengujian round-trip

Untuk setiap plaintext uji:

1. Jalankan enkripsi.
2. Ambil ciphertext dan metadata.
3. Jalankan dekripsi dengan keyword dan metadata yang sama.
4. Bandingkan hasil dekripsi dengan plaintext setelah normalisasi.

Kriteria utama:

`decrypt(encrypt(plaintext)) == normalized_plaintext`

Uji setidaknya:
- Teks satu karakter.
- Teks lebih pendek dari keyword.
- Teks dengan panjang tepat kelipatan keyword.
- Teks yang memerlukan padding.
- Teks dengan keyword berulang seperti `BOROBUDUR`.
- Teks yang mengandung karakter `X` di bagian akhir.

### 9.5 Pengujian konsistensi contoh PDF

PDF menampilkan plaintext:

`PASUKAN SIAP BERANGKAT SEKARANG JUGA`

dan ciphertext:

`PKKE ASXJ NAKG AUAB NTXG SIPG ARXX ASRN EAUA`

Namun, hasil ciphertext pada slide perlu diverifikasi kembali terhadap matriks dan aturan pembacaan yang digambarkan. Jangan menjadikan ciphertext tersebut sebagai expected output final sebelum perhitungan manualnya dipastikan.

Gunakan aturan algoritma dan pengujian round-trip sebagai dasar verifikasi implementasi.

## 10. Kompleksitas yang perlu dianalisis

PDF menyatakan kompleksitas komputasi `O(N)`.

Dalam implementasi, analisis secara terpisah:

- Normalisasi plaintext.
- Pembentukan matriks.
- Dynamic Row Shift.
- Pembacaan Myszkowski.
- Rekonstruksi matriks.
- Inverse Dynamic Row Shift.

Sebagian besar operasi matriks dan pembacaan karakter dapat dirancang linear terhadap jumlah karakter. Proses pengurutan huruf unik pada keyword juga memiliki biaya yang bergantung pada panjang keyword.

Jangan menyimpulkan keamanan kriptografi hanya dari kompleksitas waktu `O(N)`. Kompleksitas komputasi dan ketahanan terhadap serangan kriptanalisis adalah dua aspek yang berbeda.

## 11. Batasan keamanan

Metode ini merupakan algoritma transposisi. Metode ini mengubah posisi karakter, bukan mengganti karakter dengan simbol baru.

Karena itu:

- Jangan menyatakan metode ini setara dengan AES.
- Jangan menyatakan metode ini aman untuk melindungi dokumen sensitif tanpa evaluasi keamanan.
- Klaim difusi kuat harus dibuktikan dengan pengujian.
- Jika digunakan dalam sistem nyata untuk data sensitif, gunakan algoritma enkripsi terstandar seperti AES-GCM sebagai perlindungan utama. Metode penelitian ini dapat dievaluasi sebagai eksperimen atau lapisan tambahan, bukan pengganti enkripsi terstandar.

## 12. Urutan pengerjaan

Kerjakan secara bertahap:

1. Implementasikan dan uji ranking keyword.
2. Implementasikan pengelompokan kolom.
3. Implementasikan pembentukan matriks dan padding.
4. Implementasikan Dynamic Row Shift.
5. Implementasikan pembacaan Myszkowski.
6. Gabungkan fungsi menjadi proses enkripsi.
7. Implementasikan rekonstruksi matriks dekripsi.
8. Implementasikan inverse Dynamic Row Shift.
9. Implementasikan proses dekripsi lengkap.
10. Jalankan seluruh pengujian round-trip.
11. Dokumentasikan hasil dan kompleksitas.

Jangan lanjut ke tahap berikutnya sebelum tahap sebelumnya lulus pengujian.

## 13. Kriteria program selesai

Program dianggap memenuhi spesifikasi awal jika:

- Ranking keyword sesuai aturan alfabet dan huruf berulang mendapat ranking sama.
- Matriks tersusun sesuai jumlah kolom keyword.
- Pergeseran baris mengikuti `i - 1` dan bergerak ke kanan secara melingkar.
- Kolom dibaca sesuai aturan Myszkowski.
- Dekripsi merekonstruksi matriks hasil shift secara tepat.
- Inverse shift mengembalikan matriks sebelum shift.
- Padding dapat dihapus tanpa menghilangkan karakter plaintext asli.
- Semua pengujian round-trip berhasil.
- Program menangani input tidak valid dengan pesan yang jelas.

---

## Catatan akhir

Gunakan dokumen ini sebagai spesifikasi sebelum menulis kode. Pastikan keputusan tentang spasi, karakter yang didukung, padding, dan metadata ditetapkan terlebih dahulu. Detail tersebut belum dijelaskan secara lengkap dalam PDF dan berpengaruh langsung terhadap keberhasilan dekripsi.
"""

out = Path("/mnt/data/spesifikasi_implementasi_myszkowski_dynamic_row_shift.md")
try:
    import pypandoc
    pypandoc.convert_text(content, "md", format="md", outputfile=str(out), extra_args=["--standalone"])
except Exception:
    out.write_text(content, encoding="utf-8")

print(f"File dibuat: {out}")
