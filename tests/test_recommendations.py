import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app


test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestRecommendationEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

    @staticmethod
    def workload(**overrides):
        request = {
            "application_type": "E-Commerce",
            "expected_users_per_day": 25000,
            "concurrent_users": 600,
            "storage_required_gb": 300,
            "deployment_region": "us-east",
            "traffic_pattern": "High",
        }
        request.update(overrides)
        return request

    def register_user(self, email):
        response = self.client.post(
            "/api/auth/register",
            json={"name": "Recommendation User", "email": email, "password": "SecurePass123!"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["access_token"]

    @staticmethod
    def auth_headers(token):
        return {"Authorization": f"Bearer {token}"}

    def create_recommendation(self, token, workload=None):
        return self.client.post(
            "/api/recommendations",
            json=workload or self.workload(),
            headers=self.auth_headers(token),
        )

    def test_authenticated_user_can_create_and_persist_multi_cloud_recommendation(self):
        token = self.register_user("recommend@cloudpilot.ai")

        response = self.create_recommendation(token)

        self.assertEqual(response.status_code, 201)
        recommendation = response.json()
        self.assertGreater(recommendation["id"], 0)
        self.assertGreater(recommendation["user_id"], 0)
        self.assertGreater(recommendation["predicted_vcpu"], 0)
        self.assertGreater(recommendation["predicted_ram_gb"], 0)
        providers = {option["cloud_provider"] for option in recommendation["options"]}
        self.assertEqual(providers, {"AWS", "Azure", "GCP"})
        self.assertTrue(recommendation["recommended_provider"])
        self.assertTrue(recommendation["cheapest_vm"])
        self.assertGreater(recommendation["cheapest_monthly_cost_usd"], 0)
        self.assertTrue(recommendation["options"][0]["yearly_cost_usd"] > 0)

        history = self.client.get(
            "/api/recommendations", headers=self.auth_headers(token)
        )
        self.assertEqual(history.status_code, 200)
        self.assertEqual([item["id"] for item in history.json()], [recommendation["id"]])

    def test_unauthenticated_user_cannot_create_recommendation(self):
        response = self.client.post("/api/recommendations", json=self.workload())

        self.assertEqual(response.status_code, 401)

    def test_user_can_list_only_their_recommendation_history(self):
        first_token = self.register_user("history-first@cloudpilot.ai")
        second_token = self.register_user("history-second@cloudpilot.ai")
        first_recommendation = self.create_recommendation(first_token).json()
        self.create_recommendation(second_token)

        response = self.client.get(
            "/api/recommendations", headers=self.auth_headers(first_token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.json()],
            [first_recommendation["id"]],
        )

    def test_user_can_retrieve_their_recommendation(self):
        token = self.register_user("retrieve-rec@cloudpilot.ai")
        created = self.create_recommendation(token).json()

        response = self.client.get(
            f"/api/recommendations/{created['id']}",
            headers=self.auth_headers(token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], created["id"])

    def test_user_cannot_retrieve_another_users_recommendation(self):
        owner_token = self.register_user("rec-owner@cloudpilot.ai")
        other_token = self.register_user("rec-other@cloudpilot.ai")
        created = self.create_recommendation(owner_token).json()

        response = self.client.get(
            f"/api/recommendations/{created['id']}",
            headers=self.auth_headers(other_token),
        )

        self.assertEqual(response.status_code, 404)

    def test_invalid_workload_is_rejected_without_persisting(self):
        token = self.register_user("invalid-rec@cloudpilot.ai")
        invalid_requests = [
            self.workload(expected_users_per_day=0),
            self.workload(application_type="Unknown App"),
            self.workload(traffic_pattern="Bursty"),
            self.workload(user_id=123),
            self.workload(cloud_provider="Unknown Cloud"),
        ]

        for workload in invalid_requests:
            with self.subTest(workload=workload):
                response = self.create_recommendation(token, workload)
                self.assertEqual(response.status_code, 422)

        history = self.client.get(
            "/api/recommendations", headers=self.auth_headers(token)
        )
        self.assertEqual(history.json(), [])

    def test_unsupported_region_is_returned_as_client_error_without_persisting(self):
        token = self.register_user("region-rec@cloudpilot.ai")

        response = self.create_recommendation(
            token,
            self.workload(deployment_region="ap-south-1"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported deployment region", response.json()["detail"])
        self.assertEqual(
            self.client.get(
                "/api/recommendations", headers=self.auth_headers(token)
            ).json(),
            [],
        )

    def test_capacity_error_is_returned_without_persisting(self):
        token = self.register_user("capacity-rec@cloudpilot.ai")

        with patch(
            "backend.app.api.v1.recommendations.ml_engine.predict_resources",
            return_value=(32, 64),
        ):
            response = self.create_recommendation(token)

        self.assertEqual(response.status_code, 400)
        self.assertIn("exceeds the maximum available", response.json()["detail"])
        self.assertEqual(
            self.client.get(
                "/api/recommendations", headers=self.auth_headers(token)
            ).json(),
            [],
        )


if __name__ == "__main__":
    unittest.main()