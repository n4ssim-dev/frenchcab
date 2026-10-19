import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_ml_models import main_train

if __name__ == "__main__":
    main_train()
