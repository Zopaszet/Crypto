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


if __name__ == "__main__":
    assert zigzag_encrypt("A6B8gxkrEphySgnqvtY1") == "AgESv68xrpygqt1BkhnY"
    assert zigzag_decrypt("AgESv68xrpygqt1BkhnY") == "A6B8gxkrEphySgnqvtY1"

    key = "Makassar, 6/21/2021"
    pt = "Fakultas Ilmu Komputer"
    ct = super_encrypt(pt, key)
    print("Plaintext :", pt)
    print("Ciphertext:", ct)
    print("Dekripsi  :", super_decrypt(ct, key))