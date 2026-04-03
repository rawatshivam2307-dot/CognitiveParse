import unittest

from backend.app import app
from backend.database import clear_errors, fetch_recent_errors, init_db


class ApiTests(unittest.TestCase):
    def setUp(self):
        init_db()
        clear_errors()
        self.client = app.test_client()

    def test_analyze_valid_code(self):
        code = """
class A:
    def __init__(self, x):
        self.x = x

    def square(self):
        return self.x ** 2
"""
        response = self.client.post("/analyze", json={"code": code})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["ok"])
        self.assertIn("node_count", payload["ast"])

    def test_analyze_invalid_code_logs_error(self):
        response = self.client.post("/analyze", json={"code": "for i in range(5) print(i)\n"})
        self.assertEqual(response.status_code, 422)
        payload = response.get_json()
        self.assertFalse(payload["ok"])

        rows = fetch_recent_errors()
        self.assertGreaterEqual(len(rows), 1)
        self.assertIn("category", rows[0])

    def test_dashboard_api_endpoints(self):
        self.client.post("/analyze", json={"code": "x =\n"})

        stats = self.client.get("/api/stats")
        errors = self.client.get("/api/errors")

        self.assertEqual(stats.status_code, 200)
        self.assertEqual(errors.status_code, 200)

        stats_payload = stats.get_json()
        errors_payload = errors.get_json()

        self.assertIn("categories", stats_payload)
        self.assertIn("errors", errors_payload)

    def test_clear_errors_endpoint(self):
        self.client.post("/analyze", json={"code": "if True print('x')\n"})
        self.assertGreaterEqual(len(fetch_recent_errors()), 1)

        cleared = self.client.post("/api/errors/clear")
        self.assertEqual(cleared.status_code, 200)
        payload = cleared.get_json()
        self.assertTrue(payload["ok"])
        self.assertEqual(len(fetch_recent_errors()), 0)

    def test_performance_report_endpoints(self):
        self.client.post("/analyze", json={"code": "if True print('x')\n"})

        report_json = self.client.get("/api/report")
        self.assertEqual(report_json.status_code, 200)
        payload = report_json.get_json()
        self.assertIn("total_errors", payload)
        self.assertIn("category_distribution", payload)

        report_md = self.client.get("/api/report/markdown")
        self.assertEqual(report_md.status_code, 200)
        self.assertIn("Performance Evaluation Report", report_md.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
