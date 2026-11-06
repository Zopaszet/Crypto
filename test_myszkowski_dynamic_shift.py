"""Pengujian implementasi Myszkowski + Dynamic Row Shift (br.md bagian 9).

Jalankan:  python3 -m unittest -v test_myszkowski_dynamic_shift
"""

import unittest

from myszkowski_dynamic_shift import (
    DEFAULT_PADDING,
    Metadata,
    MyszkowskiError,
    apply_padding,
    create_matrix,
    decrypt,
    decrypt_token,
    dynamic_row_shift,
    encrypt,
    encrypt_token,
    generate_key_ranking,
    group_columns_by_rank,
    inverse_row_shift,
    normalize_text,
    read_myszkowski_columns,
    reconstruct_shifted_matrix,
    validate_key,
)


def _grid(text):
    """'ABCDEFGHIJKL' -> [['A'..'D'], ['E'..'H'], ['I'..'L']] untuk 4 kolom."""
    return [list(text[i : i + 4]) for i in range(0, len(text), 4)]


def _grid2(text):
    """'ABCDEFGHIJKL' -> [['A','B'], ...] untuk 2 kolom."""
    return [list(text[i : i + 2]) for i in range(0, len(text), 2)]


class TestRanking(unittest.TestCase):
    """9.1 Pengujian ranking."""

    def test_borobudur(self):
        self.assertEqual(
            generate_key_ranking("BOROBUDUR"), [1, 3, 4, 3, 1, 5, 2, 5, 4]
        )

    def test_ranking_case_and_space_insensitive(self):
        self.assertEqual(
            generate_key_ranking("  borobudur "), generate_key_ranking("BOROBUDUR")
        )

    def test_single_repeated_letter(self):
        # 8.8: keyword hanya satu jenis huruf -> semua ranking 1
        self.assertEqual(generate_key_ranking("AAAA"), [1, 1, 1, 1])

    def test_simple_key(self):
        self.assertEqual(generate_key_ranking("CAB"), [3, 1, 2])

    def test_empty_key_rejected(self):
        with self.assertRaises(MyszkowskiError):
            generate_key_ranking("")

    def test_whitespace_only_key_rejected(self):
        with self.assertRaises(MyszkowskiError):
            validate_key("   ")

    def test_non_alpha_key_rejected(self):
        with self.assertRaises(MyszkowskiError) as ctx:
            validate_key("BORO1")
        self.assertIn("A-Z", str(ctx.exception))


class TestColumnGroups(unittest.TestCase):
    """9.3 Pengujian kelompok kolom."""

    def test_borobudur_groups(self):
        groups = group_columns_by_rank(generate_key_ranking("BOROBUDUR"))
        self.assertEqual(groups, [[0, 4], [6], [1, 3], [2, 8], [5, 7]])

    def test_groups_are_sorted_ascending(self):
        for cols in group_columns_by_rank(generate_key_ranking("BOROBUDUR")):
            self.assertEqual(cols, sorted(cols))


class TestDynamicRowShift(unittest.TestCase):
    """9.2 Pengujian Dynamic Row Shift."""

    def test_spec_matrix(self):
        before = _grid("ABCDEFGHIJKL")
        after = dynamic_row_shift(before)
        self.assertEqual(after, _grid("ABCDHEFGKLIJ"))
        self.assertEqual(after, [["A", "B", "C", "D"],
                                 ["H", "E", "F", "G"],
                                 ["K", "L", "I", "J"]])

    def test_first_row_never_moves(self):
        before = _grid("ABCDEFGHIJKL")
        self.assertEqual(dynamic_row_shift(before)[0], before[0])

    def test_shift_is_circular(self):
        before = _grid("ABCDEFGHIJKL")
        after = dynamic_row_shift(before)
        for row_before, row_after in zip(before, after):
            self.assertEqual(sorted(row_before), sorted(row_after))

    def test_inverse_restores_matrix(self):
        before = _grid("ABCDEFGHIJKL")
        self.assertEqual(inverse_row_shift(dynamic_row_shift(before)), before)

    def test_inverse_roundtrip_random_sizes(self):
        for rows in range(1, 7):
            for cols in range(1, 7):
                before = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]
                self.assertEqual(inverse_row_shift(dynamic_row_shift(before)), before)

    def test_shift_does_not_mutate_input(self):
        before = _grid("ABCDEFGHIJKL")
        snapshot = [row[:] for row in before]
        dynamic_row_shift(before)
        self.assertEqual(before, snapshot)

    def test_empty_matrix(self):
        self.assertEqual(dynamic_row_shift([]), [])
        self.assertEqual(inverse_row_shift([]), [])


class TestMatrixAndPadding(unittest.TestCase):
    """6.2 Pembentukan matriks + padding."""

    def test_rows_is_ceil(self):
        self.assertEqual(len(create_matrix("ABCDEFGHIJ", 4)), 3)  # ceil(10/4)=3
        self.assertEqual(len(create_matrix("ABCDEFGH", 4)), 2)   # exact
        self.assertEqual(len(create_matrix("A", 4)), 1)          # shorter than key

    def test_padding_fills_last_row(self):
        grid, count = apply_padding(create_matrix("ABCDEFGHIJ", 4))
        self.assertEqual(count, 2)
        self.assertEqual(grid[-1], ["I", "J", DEFAULT_PADDING, DEFAULT_PADDING])

    def test_no_padding_when_exact(self):
        _, count = apply_padding(create_matrix("ABCDEFGH", 4))
        self.assertEqual(count, 0)

    def test_padding_character_configurable(self):
        grid, _ = apply_padding(create_matrix("ABCDEFGHIJ", 4), "Q")
        self.assertEqual(grid[-1][2:], ["Q", "Q"])


class TestMyszkowskiRead(unittest.TestCase):
    """6.4 Pembacaan Myszkowski: vertikal vs horizontal."""

    def test_single_column_is_vertical(self):
        grid = _grid2("ABCDEFGHIJKL")  # 6 baris x 2 kolom
        # keyword "AB" -> ranking [1,2] -> dua kelompok satu kolom
        groups = group_columns_by_rank(generate_key_ranking("AB"))
        self.assertEqual(groups, [[0], [1]])
        # kolom 0 vertikal lalu kolom 1 vertikal
        self.assertEqual(read_myszkowski_columns(grid, groups), "ACEGIKBDFHJL")

    def test_shared_rank_reads_horizontally(self):
        grid = _grid2("ABCDEFGHIJKL")
        # keyword "AA" -> satu kelompok [0,1] -> horizontal per baris
        groups = group_columns_by_rank(generate_key_ranking("AA"))
        self.assertEqual(groups, [[0, 1]])
        self.assertEqual(read_myszkowski_columns(grid, groups), "ABCDEFGHIJKL")

    def test_mixed_group_reads_correctly(self):
        # BOROBUDUR punya kelompok tunggal (rank 2) dan ganda (rank 1,3,4,5)
        grid = [["P", "A", "S", "U", "K", "A", "N", "S", "I"],
                ["A", "P", "B", "E", "R", "A", "N", "G", "K"]]
        groups = group_columns_by_rank(generate_key_ranking("BOROBUDUR"))
        # rank1 = kolom 0,4 -> horizontal per baris: (P,K) lalu (A,R) = "PKAR"
        # rank2 = kolom 6 -> vertikal: "NN"
        self.assertEqual(read_myszkowski_columns(grid, groups)[:6], "PKARNN")

    def test_group_size_mismatch_raises(self):
        grid = _grid("ABCDEFGHIJKL")
        with self.assertRaises(MyszkowskiError):
            read_myszkowski_columns(grid, [[0, 1]])  # hanya 2 kolom, butuh 4


class TestRoundTrip(unittest.TestCase):
    """9.4 Pengujian round-trip — kriteria utama."""

    CASES = [
        ("A", "KEY"),                                  # satu karakter
        ("HI", "BOROBUDUR"),                           # lebih pendek dari keyword
        ("ABCDEFGHI", "ABCDEFGHI"),                    # tepat kelipatan keyword
        ("PASUKANSIAPBERANGKATSEKARANGJUGA", "BOROBUDUR"),  # butuh padding
        ("HELLO WORLD", "SECRET"),                     # ada spasi
        ("DATAX", "KUNCI"),                            # X asli di akhir
        ("XXXX", "AB"),                                # semua X
        ("THEQUICKBROWNFOXJUMPSOVERTHELAZYDOG", "ZEBRA"),
    ]

    def test_roundtrip_all_cases(self):
        for plaintext, keyword in self.CASES:
            with self.subTest(plaintext=plaintext, keyword=keyword):
                ciphertext, meta = encrypt(plaintext, keyword)
                recovered = decrypt(ciphertext, keyword, meta)
                self.assertEqual(recovered, normalize_text(plaintext))

    def test_roundtrip_token(self):
        for plaintext, keyword in self.CASES:
            with self.subTest(plaintext=plaintext, keyword=keyword):
                token = encrypt_token(plaintext, keyword)
                self.assertEqual(decrypt_token(token, keyword), normalize_text(plaintext))

    def test_trailing_x_preserved(self):
        """X asli di akhir tidak boleh hilang sebagai padding (butuh metadata)."""
        ciphertext, meta = encrypt("DATAX", "KUNCI")
        self.assertEqual(meta.original_length, 5)
        self.assertEqual(decrypt(ciphertext, keyword="KUNCI", metadata=meta), "DATAX")

    def test_roundtrip_bruteforce_short_strings(self):
        import itertools

        alphabet = "ABX"
        for n in range(1, 6):
            for tup in itertools.product(alphabet, repeat=n):
                text = "".join(tup)
                ciphertext, meta = encrypt(text, "BOROBUDUR")
                self.assertEqual(
                    decrypt(ciphertext, "BOROBUDUR", meta), text, msg=text
                )

    def test_metadata_dict_works(self):
        ciphertext, meta = encrypt("PASUKAN", "BOROBUDUR")
        self.assertEqual(decrypt(ciphertext, "BOROBUDUR", meta.to_dict()), "PASUKAN")


class TestReconstruction(unittest.TestCase):
    """6.5 Rekonstruksi matriks saat dekripsi."""

    def test_reconstruction_matches_shifted_matrix(self):
        keyword = "BOROBUDUR"
        text = "PASUKANSIAPBERANGKATSEKARANGJUGA"
        ranking = generate_key_ranking(keyword)
        groups = group_columns_by_rank(ranking)

        grid, _ = apply_padding(create_matrix(text, len(keyword)))
        shifted = dynamic_row_shift(grid)
        ciphertext = read_myszkowski_columns(shifted, groups)

        rebuilt = reconstruct_shifted_matrix(ciphertext, groups, len(grid), len(keyword))
        self.assertEqual(rebuilt, shifted)

    def test_wrong_length_raises(self):
        groups = group_columns_by_rank(generate_key_ranking("BOROBUDUR"))
        with self.assertRaises(MyszkowskiError):
            reconstruct_shifted_matrix("ABC", groups, 1, 9)


class TestNormalization(unittest.TestCase):
    def test_uppercase_and_strip_spaces(self):
        self.assertEqual(normalize_text("Halo Dunia"), "HALODUNIA")

    def test_strict_rejects_unsupported(self):
        with self.assertRaises(MyszkowskiError) as ctx:
            normalize_text("HALO123")
        self.assertIn("tidak didukung", str(ctx.exception))

    def test_strip_mode_discards_unsupported(self):
        self.assertEqual(normalize_text("HALO123", mode="strip"), "HALO")

    def test_strip_mode_all_invalid_returns_empty(self):
        self.assertEqual(normalize_text("123", mode="strip"), "")


class TestValidation(unittest.TestCase):
    """8. Validasi input dan penanganan kasus khusus."""

    def test_empty_plaintext(self):
        with self.assertRaises(MyszkowskiError):
            encrypt("", "KEY")

    def test_plaintext_only_spaces(self):
        with self.assertRaises(MyszkowskiError):
            encrypt("     ", "KEY")

    def test_empty_keyword(self):
        with self.assertRaises(MyszkowskiError):
            encrypt("HELLO", "")

    def test_empty_ciphertext(self):
        _, meta = encrypt("HELLO", "KEY")
        with self.assertRaises(MyszkowskiError):
            decrypt("", "KEY", meta)

    def test_missing_metadata(self):
        ciphertext, _ = encrypt("HELLO", "KEY")
        with self.assertRaises(MyszkowskiError):
            decrypt(ciphertext, "KEY", None)

    def test_incomplete_metadata(self):
        ciphertext, meta = encrypt("HELLO", "KEY")
        broken = meta.to_dict()
        del broken["rows"]
        with self.assertRaises(MyszkowskiError) as ctx:
            decrypt(ciphertext, "KEY", broken)
        self.assertIn("tidak lengkap", str(ctx.exception))

    def test_keyword_length_mismatch(self):
        ciphertext, meta = encrypt("HELLO", "KEY")
        with self.assertRaises(MyszkowskiError) as ctx:
            decrypt(ciphertext, "KEYWORD", meta)
        self.assertIn("tidak cocok", str(ctx.exception))

    def test_metadata_size_mismatch(self):
        ciphertext, meta = encrypt("HELLO", "KEY")
        bad = Metadata(
            original_length=meta.original_length,
            key_length=meta.key_length,
            padding_character=meta.padding_character,
            padding_count=meta.padding_count,
            normalization_mode=meta.normalization_mode,
            rows=meta.rows + 3,
        )
        with self.assertRaises(MyszkowskiError):
            decrypt(ciphertext, "KEY", bad)

    def test_original_length_exceeds_ciphertext(self):
        ciphertext, meta = encrypt("HELLO", "KEY")
        bad = Metadata(
            original_length=len(ciphertext) + 5,
            key_length=meta.key_length,
            padding_character=meta.padding_character,
            padding_count=meta.padding_count,
            normalization_mode=meta.normalization_mode,
            rows=meta.rows,
        )
        with self.assertRaises(MyszkowskiError):
            decrypt(ciphertext, "KEY", bad)

    def test_bad_padding_character(self):
        with self.assertRaises(MyszkowskiError):
            encrypt("HELLO", "KEY", padding_character="XY")

    def test_invalid_token(self):
        with self.assertRaises(MyszkowskiError):
            decrypt_token("garbage", "KEY")

    def test_error_messages_are_clear(self):
        for args in [("", "KEY"), ("HELLO", "")]:
            with self.assertRaises(MyszkowskiError) as ctx:
                encrypt(*args)
            self.assertTrue(str(ctx.exception))
            self.assertNotIsInstance(ctx.exception, KeyError)


class TestPDFExample(unittest.TestCase):
    """9.5 Konsistensi contoh PDF (diverifikasi, bukan diasumsikan benar)."""

    PLAINTEXT = "PASUKAN SIAP BERANGKAT SEKARANG JUGA"
    KEYWORD = "BOROBUDUR"
    PDF_CIPHER = "PKKEASXJNAKGAUABNTXGSIPGARXXASRNEAUA"

    def test_matrix_matches_pdf_layout(self):
        grid, _ = apply_padding(create_matrix(normalize_text(self.PLAINTEXT), 9))
        self.assertEqual(
            ["".join(r) for r in grid],
            ["PASUKANSI", "APBERANGK", "ATSEKARAN", "GJUGAXXXX"],
        )

    def test_ciphertext_length(self):
        ciphertext, meta = encrypt(self.PLAINTEXT, self.KEYWORD)
        self.assertEqual(len(ciphertext), 36)
        self.assertEqual(meta.padding_count, 4)
        self.assertEqual(meta.original_length, 32)

    def test_pdf_ciphertext_reproduces(self):
        """Ciphertext slide PDF HARUS cocok dengan aturan yang didokumentasikan."""
        ciphertext, _ = encrypt(self.PLAINTEXT, self.KEYWORD)
        self.assertEqual(ciphertext, self.PDF_CIPHER)

    def test_roundtrip_pdf_example(self):
        ciphertext, meta = encrypt(self.PLAINTEXT, self.KEYWORD)
        self.assertEqual(
            decrypt(ciphertext, self.KEYWORD, meta),
            "PASUKANSIAPBERANGKATSEKARANGJUGA",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
