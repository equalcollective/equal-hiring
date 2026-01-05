Youtube video: https://youtu.be/GHeFLikN2uA

# X-Ray SDK

Python SDK for decision observability in multi-step algorithmic systems.

## Installation

### Option 1: Install as a Package (Recommended)

Install the SDK as a proper Python package:

```bash
cd sdk
pip install -e .
```

The `-e` flag installs it in "editable" mode, so changes to the code are immediately available.

### Option 2: Install from Requirements

```bash
cd sdk
pip install -r requirements.txt
```

Note: This installs dependencies but doesn't install the SDK as a package. You'll need to add the SDK directory to your Python path.

### Option 3: Install in Development Mode

For development, you can install it in editable mode from the project root:

```bash
# From project root
pip install -e ./sdk
```

## Usage

### Basic Usage

```python
from sdk import start_run, step, process_candidates

# Start a run
with start_run(name="my_pipeline", tags={"version": "1.0"}):
    
    # Create a step
    with step(name="filter_products", step_type="filter"):
        candidates = [1, 2, 3, 4, 5]
        
        def filter_fn(item):
            if item > 3:
                return True, None  # Accepted
            return False, "too_small"  # Rejected with reason
        
        survivors = process_candidates(candidates, filter_fn)
        print(f"Survivors: {survivors}")
```

### Configure API URL

```python
from sdk import initialize

# Initialize with custom API URL
client = initialize(api_url="http://localhost:8000")

# Now use the convenience functions
with start_run(name="my_pipeline"):
    # ...
```

### Using in Backend Code

The SDK can be imported and used directly in backend code:

```python
# backend/app/some_module.py
from sdk import start_run, step

def process_data():
    with start_run(name="backend_processing"):
        with step(name="data_validation", step_type="logic"):
            # Your backend logic here
            pass
```

## API Reference

See the main project README for full API documentation.

