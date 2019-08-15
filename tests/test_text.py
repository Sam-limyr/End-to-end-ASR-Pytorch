import unittest

from src import text


class TestChacterTextEncoder(unittest.TestCase):
    def setUp(self):
        super(TestChacterTextEncoder, self).__init__()
        self.vocab_file = "tests/sample_data/character.vocab"
        self.vocab_list = list(" ABCDEFGHIJKLMNOPQRSTUVWXYZ'")
        self.text = "SPEECH LAB!"

    def test_load_from_file(self):
        text_encoder = text.CharacterTextEncoder.load_from_file(
            self.vocab_file)
        self._test_encode_decode(text_encoder)

    def test_from_vocab_list(self):
        text_encoder = text.CharacterTextEncoder(self.vocab_list)
        self._test_encode_decode(text_encoder)

    def _test_encode_decode(self, text_encoder):
        ids = text_encoder.encode(self.text)

        self.assertEqual(31, text_encoder.vocab_size)
        self.assertEqual(
            ids, [22, 19, 8, 8, 6, 11, 3, 15, 4, 5, 2, 1])

        decoded = text_encoder.decode(ids)
        self.assertEqual(decoded, self.text.replace("!", "<unk>"))


class TestSubwordTextEncoder(unittest.TestCase):
    def setUp(self):
        self.filepath = "tests/sample_data/subword.model"
        self.text = "SPEECH LAB IS GREAT"

    def test_load_from_file(self):
        text_encoder = text.SubwordTextEncoder.load_from_file(self.filepath)
        self._test_encode_decode(text_encoder)

    def _test_encode_decode(self, text_encoder):
        ids = text_encoder.encode(self.text)

        self.assertEqual(100, text_encoder.vocab_size)
        self.assertEqual(ids, [9, 92, 74, 74, 87, 80, 37,
                               76, 93, 18, 81, 44, 11, 22, 1])

        decoded = text_encoder.decode(ids)
        self.assertEqual(decoded, self.text)


class TestWordTextEncoder(unittest.TestCase):
    def setUp(self):
        super(TestWordTextEncoder, self).__init__()
        self.vocab_file = "tests/sample_data/word.vocab"
        self.vocab_list = ["SPEECH", "LAB", "IS", "GREAT"]
        self.text = "SPEECH LAB IS GREAT !!!"

    def test_load_from_file(self):
        text_encoder = text.WordTextEncoder.load_from_file(self.vocab_file)
        self._test_encode_decode(text_encoder)

    def test_from_vocab_list(self):
        text_encoder = text.WordTextEncoder(self.vocab_list)
        self._test_encode_decode(text_encoder)

    def _test_encode_decode(self, text_encoder):
        ids = text_encoder.encode(self.text)

        self.assertEqual(7, text_encoder.vocab_size)
        self.assertEqual(ids, [3, 4, 5, 6, 2, 1])

        decoded = text_encoder.decode(ids)
        self.assertEqual(decoded, self.text.replace("!!!", "<unk>"))
