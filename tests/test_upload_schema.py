import unittest

from app.main import app
from app.db import engine


class UploadSchemaTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        engine.dispose()

    def test_bot_mask_is_optional_but_binary_remains_required(self):
        schema = app.openapi()
        body = schema["paths"]["/api/bots"]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
        name = body["$ref"].rsplit("/", 1)[-1]
        required = schema["components"]["schemas"][name]["required"]
        self.assertIn("binary", required)
        self.assertNotIn("avatar", required)


if __name__ == "__main__":
    unittest.main()
