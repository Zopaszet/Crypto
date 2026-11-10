import string

ALPHABET = (
    "0" + string.ascii_uppercase + string.ascii_lowercase + "123456789"
    + "!@#$%^&*()-_=+[]{}\\|;:'\",./?<>`~"
    + "¡¤¥µ±" + " "
)
assert len(ALPHABET) == 100 and len(set(ALPHABET)) == 100

FILLER = "X"


def build_table(key: str):
    seen, order = set(), []
    for ch in key + ALPHABET:
        if ch in ALPHABET and ch not in seen:
            seen.add(ch)
            order.append(ch)
    table = [order[i * 10:(i + 1) * 10] for i in range(10)]
    pos = {ch: (r, c) for r, row in enumerate(table) for c, ch in enumerate(row)}
    return table, pos


def make_bigrams(text: str):
    pairs, i = [], 0
    while i < len(text):
        a = text[i]
        b = text[i + 1] if i + 1 < len(text) else FILLER
        if a == b:                     
            pairs.append((a, FILLER))
            i += 1
        else:
            pairs.append((a, b))
            i += 2
    return pairs


def _shift(pairs, pos, table, step):
    out = []
    for a, b in pairs:
        ra, ca = pos[a]
        rb, cb = pos[b]
        if ra == rb:                    
            out += [table[ra][(ca + step) % 10], table[rb][(cb + step) % 10]]
        elif ca == cb:                 
            out += [table[(ra + step) % 10][ca], table[(rb + step) % 10][cb]]
        else:                           
            out += [table[ra][cb], table[rb][ca]]
    return "".join(out)


def playfair_encrypt(plaintext: str, key: str) -> str:
    table, pos = build_table(key)
    return _shift(make_bigrams(plaintext), pos, table, +1)


def playfair_decrypt(ciphertext: str, key: str) -> str:
    table, pos = build_table(key)
    pairs = [(ciphertext[i], ciphertext[i + 1]) for i in range(0, len(ciphertext), 2)]
    return _shift(pairs, pos, table, -1)



def _rail_pattern(n: int, rails: int, offset: int):
    if rails == 1:
        return [0] * n
    cycle = 2 * (rails - 1)
    pat = []
    for i in range(n):
        k = (i + offset) % cycle
        pat.append(k if k < rails else cycle - k)
    return pat


def zigzag_encrypt(text: str, rails: int = 3, offset: int = 0) -> str:
    pat = _rail_pattern(len(text), rails, offset)
    return "".join(ch for r in range(rails) for ch, p in zip(text, pat) if p == r)


def zigzag_decrypt(text: str, rails: int = 3, offset: int = 0) -> str:
    pat = _rail_pattern(len(text), rails, offset)
    order = sorted(range(len(text)), key=lambda i: (pat[i], i))
    out = [""] * len(text)
    for ch, idx in zip(text, order):
        out[idx] = ch
    return "".join(out)



def super_encrypt(plaintext: str, key: str) -> str:
    return zigzag_encrypt(playfair_encrypt(plaintext, key))


def super_decrypt(ciphertext: str, key: str) -> str:
    return playfair_decrypt(zigzag_decrypt(ciphertext), key)


def print_header(title: str):
    print("\n\n" + "┌──────────────────────────────────────────────────────────┐")
    print(f"│ {title:^56} │")
    print("└──────────────────────────────────────────────────────────┘\n")


if __name__ == "__main__":
    print_header("KRYPTOS - CLASSICAL CRYPTOGRAPHY SUITE")
    print(" [1] Super Cipher (Playfair + Zigzag)")
    print(" [2] Myszkowski Columnar Transposition + Dynamic Row Shift")
    print(" [0] Keluar\n")
    
    prog_choice = input("[+] Pilih program\n    Pilihan (0-2): ").strip()
    print("\n\n")

    if prog_choice == "1":
        print_header("SUPER CIPHER (PLAYFAIR + ZIGZAG)")
        print(" [1] Enkripsi (Plaintext -> Ciphertext)")
        print(" [2] Dekripsi (Ciphertext -> Plaintext)\n")
        choice = input("[+] Pilih menu\n    Pilihan (1/2): ").strip()
        print("\n")

        if choice == "1":
            print("[+] Masukkan data untuk Enkripsi")
            plaintext = input("    Plaintext : ")
            keyword = input("    Keyword   : ")
            print("\n")
            ct = super_encrypt(plaintext, keyword)
            print("  HASIL CIPHERTEXT:")
            print(f"  {ct}\n\n")
        elif choice == "2":
            print("[+] Masukkan data untuk Dekripsi")
            ciphertext = input("   Ciphertext: ")
            keyword = input("   Keyword   : ")
            print("\n")
            pt = super_decrypt(ciphertext, keyword)
            print("  HASIL PLAINTEXT:")
            print(f"  {pt}\n\n")
        else:
            print("[!] Pilihan menu tidak valid.\n\n")

    elif prog_choice == "2":
        print_header("MYSZKOWSKI + DYNAMIC ROW SHIFT")
        print(" [1] Enkripsi (Plaintext -> Token)")
        print(" [2] Dekripsi (Token -> Plaintext)\n")
        choice = input("[+] Pilih menu\n   Pilihan (1/2): ").strip()
        print("\n\n")

        try:
            if choice == "1":
                print("[+] Masukkan data untuk Enkripsi")
                plaintext = input("     Plaintext : ")
                keyword = input("   Keyword   : ")
                mode_input = input("   Mode [strict/strip] (tekan Enter untuk default 'strict'): ").strip()
                mode = mode_input if mode_input in ("strict", "strip") else DEFAULT_MODE
                print("\n")
                
                token = encrypt_token(plaintext, keyword, mode=mode)
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
            print(f"\n[ERROR] {exc}\n\n")
    elif prog_choice == "0":
        print("Keluar dari program. Terima kasih!\n\n")
    else:
        print("[!] Pilihan program tidak valid.\n\n")