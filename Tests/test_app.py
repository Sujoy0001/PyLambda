import unittest

from fastapi.testclient import TestClient

from app.Api.V1.dataValue import data_table
from main import app


class AppTests(unittest.TestCase):
    def setUp(self):
        data_table.clear()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def test_root_returns_service_message(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "the server is working"})

    def test_health_returns_ok(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_data_can_be_created_and_read(self):
        create_response = self.client.post("/v1/data", params={"data": "sample"})
        read_response = self.client.get("/v1/data")

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json(), {"message": "sample"})
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json(), {"data": ["sample"]})

    def test_duplicate_data_returns_bad_request(self):
        self.client.post("/v1/data", params={"data": "sample"})

        response = self.client.post("/v1/data", params={"data": "sample"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Data already exists"})


if __name__ == "__main__":
    unittest.main()
