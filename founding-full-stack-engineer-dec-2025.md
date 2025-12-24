# Founding Full-Stack Engineer - Take-Home Assignment

## Overview

Build an **X-Ray library and dashboard** for debugging non-deterministic, multi-step algorithmic systems.

**Time Budget:** 4-6 hours (please do not exceed this)

**Tech Stack:** Your choice - use whatever you're most productive with

---

## The Problem

Modern software increasingly relies on multi-step, non-deterministic processes:

- An LLM generates search keywords from a product description
- A search API returns thousands of results
- Filters narrow down candidates based on business rules
- A ranking algorithm selects the final output

These systems are notoriously difficult to debug. Traditional logging tells you *what* happened, but not *why* a particular decision was made. When the final output is wrong, you're left reverse-engineering the entire pipeline.

**Example:** Imagine a product comparison system for Amazon (which has 4+ billion products). Given an input product, the system must:
1. Generate relevant search keywords (LLM step - non-deterministic)
2. Search and retrieve candidate products (API step - large result set)
3. Apply filters (price range, rating threshold, category match)
4. Rank and select the best comparators

If the final comparators are poor, which step failed? Was it bad keywords? Overly strict filters? A ranking bug? Without visibility into each decision point, debugging is guesswork.

---

## Your Task

Build an **X-Ray system** that provides transparency into multi-step decision processes.

### Deliverables

1. **X-Ray Library/SDK**
   - A lightweight wrapper that developers integrate into their code
   - Captures decision context at each step: inputs, candidates, filters applied, outcomes, and *reasoning*
   - Should be general-purpose (not tied to a specific domain)

2. **Dashboard UI**
   - Visualizes the complete decision trail for a given execution
   - Shows each step, what went in, what came out, and why
   - Makes it easy to identify where things went wrong

3. **Demo Application**
   - A simple multi-step workflow (2-3 steps) that demonstrates the library
   - **Use dummy/mock data** - we're evaluating your system design and decisions, not a working integration
   - **Suggested scenario: Competitor Product Selection**
     - Given a seller's product (the "prospect"), find the best competitor product to compare against
     - Step 1: Generate search keywords from the prospect's title/category (simulated LLM call)
     - Step 2: Search and retrieve candidate products (mock API returning dummy products)
     - Step 3: Apply filters (price range, rating threshold, review count) and select the best match
   - Feel free to modify this scenario or create your own - the demo exists to showcase your X-Ray system

4. **Video Walkthrough** (5-10 minutes, Loom or similar)
   - Walk through your solution and explain your thinking
   - Demonstrate the dashboard with your demo app
   - Discuss trade-offs and what you'd improve with more time
   - **Keep it informal** - we're more interested in how you think than a polished presentation

---

## What Makes This Different From Tracing

Traditional distributed tracing (Jaeger, Zipkin, etc.) answers: *"What functions were called and how long did they take?"*

X-Ray answers: *"Why did the system make this decision?"*

| Aspect | Traditional Tracing | X-Ray |
|--------|---------------------|-------|
| Focus | Performance & flow | Decision reasoning |
| Data | Spans, timing, service calls | Candidates, filters, selection logic |
| Question answered | "What happened?" | "Why this output?" |
| Granularity | Function/service level | Business logic level |

**Example X-Ray output for a competitor selection filter step:**
```
Step: Competitor Filter
├── Input: 47 candidate products
├── Reference Product: "Stainless Steel Water Bottle" ($25.00, 4.2★, 1,247 reviews)
├── Filters Applied:
│   ├── Price Range: 0.5x - 2x of reference ($12.50 - $50.00)
│   ├── Rating: minimum 3.8★
│   └── Reviews: minimum 100
├── Candidates Evaluated:
│   ├── ✓ HydroFlask 32oz ($34.99, 4.5★, 8,932 reviews) - PASSED all filters
│   ├── ✗ Generic Bottle ($8.99, 3.2★, 45 reviews) - FAILED: price below range, rating below 3.8, reviews below 100
│   ├── ✓ Yeti Rambler ($29.99, 4.4★, 5,621 reviews) - PASSED all filters
│   ├── ✗ Premium Titanium ($89.00, 4.8★, 234 reviews) - FAILED: price $89 > $50 max
│   └── ... (8 passed, 39 failed)
├── Selection: HydroFlask 32oz (highest review count among qualified)
└── Output: 1 competitor selected
```

This level of detail lets you immediately see why products were included or excluded, and why the final selection was made.

---

## Example X-Ray Data Structures

Below are example JSON structures for each step in a competitor selection pipeline. Your implementation doesn't need to match this exactly, but it illustrates the level of detail that makes X-Ray useful.

### Step 1: Keyword Generation

```json
{
  "step": "keyword_generation",
  "input": {
    "product_title": "Stainless Steel Water Bottle 32oz Insulated",
    "category": "Sports & Outdoors"
  },
  "output": {
    "keywords": ["stainless steel water bottle insulated", "vacuum insulated bottle 32oz"],
    "model": "gpt-4"
  },
  "reasoning": "Extracted key product attributes: material (stainless steel), capacity (32oz), feature (insulated)"
}
```

### Step 2: Candidate Search

```json
{
  "step": "candidate_search",
  "input": {
    "keyword": "stainless steel water bottle insulated",
    "limit": 50
  },
  "output": {
    "total_results": 2847,
    "candidates_fetched": 50,
    "candidates": [
      {"asin": "B0COMP01", "title": "HydroFlask 32oz Wide Mouth", "price": 44.99, "rating": 4.5, "reviews": 8932},
      {"asin": "B0COMP02", "title": "Yeti Rambler 26oz", "price": 34.99, "rating": 4.4, "reviews": 5621},
      {"asin": "B0COMP03", "title": "Generic Water Bottle", "price": 8.99, "rating": 3.2, "reviews": 45}
    ]
  },
  "reasoning": "Fetched top 50 results by relevance; 2847 total matches found"
}
```

### Step 3: Filter & Select

```json
{
  "step": "filter_and_select",
  "input": {
    "candidates_count": 50,
    "reference_product": {
      "asin": "B0XYZ123",
      "title": "ProBrand Steel Bottle",
      "price": 29.99,
      "rating": 4.2,
      "reviews": 1247
    }
  },
  "filters_applied": {
    "price_range": {"min": 12.50, "max": 59.98, "rule": "0.5x - 2x of reference price"},
    "min_rating": {"value": 3.8, "rule": "Must be at least 3.8 stars"},
    "min_reviews": {"value": 100, "rule": "Must have at least 100 reviews"}
  },
  "evaluations": [
    {
      "asin": "B0COMP01",
      "title": "HydroFlask 32oz Wide Mouth",
      "metrics": {"price": 44.99, "rating": 4.5, "reviews": 8932},
      "filter_results": {
        "price_range": {"passed": true, "detail": "$44.99 is within $12.50-$59.98"},
        "min_rating": {"passed": true, "detail": "4.5 >= 3.8"},
        "min_reviews": {"passed": true, "detail": "8932 >= 100"}
      },
      "qualified": true
    },
    {
      "asin": "B0COMP03",
      "title": "Generic Water Bottle",
      "metrics": {"price": 8.99, "rating": 3.2, "reviews": 45},
      "filter_results": {
        "price_range": {"passed": false, "detail": "$8.99 is below minimum $12.50"},
        "min_rating": {"passed": false, "detail": "3.2 < 3.8 threshold"},
        "min_reviews": {"passed": false, "detail": "45 < 100 minimum"}
      },
      "qualified": false
    }
  ],
  "summary": {
    "total_evaluated": 50,
    "passed": 8,
    "failed": 42
  },
  "selection": {
    "asin": "B0COMP01",
    "title": "HydroFlask 32oz Wide Mouth",
    "reason": "Highest review count (8932) among 8 qualified candidates"
  }
}
```

### What Makes Good X-Ray Data

When designing your X-Ray data structures, consider:

1. **Capture the "why"** - Every decision point should record its reasoning, not just inputs/outputs
2. **Be specific in failures** - "Failed price filter" is less useful than "Failed: $8.99 < $12.50 minimum"
3. **Preserve context** - Include enough information to reconstruct the decision without external lookups
4. **Keep it queryable** - Structure data so you can answer questions like "show me all products that failed the rating filter"
5. **Think about the dashboard** - What would a user need to see to debug a bad selection?

---

## Evaluation Criteria

We're evaluating (in order of importance):

1. **System Design**
   - How is the library architected?
   - Is it genuinely general-purpose and extensible?
   - How clean is the integration API?

2. **Dashboard UX**
   - Not just aesthetics - how *usable* is it?
   - Can you quickly understand what happened in an execution?
   - Is the information hierarchy clear?

3. **Code Quality**
   - Clean, readable, well-structured code
   - Sensible abstractions
   - Good separation of concerns

---

## Submission

1. Push your code to a GitHub repository
2. Include a README with:
   - Setup instructions
   - Brief explanation of your approach
   - Known limitations / future improvements
3. Upload your video walkthrough (YouTube unlisted, Loom, or similar)
4. Send us the repo link and video link

---

## Tips

- **Scope aggressively.** 4-6 hours is not much time. A polished, working subset is better than an ambitious but broken system.
- **Start with the data model.** What does an X-Ray record look like? Get this right first.
- **The demo app is secondary.** It exists only to showcase your X-Ray system. Keep it simple - dummy data is perfectly fine.
- **Show your thinking.** We care more about how you think and the decisions you make than a perfect implementation. The video walkthrough is your chance to explain your reasoning.

---

## Questions?

If anything is unclear, please reach out. We're happy to clarify.