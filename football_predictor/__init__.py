# football_predictor/__init__.py

# Import the main engine class
from .engine import ProfessionalPredictionEngine

# Define what should be available when importing the package
__all__ = [
    'ProfessionalPredictionEngine'
]

# Note: EnhancedPredictor is used internally by ProfessionalPredictionEngine
# and doesn't need to be exported publicly
