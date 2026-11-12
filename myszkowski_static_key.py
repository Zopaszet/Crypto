"""CLI statis Myszkowski + Dynamic Row Shift.

Skrip ini adalah pembungkus tipis (thin CLI) di atas modul
``myszkowski_dynamic_shift``: algoritma tidak disalin, hanya dipanggil.

Keyword sengaja DIPATOK permanen ke ``BOROBUDUR`` (9 huruf), mode
normalisasi ``strict``, dan karakter padding ``X``. Pengguna hanya
mengetik plaintext saat enkripsi atau token saat dekripsi; tidak ada
prompt untuk keyword, mode, maupun padding.

Konsekuensi yang perlu dipahami:

- Token hanya bisa didekripsi bila dibuat dengan keyword yang sama
  (``BOROBUDUR``). Token dari keyword lain akan gagal karena panjang
  keyword tidak cocok dengan metadata.
- Mode ``strict`` menolak karakter selain A-Z (spasi dibuang lebih dulu),
  jadi plaintext cukup diisi huruf dan spasi.

Jalankan dengan: ``python3 myszkowski_static_key.py``
"""

from __future__ import annotations

import sys

from myszkowski_dynamic_shift import (
    DEFAULT_MODE,
    DEFAULT_PADDING,
    MyszkowskiError,
    decrypt_token,
    encrypt,
    print_header,
)

# ---------------------------------------------------------------------------
# Konfigurasi tetap (tidak dapat diubah dari menu)
# ---------------------------------------------------------------------------
KEYWORD = "BOROBUDUR"
MODE = DEFAULT_MODE      # "strict"
PADDING = DEFAULT_PADDING  # "X"


def _show_menu() -> None:
    print(" [1] Enkripsi (Plaintext -> Token)")
    print(" [2] Dekripsi (Token -> Plaintext)")
    print(" [0] Keluar\n")


def _run_encrypt() -> None:
    print("[+] Masukkan data untuk Enkripsi")
    plaintext = input("   Plaintext : ")
    print("\n")

    ciphertext, meta = encrypt(plaintext, KEYWORD, padding_character=PADDING, mode=MODE)
    token = meta.pack(ciphertext)

    print("  HASIL ENKRIPSI:")
    print(f"  {ciphertext}\n")
    print("  METADATA:")
    for field, value in meta.to_dict().items():
        print(f"    {field:<18} : {value}")
    print()
    print("  TOKEN (untuk menu Dekripsi):")
    print(f"  {token}\n\n")


def _run_decrypt() -> None:
    print("[+] Masukkan data untuk Dekripsi")
    token = input("   Token     : ")
    print("\n")

    plaintext = decrypt_token(token, KEYWORD)
    print("  HASIL PLAINTEXT:")
    print(f"  {plaintext}\n\n")


def _main(argv: list[str] | None = None) -> int:
    print_header("MYSZKOWSKI + DYNAMIC ROW SHIFT (STATIC KEY)")
    _show_menu()
    choice = input("[+] Pilih menu\n    Pilihan (1/2/0): ").strip()
    print("\n\n")

    try:
        if choice == "1":
            _run_encrypt()
        elif choice == "2":
            _run_decrypt()
        elif choice == "0":
            print("[+] Keluar.\n\n")
        else:
            print("[!] Pilihan menu tidak valid.\n\n")
    except MyszkowskiError as exc:
        print(f"\n[ERROR] {exc}\n\n", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
