import unittest
from unittest.mock import patch

from chroma_connection import ChromaServerConfig, create_chroma_http_client


class ChromaServerConfigTest(unittest.TestCase):
    def test_defaults_target_local_docker_server(self) -> None:
        config = ChromaServerConfig.from_env({})

        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 8000)
        self.assertFalse(config.ssl)
        self.assertEqual(config.collection_name, "stock-terms")

    def test_railway_connection_is_loaded_from_environment(self) -> None:
        config = ChromaServerConfig.from_env(
            {
                "CHROMA_HOST": "chroma.railway.internal",
                "CHROMA_PORT": "8000",
                "CHROMA_SSL": "false",
                "CHROMA_COLLECTION": "korean-stock-terms",
            }
        )

        self.assertEqual(config.host, "chroma.railway.internal")
        self.assertEqual(config.port, 8000)
        self.assertFalse(config.ssl)
        self.assertEqual(config.collection_name, "korean-stock-terms")

    def test_invalid_port_is_rejected(self) -> None:
        for port in ("not-a-number", "0", "65536"):
            with self.subTest(port=port):
                with self.assertRaisesRegex(ValueError, "CHROMA_PORT"):
                    ChromaServerConfig.from_env({"CHROMA_PORT": port})

    def test_invalid_ssl_value_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "CHROMA_SSL"):
            ChromaServerConfig.from_env({"CHROMA_SSL": "sometimes"})

    @patch("chroma_connection.chromadb.HttpClient")
    def test_http_client_uses_validated_connection(self, http_client) -> None:
        config = ChromaServerConfig(
            host="chroma.railway.internal",
            port=8000,
            ssl=False,
            collection_name="stock-terms",
        )

        result = create_chroma_http_client(config)

        http_client.assert_called_once_with(
            host="chroma.railway.internal",
            port=8000,
            ssl=False,
        )
        self.assertEqual(result, http_client.return_value)


if __name__ == "__main__":
    unittest.main()
