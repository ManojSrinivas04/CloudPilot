import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base, get_db
from backend.app.main import app

# Create in-memory SQLite engine for isolated test runs
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
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


class TestAuthenticationEndpoints(unittest.TestCase):
    """Test suite covering User registration, login, JWT validation, and /api/auth/me."""

    @classmethod
    def setUpClass(cls):
        # Override get_db dependency to point to the isolated in-memory test database
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        # Recreate schema before each test for total isolation
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)

    def test_successful_registration(self):
        """Test registering a new user returns 201 Created and a valid JWT token."""
        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Alice FinOps",
                "email": "alice@cloudpilot.ai",
                "password": "SecurePassword123!",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["name"], "Alice FinOps")
        self.assertEqual(data["user"]["email"], "alice@cloudpilot.ai")
        self.assertIn("id", data["user"])
        self.assertIn("created_at", data["user"])

    def test_duplicate_email_registration(self):
        """Test registering an existing email returns 400 Bad Request."""
        payload = {
            "name": "Bob Admin",
            "email": "bob@cloudpilot.ai",
            "password": "Password123!",
        }
        # First registration succeeds
        r1 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(r1.status_code, 201)

        # Duplicate registration fails
        r2 = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(r2.status_code, 400)
        self.assertIn("Email is already registered", r2.json()["detail"])

    def test_successful_login(self):
        """Test logging in with valid credentials returns a valid JWT token."""
        self.client.post(
            "/api/auth/register",
            json={
                "name": "Charlie Dev",
                "email": "charlie@cloudpilot.ai",
                "password": "MySecretPass456",
            },
        )

        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "charlie@cloudpilot.ai",
                "password": "MySecretPass456",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "charlie@cloudpilot.ai")

    def test_invalid_password_login(self):
        """Test logging in with an incorrect password returns 401 Unauthorized."""
        self.client.post(
            "/api/auth/register",
            json={
                "name": "Dana SDE",
                "email": "dana@cloudpilot.ai",
                "password": "CorrectPassword123",
            },
        )

        response = self.client.post(
            "/api/auth/login",
            json={
                "email": "dana@cloudpilot.ai",
                "password": "WrongPassword!",
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("Invalid email or password", response.json()["detail"])

    def test_invalid_and_missing_jwt(self):
        """Test accessing protected /api/auth/me without or with invalid token returns 401."""
        # 1. Missing Authorization header
        r_missing = self.client.get("/api/auth/me")
        self.assertEqual(r_missing.status_code, 401)
        self.assertIn("Authentication token is missing", r_missing.json()["detail"])

        # 2. Invalid JWT signature
        r_invalid = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this.is.an.invalid.token.signature"},
        )
        self.assertEqual(r_invalid.status_code, 401)
        self.assertIn("Invalid or expired authentication token", r_invalid.json()["detail"])

    def test_authenticated_get_me_request(self):
        """Test accessing /api/auth/me with valid Bearer token returns user info."""
        reg_response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Eve Engineer",
                "email": "eve@cloudpilot.ai",
                "password": "EngineeringPassword789",
            },
        )
        self.assertEqual(reg_response.status_code, 201)
        token = reg_response.json()["access_token"]

        me_response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(me_response.status_code, 200)
        user_info = me_response.json()
        self.assertEqual(user_info["name"], "Eve Engineer")
        self.assertEqual(user_info["email"], "eve@cloudpilot.ai")
        self.assertIsInstance(user_info["id"], int)


if __name__ == "__main__":
    unittest.main()
