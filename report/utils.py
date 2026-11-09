# flake8: noqa

# Locate and load the trained model artifact used by the dashboard.

import pickle
from pathlib import Path

# Anchor paths to this module so model lookup does not depend on the shell
# directory from which the dashboard was launched.
project_root = Path(__file__).parent.parent

# The asset-building script writes the fitted classifier to this location.
model_path = project_root / "assets" / "model.pkl"


def load_model():

    # Restore the fitted estimator, including its coefficients and feature names.
    # This reads an existing artifact; it does not train or update the model.
    with model_path.open("rb") as file:
        model = pickle.load(file)

    return model
