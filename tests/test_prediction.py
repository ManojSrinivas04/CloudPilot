import unittest

from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.ml_engine import ml_engine
from backend.app.services.recommendation import (
    CapacityExceededError,
    UnsupportedRegionError,
    recommendation_service,
)


class TestMLAndRecommendation(unittest.TestCase):
    """Test suite covering ML inference, VM recommendations, and edge cases."""

    def test_ml_prediction_valid_workload(self):
        """Test ML prediction produces positive integer vCPU and RAM requirements."""
        vcpu, ram = ml_engine.predict_resources(
            application_type="E-Commerce",
            expected_users_per_day=25000,
            concurrent_users=600,
            storage_required_gb=300,
            deployment_region="asia-south",
            traffic_pattern="High",
        )
        self.assertIsInstance(vcpu, int)
        self.assertIsInstance(ram, int)
        self.assertGreaterEqual(vcpu, 1)
        self.assertGreaterEqual(ram, 1)
        self.assertEqual(vcpu, 2)
        self.assertEqual(ram, 4)

    def test_valid_recommendation_flow(self):
        """Test full recommendation flow with compute and storage cost calculations."""
        result = recommendation_service.recommend_cheapest_vm(
            predicted_vcpu=2,
            predicted_ram=4,
            deployment_region="asia-south",
            storage_required_gb=300,
        )

        self.assertEqual(result["cloud_provider"], "GCP")
        self.assertEqual(result["recommended_vm"], "e2-medium")
        self.assertAlmostEqual(result["price_per_hour_usd"], 0.033, places=3)
        self.assertEqual(result["storage_type"], "pd-balanced")
        self.assertAlmostEqual(result["compute_monthly_cost_usd"], 23.76, places=2)
        self.assertAlmostEqual(result["storage_monthly_cost_usd"], 30.00, places=2)
        self.assertAlmostEqual(result["monthly_cost_usd"], 53.76, places=2)
        self.assertAlmostEqual(result["yearly_cost_usd"], 645.12, places=2)

    def test_unsupported_region_raises_error(self):
        """Test that requesting an unknown region raises UnsupportedRegionError."""
        with self.assertRaises(UnsupportedRegionError) as context:
            recommendation_service.recommend_cheapest_vm(
                predicted_vcpu=2,
                predicted_ram=4,
                deployment_region="ap-south-1",  # Invalid region
                storage_required_gb=100,
            )

        self.assertIn("Unsupported deployment region 'ap-south-1'", str(context.exception))
        self.assertIn("asia-south", str(context.exception))

    def test_capacity_exceeded_raises_error(self):
        """Test that requesting resources beyond catalog maximum raises CapacityExceededError."""
        # Catalog max in asia-south is 16 vCPU, 32 GB RAM
        with self.assertRaises(CapacityExceededError) as context:
            recommendation_service.recommend_cheapest_vm(
                predicted_vcpu=32,  # Exceeds max 16 vCPU
                predicted_ram=64,   # Exceeds max 32 GB RAM
                deployment_region="asia-south",
                storage_required_gb=500,
            )

        self.assertIn("exceeds the maximum available single VM capacity", str(context.exception))
        self.assertEqual(context.exception.predicted_vcpu, 32)
        self.assertEqual(context.exception.predicted_ram, 64)

    def test_multi_cloud_comparison(self):
        """Test side-by-side comparison across AWS, Azure, and GCP."""
        comparison = recommendation_service.compare_all_providers(
            predicted_vcpu=2,
            predicted_ram=4,
            deployment_region="us-east",
            storage_required_gb=100,
        )

        self.assertGreaterEqual(len(comparison.options), 2)
        providers = [opt.cloud_provider for opt in comparison.options]
        self.assertIn("AWS", providers)
        self.assertIn("Azure", providers)
        self.assertIn("GCP", providers)

        # Exactly one option should be marked as cheapest
        cheapest_options = [opt for opt in comparison.options if opt.is_cheapest]
        self.assertEqual(len(cheapest_options), 1)
        self.assertEqual(cheapest_options[0].cloud_provider, comparison.recommended_provider)

    def test_supported_options_metadata(self):
        """Test supported options lists are correctly populated."""
        self.assertIn("E-Commerce", ml_engine.application_types)
        self.assertIn("asia-south", recommendation_service.supported_regions)
        self.assertIn("us-east", recommendation_service.supported_regions)
        self.assertIn("europe-west", recommendation_service.supported_regions)
        self.assertIn("High", ml_engine.traffic_patterns)


if __name__ == "__main__":
    unittest.main()
