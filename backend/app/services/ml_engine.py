from typing import List, Tuple
import joblib
import pandas as pd

from backend.app.config import FEATURES_FILE_PATH, MODEL_FILE_PATH


class MLEngine:
    """Service to handle ML model inference for cloud resource prediction."""

    def __init__(self) -> None:
        if not MODEL_FILE_PATH.exists():
            raise FileNotFoundError(f"Model file not found at: {MODEL_FILE_PATH}")
        if not FEATURES_FILE_PATH.exists():
            raise FileNotFoundError(f"Features file not found at: {FEATURES_FILE_PATH}")

        self.model = joblib.load(MODEL_FILE_PATH)
        self.feature_columns: List[str] = joblib.load(FEATURES_FILE_PATH)

        self.application_types: List[str] = [
            "Banking",
            "Blog",
            "CRM",
            "E-Commerce",
            "ERP",
            "Healthcare",
            "News Portal",
            "Portfolio",
            "Social Media",
            "Streaming",
        ]

        self.traffic_patterns: List[str] = ["Low", "Medium", "High"]

    def preprocess(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encodes the inputs and aligns columns with the trained model features."""
        encoded_df = pd.get_dummies(input_df)
        aligned_df = encoded_df.reindex(
            columns=self.feature_columns,
            fill_value=0
        )
        return aligned_df

    def predict_resources(
        self,
        application_type: str,
        expected_users_per_day: int,
        concurrent_users: int,
        storage_required_gb: int,
        deployment_region: str,
        traffic_pattern: str,
    ) -> Tuple[int, int]:
        """
        Predicts required vCPU and RAM (GB) based on application workload attributes.

        Returns:
            Tuple[int, int]: (predicted_vcpu, predicted_ram_gb)
        """
        input_df = pd.DataFrame([{
            "application_type": application_type,
            "expected_users_per_day": expected_users_per_day,
            "concurrent_users": concurrent_users,
            "storage_required_gb": storage_required_gb,
            "deployment_region": deployment_region,
            "traffic_pattern": traffic_pattern,
        }])

        processed_input = self.preprocess(input_df)
        raw_prediction = self.model.predict(processed_input)

        predicted_vcpu = max(1, int(round(raw_prediction[0][0])))
        predicted_ram = max(1, int(round(raw_prediction[0][1])))

        return predicted_vcpu, predicted_ram


# Global singleton instance
ml_engine = MLEngine()
