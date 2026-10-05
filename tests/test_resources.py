import unittest

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


class TestResourceEndpoints(unittest.TestCase):
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
    def resource_payload(**overrides):
        payload = {
            "name": "Production API",
            "cloud_provider": "AWS",
            "region": "us-east-1",
            "resource_type": "Virtual Machine",
            "vcpu": 2,
            "ram_gb": 4,
            "storage_gb": 100,
            "hourly_cost": 0.045,
        }
        payload.update(overrides)
        return payload

    def register_user(self, email):
        response = self.client.post(
            "/api/auth/register",
            json={"name": "Resource User", "email": email, "password": "SecurePass123!"},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["access_token"]

    @staticmethod
    def auth_headers(token):
        return {"Authorization": f"Bearer {token}"}

    def create_resource(self, token, payload=None):
        return self.client.post(
            "/api/resources",
            json=payload or self.resource_payload(),
            headers=self.auth_headers(token),
        )

    def test_authenticated_user_can_create_resource(self):
        token = self.register_user("create@cloudpilot.ai")

        response = self.create_resource(token)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Production API")
        self.assertEqual(data["cloud_provider"], "AWS")
        self.assertGreater(data["user_id"], 0)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_unauthenticated_user_cannot_create_or_list_resources(self):
        create_response = self.client.post(
            "/api/resources", json=self.resource_payload()
        )
        list_response = self.client.get("/api/resources")

        self.assertEqual(create_response.status_code, 401)
        self.assertEqual(list_response.status_code, 401)

    def test_user_can_list_only_their_own_resources(self):
        first_token = self.register_user("first@cloudpilot.ai")
        second_token = self.register_user("second@cloudpilot.ai")
        first_resource = self.create_resource(first_token).json()
        self.create_resource(
            second_token,
            self.resource_payload(name="Other user's resource"),
        )

        response = self.client.get(
            "/api/resources", headers=self.auth_headers(first_token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [first_resource["id"]])

    def test_user_can_retrieve_their_own_resource(self):
        token = self.register_user("retrieve@cloudpilot.ai")
        created = self.create_resource(token).json()

        response = self.client.get(
            f"/api/resources/{created['id']}", headers=self.auth_headers(token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], created["id"])

    def test_authenticated_user_can_calculate_resource_cost(self):
        token = self.register_user("cost@cloudpilot.ai")
        resource = self.create_resource(token).json()

        response = self.client.get(
            f"/api/resources/{resource['id']}/cost",
            headers=self.auth_headers(token),
        )

        self.assertEqual(response.status_code, 200)
        cost = response.json()
        self.assertEqual(cost["resource_id"], resource["id"])
        self.assertEqual(cost["cloud_provider"], "AWS")
        self.assertEqual(cost["region"], "us-east-1")
        self.assertEqual(cost["storage_type"], "gp3")
        self.assertAlmostEqual(cost["hourly_cost"], 0.045)
        self.assertEqual(cost["monthly_compute_cost"], 32.4)
        self.assertEqual(cost["monthly_storage_cost"], 8.0)
        self.assertEqual(cost["total_monthly_cost"], 40.4)
        self.assertEqual(cost["yearly_cost"], 484.8)

    def test_unauthenticated_user_cannot_calculate_resource_cost(self):
        response = self.client.get("/api/resources/1/cost")

        self.assertEqual(response.status_code, 401)

    def test_user_cannot_calculate_another_users_resource_cost(self):
        owner_token = self.register_user("cost-owner@cloudpilot.ai")
        other_token = self.register_user("cost-other@cloudpilot.ai")
        resource = self.create_resource(owner_token).json()

        response = self.client.get(
            f"/api/resources/{resource['id']}/cost",
            headers=self.auth_headers(other_token),
        )

        self.assertEqual(response.status_code, 404)

    def test_storage_cost_uses_cloud_provider_catalog_rate(self):
        token = self.register_user("gcp-cost@cloudpilot.ai")
        resource = self.create_resource(
            token,
            self.resource_payload(
                cloud_provider="GCP",
                storage_gb=100,
                hourly_cost=0.05,
            ),
        ).json()

        response = self.client.get(
            f"/api/resources/{resource['id']}/cost",
            headers=self.auth_headers(token),
        )

        self.assertEqual(response.status_code, 200)
        cost = response.json()
        self.assertEqual(cost["storage_type"], "pd-balanced")
        self.assertEqual(cost["monthly_compute_cost"], 36.0)
        self.assertEqual(cost["monthly_storage_cost"], 10.0)
        self.assertEqual(cost["total_monthly_cost"], 46.0)
        self.assertEqual(cost["yearly_cost"], 552.0)

    def test_user_can_update_their_own_resource(self):
        token = self.register_user("update@cloudpilot.ai")
        created = self.create_resource(token).json()

        response = self.client.patch(
            f"/api/resources/{created['id']}",
            json={"name": "Updated API", "hourly_cost": 0.08},
            headers=self.auth_headers(token),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated API")
        self.assertEqual(response.json()["hourly_cost"], 0.08)
        self.assertEqual(response.json()["user_id"], created["user_id"])

    def test_user_can_delete_their_own_resource(self):
        token = self.register_user("delete@cloudpilot.ai")
        created = self.create_resource(token).json()

        response = self.client.delete(
            f"/api/resources/{created['id']}", headers=self.auth_headers(token)
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(
            self.client.get(
                f"/api/resources/{created['id']}", headers=self.auth_headers(token)
            ).status_code,
            404,
        )

    def test_user_cannot_access_another_users_resource(self):
        owner_token = self.register_user("owner@cloudpilot.ai")
        other_token = self.register_user("other@cloudpilot.ai")
        resource = self.create_resource(owner_token).json()
        headers = self.auth_headers(other_token)
        resource_url = f"/api/resources/{resource['id']}"

        get_response = self.client.get(resource_url, headers=headers)
        update_response = self.client.patch(
            resource_url, json={"name": "Stolen"}, headers=headers
        )
        delete_response = self.client.delete(resource_url, headers=headers)

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)

    def test_invalid_resource_data_and_client_user_id_are_rejected(self):
        token = self.register_user("invalid@cloudpilot.ai")
        invalid_payloads = [
            self.resource_payload(vcpu=0),
            self.resource_payload(ram_gb=0),
            self.resource_payload(storage_gb=-1),
            self.resource_payload(hourly_cost=-0.01),
            self.resource_payload(cloud_provider="DigitalOcean"),
            self.resource_payload(user_id=999),
        ]

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.create_resource(token, payload)
                self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()