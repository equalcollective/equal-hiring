"""
Example: Using X-Ray SDK directly in backend code

This demonstrates how the backend can import and use the SDK as a library.
This is useful for instrumenting backend operations, testing, or server-side processing.
"""

from sdk import start_run, step, process_candidates


def example_backend_processing():
    """Example of using SDK in backend code."""
    
    with start_run(name="backend_data_processing", tags={"source": "backend"}):
        
        with step(name="validate_input", step_type="logic", reasoning="Validate incoming data"):
            # Your validation logic
            input_data = {"items": [1, 2, 3, 4, 5]}
            print("Validating input data...")
        
        with step(name="filter_items", step_type="filter", reasoning="Filter valid items"):
            items = input_data["items"]
            
            def filter_fn(item):
                if item > 2:
                    return True, None
                return False, "value_too_low"
            
            filtered = process_candidates(items, filter_fn)
            print(f"Filtered items: {filtered}")
        
        with step(name="save_results", step_type="logic", reasoning="Save processed data"):
            # Your save logic
            print("Saving results...")


if __name__ == "__main__":
    example_backend_processing()
