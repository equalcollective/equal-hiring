# Founding Full-Stack Engineer - Take-Home Assignment

## Overview

Build an **X-Ray library and dashboard** for debugging non-deterministic, multi-step algorithmic systems.

**Time Budget:** Half a day to a full day

**Tech Stack:** Your choice - use whatever you're most productive with

---

## The Problem

Modern software increasingly relies on multi-step, non-deterministic processes:

- An LLM generates search keywords from a product description
- A search API returns thousands of results
- Filters narrow down candidates based on business rules
- A ranking algorithm selects the final output

These systems are notoriously difficult to debug. Traditional logging tells you *what* happened, but not *why* a particular decision was made. When the final output is wrong, you're left reverse-engineering the entire pipeline.

**Example:** Imagine a competitor selection system for Amazon (which has 4+ billion products). Given a seller's product, the system must find the best competitor product to benchmark against:
1. Generate relevant search keywords from the product title and category (LLM step - non-deterministic)
2. Search and retrieve candidate competitor products (API step - large result set)
3. Apply filters (price range, rating threshold, review count, category match)
4. Use an LLM to evaluate relevance and eliminate false positives (LLM step - non-deterministic)
5. Rank and select the single best competitor

If the selected competitor is a poor match, which step failed? Did the LLM generate irrelevant keywords? Were the filters too strict, eliminating good candidates? Did the ranking algorithm pick the wrong product from qualified options? Without visibility into each decision point, debugging is guesswork.

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

Below are example JSON structures for each step in a competitor selection pipeline. **This is just one example use case.** The X-Ray library you build should be general-purpose and reusable across different systems and pipelines—whether it's competitor discovery, content recommendation, lead scoring, or any other multi-step decision process. The goal is a library that can be dropped into any part of your system where you need visibility into decision-making.

**Note on data format:** The JSON structures below are just one way to represent X-Ray data. In practice, different systems may need different formats or schemas. When building your library, consider how you'll handle varying data structures—will you enforce a strict schema, allow flexible key-value pairs, or something else? For this exercise, feel free to restrict to a specific format if it simplifies your implementation. We're more interested in your architectural thinking than supporting every edge case.

Your implementation doesn't need to match these structures exactly, but they illustrate the level of detail that makes X-Ray useful for debugging.

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

### Step 3: Apply Filters

```json
{
  "step": "apply_filters",
  "input": {
    "candidates_count": 50,
    "reference_product": {
      "asin": "B0XYZ123",
      "title": "ProBrand Steel Bottle 32oz Insulated",
      "price": 29.99,
      "rating": 4.2,
      "reviews": 1247
    }
  },
  "filters_applied": {
    "price_range": {"min": 14.99, "max": 59.98, "rule": "0.5x - 2x of reference price"},
    "min_rating": {"value": 3.8, "rule": "Must be at least 3.8 stars"},
    "min_reviews": {"value": 100, "rule": "Must have at least 100 reviews"}
  },
  "evaluations": [
    {
      "asin": "B0COMP01",
      "title": "HydroFlask 32oz Wide Mouth",
      "metrics": {"price": 44.99, "rating": 4.5, "reviews": 8932},
      "filter_results": {
        "price_range": {"passed": true, "detail": "$44.99 is within $14.99-$59.98"},
        "min_rating": {"passed": true, "detail": "4.5 >= 3.8"},
        "min_reviews": {"passed": true, "detail": "8932 >= 100"}
      },
      "qualified": true
    },
    {
      "asin": "B0COMP02",
      "title": "Yeti Rambler 26oz",
      "metrics": {"price": 34.99, "rating": 4.4, "reviews": 5621},
      "filter_results": {
        "price_range": {"passed": true, "detail": "$34.99 is within $14.99-$59.98"},
        "min_rating": {"passed": true, "detail": "4.4 >= 3.8"},
        "min_reviews": {"passed": true, "detail": "5621 >= 100"}
      },
      "qualified": true
    },
    {
      "asin": "B0COMP03",
      "title": "Generic Water Bottle",
      "metrics": {"price": 8.99, "rating": 3.2, "reviews": 45},
      "filter_results": {
        "price_range": {"passed": false, "detail": "$8.99 is below minimum $14.99"},
        "min_rating": {"passed": false, "detail": "3.2 < 3.8 threshold"},
        "min_reviews": {"passed": false, "detail": "45 < 100 minimum"}
      },
      "qualified": false
    },
    {
      "asin": "B0COMP04",
      "title": "Bottle Cleaning Brush Set",
      "metrics": {"price": 12.99, "rating": 4.6, "reviews": 3421},
      "filter_results": {
        "price_range": {"passed": false, "detail": "$12.99 is below minimum $14.99"},
        "min_rating": {"passed": true, "detail": "4.6 >= 3.8"},
        "min_reviews": {"passed": true, "detail": "3421 >= 100"}
      },
      "qualified": false
    }
  ],
  "output": {
    "total_evaluated": 50,
    "passed": 12,
    "failed": 38
  },
  "reasoning": "Applied price, rating, and review count filters to narrow candidates from 50 to 12"
}
```

### Step 4: LLM Relevance Evaluation

```json
{
  "step": "llm_relevance_evaluation",
  "input": {
    "candidates_count": 12,
    "reference_product": {
      "asin": "B0XYZ123",
      "title": "ProBrand Steel Bottle 32oz Insulated",
      "category": "Sports & Outdoors > Water Bottles"
    },
    "model": "gpt-4"
  },
  "prompt_template": "Given the reference product '{title}', determine if each candidate is a true competitor (same product type) or a false positive (accessory, replacement part, bundle, etc.)",
  "evaluations": [
    {
      "asin": "B0COMP01",
      "title": "HydroFlask 32oz Wide Mouth",
      "is_competitor": true,
      "confidence": 0.95
    },
    {
      "asin": "B0COMP02",
      "title": "Yeti Rambler 26oz",
      "is_competitor": true,
      "confidence": 0.92
    },
    {
      "asin": "B0COMP05",
      "title": "Replacement Lid for HydroFlask",
      "is_competitor": false,
      "confidence": 0.98
    },
    {
      "asin": "B0COMP06",
      "title": "Water Bottle Carrier Bag with Strap",
      "is_competitor": false,
      "confidence": 0.97
    }
  ],
  "output": {
    "total_evaluated": 12,
    "confirmed_competitors": 8,
    "false_positives_removed": 4
  },
  "reasoning": "LLM identified and removed 4 false positives (accessories and replacement parts)"
}
```

### Step 5: Rank & Select

```json
{
  "step": "rank_and_select",
  "input": {
    "candidates_count": 8,
    "reference_product": {
      "asin": "B0XYZ123",
      "title": "ProBrand Steel Bottle 32oz Insulated",
      "price": 29.99,
      "rating": 4.2,
      "reviews": 1247
    }
  },
  "ranking_criteria": {
    "primary": "review_count",
    "secondary": "rating",
    "tertiary": "price_proximity"
  },
  "ranked_candidates": [
    {
      "rank": 1,
      "asin": "B0COMP01",
      "title": "HydroFlask 32oz Wide Mouth",
      "metrics": {"price": 44.99, "rating": 4.5, "reviews": 8932},
      "score_breakdown": {
        "review_count_score": 1.0,
        "rating_score": 0.9,
        "price_proximity_score": 0.7
      },
      "total_score": 0.92
    },
    {
      "rank": 2,
      "asin": "B0COMP02",
      "title": "Yeti Rambler 26oz",
      "metrics": {"price": 34.99, "rating": 4.4, "reviews": 5621},
      "score_breakdown": {
        "review_count_score": 0.63,
        "rating_score": 0.85,
        "price_proximity_score": 0.85
      },
      "total_score": 0.74
    },
    {
      "rank": 3,
      "asin": "B0COMP07",
      "title": "Stanley Adventure Quencher",
      "metrics": {"price": 35.00, "rating": 4.3, "reviews": 4102},
      "score_breakdown": {
        "review_count_score": 0.46,
        "rating_score": 0.8,
        "price_proximity_score": 0.84
      },
      "total_score": 0.65
    }
  ],
  "selection": {
    "asin": "B0COMP01",
    "title": "HydroFlask 32oz Wide Mouth",
    "reason": "Highest overall score (0.92) - top review count (8,932) with strong rating (4.5★)"
  },
  "output": {
    "selected_competitor": {
      "asin": "B0COMP01",
      "title": "HydroFlask 32oz Wide Mouth",
      "price": 44.99,
      "rating": 4.5,
      "reviews": 8932
    }
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
- **Use AI assistance freely.** We're believers in AI-assisted development—not AI-generated slop, but thoughtful use of AI tools. Use them for brainstorming, architecture discussions, rubber-ducking ideas, and yes, coding too. We find AI is often most valuable in the thinking and planning phases. Just make sure you understand and can explain everything you submit.

---

## Questions?

If anything is unclear, please reach out. We're happy to clarify.
