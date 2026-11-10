"""Transposisi Kolom Myszkowski dengan Dynamic Row Shift.

Implementasi mengikuti spesifikasi pada ``br.md`` (Spesifikasi Implementasi:
Pengembangan Transposisi Kolom Myszkowski dengan Dynamic Row Shift).

Alur enkripsi
-------------
plaintext + keyword
  -> normalize_text()          kapitalisasi + kebijakan spasi/karakter
  -> validate_key()            keyword wajib valid & tidak kosong
  -> generate_key_ranking()    ranking alfabetis, huruf kembar = ranking sama
  -> group_columns_by_rank()   kelompok indeks kolom per ranking
  -> create_matrix()           susun horizontal, R = ceil(N / K)
  -> apply_padding()           lengkapi sel kosong dengan padding
  -> dynamic_row_shift()       baris i digeser kanan sejauh i (melingkar)
  -> read_myszkowski_columns() baca per kelompok ranking
  -> ciphertext + metadata

Alur dekripsi adalah kebalikan persis dari urutan di atas.

Keputusan desain (lihat br.md bagian 3 — ini BUKAN ketentuan PDF)
----------------------------------------------------------------
1. Kapitalisasi  : plaintext & keyword diubah ke huruf kapital.
2. Spasi         : dihapus saat normalisasi (mode ``"strip"``).
3. Non A-Z       : mode ``"strict"`` menolak dengan pesan jelas;
                   mode ``"strip"`` membuang karakter tak didukung.
4. Padding       : ``"X"`` secara default, dapat diubah lewat parameter.
5. Pergeseran    : ``shift = indeks_baris``, ke kanan, melingkar.
6. Metadata      : panjang plaintext asli disimpan agar padding dapat
                   dibuang tepat (tanpa metadata, "X" asli di akhir
                   plaintext tidak bisa dibedakan dari padding).

Kompleksitas
------------
Dengan N = panjang plaintext, K = panjang keyword, R = ceil(N / K):

- normalize_text            : O(N)
- generate_key_ranking      : O(K log K)  (pengurutan huruf unik)
- create_matrix + padding   : O(N + K)
- dynamic_row_shift         : O(N)
- read_myszkowski_columns   : O(N)
- rekonstruksi matriks      : O(N)
- inverse_row_shift         : O(N)

Total O(N + K log K) per operasi, linear terhadap jumlah karakter
sebagaimana klaim PDF, ditambah biaya pengurutan keyword.

Batasan keamanan
----------------
Ini murni TRANSPOSISI (mengubah posisi karakter, bukan menggantinya).
Analisis frekuensi tetap berlaku dan jumlah kunci efektif sangat kecil.
Metode ini TIDAK setara AES dan tidak layak untuk melindungi data
sensitif. Untuk pemakaian nyata gunakan AES-GCM atau ChaCha20-Poly1305
sebagai lapisan utama; algoritma ini hanya untuk eksperimen/penelitian.
"""

from __future__ import annotations

import math
import string
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

SUPPORTED = frozenset(string.ascii_uppercase)
DEFAULT_PADDING = "X"
DEFAULT_MODE = "strict"  # "strict" | "strip"


# ---------------------------------------------------------------------------
# Kesalahan
# ---------------------------------------------------------------------------
class MyszkowskiError(ValueError):
    """Kesalahan input yang dapat dilaporkan ke pengguna."""


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Metadata:
    """Metadata minimal yang wajib ikut bersama ciphertext (br.md bagian 7)."""

    original_length: int      # panjang plaintext SETELAH normalisasi
    key_length: int           # jumlah kolom matriks
    padding_character: str    # karakter padding yang dipakai
    padding_count: int        # jumlah karakter padding
    normalization_mode: str   # "strict" atau "strip"
    rows: int                 # jumlah baris matriks

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Metadata":
        try:
            return cls(
                original_length=int(data["original_length"]),
                key_length=int(data["key_length"]),
                padding_character=str(data["padding_character"]),
                padding_count=int(data["padding_count"]),
                normalization_mode=str(data["normalization_mode"]),
                rows=int(data["rows"]),
            )
        except KeyError as exc:
            raise MyszkowskiError(
                f"Metadata tidak lengkap: field {exc.args[0]!r} tidak ditemukan."
            ) from exc

    def pack(self, ciphertext: str) -> str:
        """Gabungkan ciphertext + metadata menjadi satu token portabel."""
        return "|".join(
            [
                "MDRS1",
                ciphertext,
                str(self.original_length),
                str(self.key_length),
                self.padding_character,
                str(self.padding_count),
                self.normalization_mode,
                str(self.rows),
            ]
        )

    @classmethod
    def unpack(cls, token: str) -> tuple[str, "Metadata"]:
        parts = token.split("|")
        if len(parts) != 8 or parts[0] != "MDRS1":
            raise MyszkowskiError(
                "Token tidak valid. Format: MDRS1|<ciphertext>|<orig_len>|"
                "<key_len>|<pad_char>|<pad_count>|<mode>|<rows>"
            )
        _, ct, orig, klen, pad, pcount, mode, rows = parts
        meta = cls.from_dict(
            {
                "original_length": orig,
                "key_length": klen,
                "padding_character": pad,
                "padding_count": pcount,
                "normalization_mode": mode,
                "rows": rows,
            }
        )
        return ct, meta


# ---------------------------------------------------------------------------
# 1. Normalisasi
# ---------------------------------------------------------------------------
def normalize_text(text: str, mode: str = DEFAULT_MODE) -> str:
    """Normalisasi plaintext: kapitalisasi, hapus spasi, tangani non A-Z.

    mode="strict": karakter selain A-Z (setelah spasi dibuang) -> error.
    mode="strip" : karakter selain A-Z dibuang diam-diam.
    """
    if mode not in ("strict", "strip"):
        raise MyszkowskiError(f"Mode normalisasi tidak dikenal: {mode!r}")

    cleaned = "".join(text.split())  # buang semua whitespace
    upper = cleaned.upper()

    bad = sorted({ch for ch in upper if ch not in SUPPORTED})
    if bad:
        if mode == "strict":
            raise MyszkowskiError(
                "Plaintext mengandung karakter yang tidak didukung: "
                + ", ".join(repr(ch) for ch in bad)
                + ". Gunakan hanya A-Z dan spasi, atau pilih mode='strip'."
            )
        upper = "".join(ch for ch in upper if ch in SUPPORTED)

    return upper


# ---------------------------------------------------------------------------
# 2. Validasi keyword
# ---------------------------------------------------------------------------
def validate_key(keyword: str) -> str:
    """Pastikan keyword valid, kembalikan bentuk kapital tanpa spasi."""
    if keyword is None:
        raise MyszkowskiError("Keyword tidak boleh kosong.")
    key = "".join(keyword.split()).upper()
    if not key:
        raise MyszkowskiError("Keyword tidak boleh kosong.")
    bad = sorted({ch for ch in key if ch not in SUPPORTED})
    if bad:
        raise MyszkowskiError(
            "Keyword hanya boleh berisi huruf A-Z. Ditemukan: "
            + ", ".join(repr(ch) for ch in bad)
        )
    return key


# ---------------------------------------------------------------------------
# 3. Ranking keyword
# ---------------------------------------------------------------------------
def generate_key_ranking(keyword: str) -> list[int]:
    """Ranking alfabetis; huruf kembar mendapat ranking yang sama.

    BOROBUDUR -> huruf unik terurut B,D,O,R,U -> [1,3,4,3,1,5,2,5,4]
    """
    key = validate_key(keyword)
    rank_of = {ch: i + 1 for i, ch in enumerate(sorted(set(key)))}
    return [rank_of[ch] for ch in key]


# ---------------------------------------------------------------------------
# 4. Pengelompokan kolom
# ---------------------------------------------------------------------------
def group_columns_by_rank(ranking: Sequence[int]) -> list[list[int]]:
    """Kelompokkan indeks kolom (0-based) per ranking, urut ranking naik.

    Setiap sublist sudah terurut menaik (kiri ke kanan) agar pembacaan
    horizontal konsisten.
    """
    if not ranking:
        raise MyszkowskiError("Ranking kosong; keyword tidak valid.")
    groups: dict[int, list[int]] = {}
    for col, rank in enumerate(ranking):
        groups.setdefault(rank, []).append(col)
    return [groups[rank] for rank in sorted(groups)]


# ---------------------------------------------------------------------------
# 5. Matriks & padding
# ---------------------------------------------------------------------------
def create_matrix(text: str, columns: int) -> list[list[str]]:
    """Susun teks horizontal, R = ceil(N / K). Sel sisa diisi string kosong."""
    if columns < 1:
        raise MyszkowskiError("Jumlah kolom harus >= 1.")
    rows = math.ceil(len(text) / columns) if text else 0
    grid = [["" for _ in range(columns)] for _ in range(rows)]
    for i, ch in enumerate(text):
        grid[i // columns][i % columns] = ch
    return grid


def apply_padding(
    matrix: list[list[str]], padding_character: str = DEFAULT_PADDING
) -> tuple[list[list[str]], int]:
    """Isi sel kosong dengan karakter padding; kembalikan (matriks, jumlah)."""
    if len(padding_character) != 1:
        raise MyszkowskiError("Karakter padding harus tepat satu karakter.")
    count = 0
    filled = []
    for row in matrix:
        new_row = []
        for cell in row:
            if cell == "":
                new_row.append(padding_character)
                count += 1
            else:
                new_row.append(cell)
        filled.append(new_row)
    return filled, count


# ---------------------------------------------------------------------------
# 6. Dynamic Row Shift
# ---------------------------------------------------------------------------
def dynamic_row_shift(matrix: list[list[str]]) -> list[list[str]]:
    """Geser baris i ke kanan sejauh i, melingkar.

    matriks_baru[i][j] = matriks_lama[i][(j - i) mod K]
    """
    if not matrix:
        return []
    width = len(matrix[0])
    return [
        [row[(j - i) % width] for j in range(width)]
        for i, row in enumerate(matrix)
    ]


def inverse_row_shift(matrix: list[list[str]]) -> list[list[str]]:
    """Batalkan pergeseran: geser baris i ke kiri sejauh i.

    matriks_asli[i][j] = matriks_shift[i][(j + i) mod K]
    """
    if not matrix:
        return []
    width = len(matrix[0])
    return [
        [row[(j + i) % width] for j in range(width)]
        for i, row in enumerate(matrix)
    ]


# ---------------------------------------------------------------------------
# 7. Pembacaan & rekonstruksi Myszkowski
# ---------------------------------------------------------------------------
def _read_order(groups: Iterable[Sequence[int]], rows: int) -> list[tuple[int, int]]:
    """Urutan sel (row, col) saat pembacaan Myszkowski.

    Satu kolom dalam kelompok -> vertikal atas ke bawah.
    Beberapa kolom sekelompok -> horizontal per baris, kiri ke kanan.
    """
    order: list[tuple[int, int]] = []
    for cols in groups:
        if len(cols) == 1:
            col = cols[0]
            order.extend((r, col) for r in range(rows))
        else:
            for r in range(rows):
                order.extend((r, c) for c in cols)
    return order


def read_myszkowski_columns(
    matrix: list[list[str]], groups: Sequence[Sequence[int]]
) -> str:
    """Baca matriks sesuai aturan Myszkowski, hasilkan ciphertext."""
    if not matrix:
        raise MyszkowskiError("Matriks kosong; tidak ada yang bisa dibaca.")
    order = _read_order(groups, len(matrix))
    if len(order) != len(matrix) * len(matrix[0]):
        raise MyszkowskiError("Ukuran kelompok kolom tidak cocok dengan matriks.")
    return "".join(matrix[r][c] for r, c in order)


def reconstruct_shifted_matrix(
    ciphertext: str, groups: Sequence[Sequence[int]], rows: int, columns: int
) -> list[list[str]]:
    """Isi matriks hasil shift dari ciphertext sesuai urutan baca Myszkowski."""
    if rows < 1 or columns < 1:
        raise MyszkowskiError("Ukuran matriks harus >= 1 baris dan 1 kolom.")
    order = _read_order(groups, rows)
    if len(order) != rows * columns:
        raise MyszkowskiError(
            f"Ukuran matriks {rows}x{columns} tidak cocok dengan kelompok kolom."
        )
    if len(ciphertext) != len(order):
        raise MyszkowskiError(
            f"Panjang ciphertext {len(ciphertext)} tidak sesuai: "
            f"dibutuhkan {len(order)} karakter."
        )
    grid = [["" for _ in range(columns)] for _ in range(rows)]
    for (r, c), ch in zip(order, ciphertext):
        grid[r][c] = ch
    return grid


# ---------------------------------------------------------------------------
# 8. Enkripsi & dekripsi
# ---------------------------------------------------------------------------
def encrypt(
    plaintext: str,
    keyword: str,
    padding_character: str = DEFAULT_PADDING,
    mode: str = DEFAULT_MODE,
) -> tuple[str, Metadata]:
    """Enkripsi plaintext; kembalikan (ciphertext, metadata)."""
    if not isinstance(plaintext, str):
        raise MyszkowskiError("Plaintext harus berupa string.")
    if not plaintext:
        raise MyszkowskiError("Plaintext tidak boleh kosong.")

    text = normalize_text(plaintext, mode=mode)
    if not text:
        raise MyszkowskiError(
            "Plaintext kosong setelah normalisasi; tidak ada karakter tersisa."
        )

    key = validate_key(keyword)
    ranking = generate_key_ranking(key)
    groups = group_columns_by_rank(ranking)

    matrix = create_matrix(text, len(key))
    matrix, pad_count = apply_padding(matrix, padding_character)
    shifted = dynamic_row_shift(matrix)
    ciphertext = read_myszkowski_columns(shifted, groups)

    meta = Metadata(
        original_length=len(text),
        key_length=len(key),
        padding_character=padding_character,
        padding_count=pad_count,
        normalization_mode=mode,
        rows=len(matrix),
    )
    return ciphertext, meta


def decrypt(ciphertext: str, keyword: str, metadata: Metadata | dict) -> str:
    """Dekripsi ciphertext memakai keyword dan metadata dari enkripsi."""
    if not isinstance(ciphertext, str):
        raise MyszkowskiError("Ciphertext harus berupa string.")
    if not ciphertext:
        raise MyszkowskiError("Ciphertext tidak boleh kosong.")
    if metadata is None:
        raise MyszkowskiError(
            "Metadata wajib disertakan saat dekripsi (butuh original_length)."
        )
    meta = metadata if isinstance(metadata, Metadata) else Metadata.from_dict(metadata)

    key = validate_key(keyword)
    if len(key) != meta.key_length:
        raise MyszkowskiError(
            f"Panjang keyword ({len(key)}) tidak cocok dengan metadata "
            f"({meta.key_length})."
        )

    ranking = generate_key_ranking(key)
    groups = group_columns_by_rank(ranking)

    rows = meta.rows
    columns = meta.key_length
    if rows * columns != len(ciphertext):
        raise MyszkowskiError(
            f"Metadata tidak konsisten: {rows}x{columns} = {rows * columns} sel, "
            f"tetapi ciphertext {len(ciphertext)} karakter."
        )
    if meta.original_length > len(ciphertext):
        raise MyszkowskiError(
            "Metadata tidak konsisten: original_length melebihi panjang ciphertext."
        )

    shifted = reconstruct_shifted_matrix(ciphertext, groups, rows, columns)
    matrix = inverse_row_shift(shifted)
    joined = "".join(cell for row in matrix for cell in row)
    return joined[: meta.original_length]


def encrypt_token(
    plaintext: str,
    keyword: str,
    padding_character: str = DEFAULT_PADDING,
    mode: str = DEFAULT_MODE,
) -> str:
    """Enkripsi dan bungkus ciphertext + metadata dalam satu token portabel."""
    ciphertext, meta = encrypt(plaintext, keyword, padding_character, mode)
    return meta.pack(ciphertext)


def decrypt_token(token: str, keyword: str) -> str:
    """Dekripsi token hasil :func:`encrypt_token`."""
    ciphertext, meta = Metadata.unpack(token)
    return decrypt(ciphertext, keyword, meta)


# ---------------------------------------------------------------------------
# 9. CLI
# ---------------------------------------------------------------------------
def print_header(title: str):
    print("\n\n" + "┌──────────────────────────────────────────────────────────┐")
    print(f"│ {title:^56} │")
    print("└──────────────────────────────────────────────────────────┘\n")


def _main(argv: list[str] | None = None) -> int:
    import sys

    print_header("MYSZKOWSKI + DYNAMIC ROW SHIFT")
    print(" [1] Enkripsi (Plaintext -> Token)")
    print(" [2] Dekripsi (Token -> Plaintext)\n")
    choice = input("[+] Pilih menu\n    Pilihan (1/2): ").strip()
    print("\n\n")

    try:
        if choice == "1":
            print("[+] Masukkan data untuk Enkripsi")
            plaintext = input("   Plaintext : ")
            keyword = input("   Keyword   : ")
            mode_input = input("   Mode [strict/strip] (tekan Enter untuk default 'strict'): ").strip()
            mode = mode_input if mode_input in ("strict", "strip") else DEFAULT_MODE
            print("\n")

            token = encrypt_token(plaintext, keyword, padding_character=DEFAULT_PADDING, mode=mode)
            print("  HASIL TOKEN (Ciphertext + Metadata):")
            print(f"  {token}\n\n")
        elif choice == "2":
            print("[+] Masukkan data untuk Dekripsi")
            token = input("   Token     : ")
            keyword = input("   Keyword   : ")
            print("\n")

            pt = decrypt_token(token, keyword)
            print("  HASIL PLAINTEXT:")
            print(f"  {pt}\n\n")
        else:
            print("[!] Pilihan menu tidak valid.\n\n")
    except MyszkowskiError as exc:
        print(f"\n[ERROR] {exc}\n\n", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
