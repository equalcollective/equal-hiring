"""
Simulation: Competitor Selection Process

This script demonstrates the X-Ray SDK in action by simulating a competitor selection
process where 5,000 products are retrieved and filtered down to 50 survivors.

Key demonstration:
- 5,000 products retrieved
- Filter applied: 4,950 rejected as "too expensive"
- SDK captures rejection histogram instead of logging 5,000 items
"""

import time
from typing import Dict, Tuple

from sdk import XRayClient, start_run, step, process_candidates


class Product:
    """Simple product representation for simulation."""

    def __init__(self, product_id: str, title: str, price: float, category: str, rating: float):
        self.product_id = product_id
        self.title = title
        self.price = price
        self.category = category
        self.rating = rating

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "product_id": self.product_id,
            "title": self.title,
            "price": self.price,
            "category": self.category,
            "rating": self.rating,
        }


def generate_search_keywords(product_title: str) -> list[str]:
    """Simulate LLM-based keyword generation (step 1)."""
    # Simulate some processing time
    time.sleep(0.1)

    # Simple keyword extraction (in real scenario, this would be an LLM call)
    words = product_title.lower().split()
    keywords = [w for w in words if len(w) > 3][:5]
    return keywords


def retrieve_candidates(keywords: list[str], max_results: int = 5000) -> list[Product]:
    """Simulate API-based product retrieval (step 2).
    
    Args:
        keywords: Search keywords (used in real scenario)
        max_results: Maximum number of candidates to retrieve
    """
    # Simulate API call delay
    time.sleep(0.2)
    _ = keywords  # Used in real scenario for API call

    # Generate fake candidate products
    candidates = []
    for i in range(max_results):
        # Vary prices: most are expensive, some are in range
        price = 150.0 + (i % 100) * 10.0 if i < 4950 else 20.0 + (i % 50) * 2.0
        candidates.append(
            Product(
                product_id=f"prod_{i:06d}",
                title=f"Competitor Product {i}",
                price=price,
                category="Electronics",
                rating=4.0 + (i % 10) * 0.1,
            )
        )

    return candidates


def filter_by_price(product: Product) -> Tuple[bool, str | None]:
    """
    Filter function for price filtering.

    Returns:
        Tuple of (accepted: bool, rejection_reason: str | None)
        - If accepted, returns (True, None)
        - If rejected, returns (False, reason_string)
    """
    max_price = 100.0
    if product.price > max_price:
        return False, "price_too_high"
    return True, None


def filter_by_rating(product: Product) -> Tuple[bool, str | None]:
    """Filter function for rating filtering."""
    min_rating = 4.5
    if product.rating < min_rating:
        return False, "rating_too_low"
    return True, None


def rank_candidates(candidates: list[Product]) -> Product:
    """Simulate ranking and selection (step 4)."""
    # Simple ranking: highest rating wins
    return max(candidates, key=lambda p: p.rating)


def simulate_competitor_selection(target_product: Product):
    """Main simulation: competitor selection pipeline."""

    # Initialize SDK (in real usage, this would connect to the backend API)
    # For simulation, we'll use a mock API URL - events will be dropped silently
    # The global client is used via start_run() context manager
    
    # Start a run
    with start_run(
        name="competitor_selection",
        tags={"target_product_id": target_product.product_id, "pipeline_version": "1.0"},
    ):
        # Step 1: Generate search keywords (LLM step)
        with step(name="generate_keywords", step_type="llm", reasoning="Extract relevant keywords from product title"):
            keywords = generate_search_keywords(target_product.title)
            print(f"Generated keywords: {keywords}")

        # Step 2: Retrieve candidate products (API step)
        with step(name="retrieve_candidates", step_type="retrieval", reasoning="Search product catalog"):
            candidates = retrieve_candidates(keywords, max_results=5000)
            print(f"Retrieved {len(candidates)} candidate products")

        # Step 3: Apply price filter (this is where we demonstrate smart summarization)
        with step(name="filter_by_price", step_type="filter", reasoning="Filter products within price range"):
            # This is the key: process_candidates will create a rejection histogram
            # instead of logging all 5,000 products
            price_filtered = process_candidates(
                candidates,
                filter_fn=filter_by_price,
                step_name="filter_by_price",
            )
            print(f"After price filtering: {len(price_filtered)} products remaining")

        # Step 4: Apply rating filter
        with step(name="filter_by_rating", step_type="filter", reasoning="Filter products above minimum rating"):
            rating_filtered = process_candidates(
                price_filtered,
                filter_fn=filter_by_rating,
                step_name="filter_by_rating",
            )
            print(f"After rating filtering: {len(rating_filtered)} products remaining")

        # Step 5: Rank and select best competitor (logic step)
        with step(
            name="rank_and_select",
            step_type="logic",
            reasoning="Select best match based on relevance score",
        ):
            selected_competitor = rank_candidates(rating_filtered)
            print("\nSelected competitor:")
            print(f"  Product ID: {selected_competitor.product_id}")
            print(f"  Title: {selected_competitor.title}")
            print(f"  Price: ${selected_competitor.price:.2f}")
            print(f"  Rating: {selected_competitor.rating:.2f}")

        return selected_competitor


def main():
    """Run the simulation."""
    print("=" * 60)
    print("X-Ray SDK Simulation: Competitor Selection")
    print("=" * 60)
    print()

    # Create a target product (the one we want to find competitors for)
    target_product = Product(
        product_id="target_001",
        title="Wireless Phone Charger Stand",
        price=29.99,
        category="Electronics",
        rating=4.7,
    )

    print(f"Target Product: {target_product.title}")
    print(f"Target Price: ${target_product.price:.2f}")
    print()

    try:
        selected = simulate_competitor_selection(target_product)

        print()
        print("=" * 60)
        print("Simulation Complete!")
        print("=" * 60)
        _ = selected  # Selected competitor (available for further processing)
        print()
        print("Key Points Demonstrated:")
        print("1. Context tracking across nested steps")
        print("2. Smart summarization: 5,000 candidates filtered to 50")
        print("3. Rejection histogram captures 'price_too_high' reason")
        print("4. Only survivors are logged, not all 5,000 items")
        print()
        print(
            "Note: Events are being batched and sent to http://localhost:8000/ingest"
        )
        print("If the backend is not running, events are silently dropped (fail-safe).")
        print()

    except Exception as e:
        print(f"Simulation error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
