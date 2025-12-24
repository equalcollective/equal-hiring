# Founding Full-Stack Engineer - Take-Home Assignment

## Overview

Build an **X-Ray SDK and API** for debugging non-deterministic, multi-step algorithmic systems.

**Time Budget:** Half a day to a full day

**Tech Stack:** Your choice - use whatever you're most productive with

---

## The Problem

Modern software increasingly relies on multi-step, non-deterministic processes.

These systems are notoriously difficult to debug. Traditional logging tells you *what* happened, but not *why* a particular decision was made. When the final output is wrong, you're left reverse-engineering the entire pipeline.

**Example:** Imagine a competitor selection system for Amazon (which has 4+ billion products). Given a seller's product, the system must find the best competitor product to benchmark against:
1. Generate relevant search keywords from the product title and category (LLM step - non-deterministic)
2. Search and retrieve candidate competitor products (API step - large result set)
3. Apply filters (price range, rating threshold, review count, category match + LLM based ranking which is non-deterministic)
4. Use an LLM to evaluate relevance and eliminate false positives (LLM step - non-deterministic)
5. Rank and select the single best competitor


> We've basically written the whole selection flow without understanding the EXACT nature of data as that would require exact understanding of 4+ billion products. 

If the selected competitor is a poor match, which step failed? Did the LLM generate irrelevant keywords? Were the filters too strict, eliminating good candidates? Did the ranking algorithm pick the wrong product from qualified options? Without visibility into each decision point, debugging is guesswork.

---

## Your Task

Build an **X-Ray system** that provides transparency into multi-step decision processes.

### Deliverables

1. **X-Ray Library/SDK**
   - A lightweight wrapper that developers integrate into their code
   - Captures decision context at each step: inputs, candidates, filters applied, outcomes, and *reasoning*
   - Should be general-purpose (not tied to a specific domain)

2. **X-Ray API**
   - Ingest endpoint(s) for the SDK to send X-Ray data
   - Query endpoint(s) to retrieve and analyze X-Ray data

3. **Architecture Document**

   Name this file `ARCHITECTURE.md` and place it in the root of your repo.

   Write a short document (1-2 pages) with diagrams illustrating your data model and system design. Include a brief API spec—endpoint definitions, request/response shapes. Make it easy to skim.

   Keep it **as short and concise as possible**. We value clear, direct technical writing. AI tools are fine for formatting and polish, but the substance and reasoning must be yours. We're allergic to generic, hand-wavy architecture docs. We will reject candidates with AI slop that hasn't been verified by a human. The intent is to test your ability to think and reason about the problem.

   We don't expect you to implement and take care of all of these things in the actual SDK code or the API. But we'd love your thoughts on how you deal with these things, in terms of questions which we pointed out from an architecture perspective.

   Address the following:

   **Core Design (required):**

   - **Data Model Rationale:** Your architecture doc shows your data model. Explain *why* you structured it this way. What alternatives did you consider? What would break if you'd made different choices?

   - **Debugging Walkthrough:** A competitor selection run returns a bad match—a **phone case** matched against a **laptop stand**. Using your X-Ray system, how would someone figure out where things went wrong? Be specific about what they'd see and query.

   **Queryability**

   - Your system will be used across multiple different pipelines (competitor selection, listing optimization, categorization, etc.), each with different steps. A user wants to ask: "Show me all runs where the filtering step eliminated more than 90% of candidates"—regardless of which pipeline it was. How does your data model and query API support this? What constraints or conventions do you impose on developers to make this possible? Also think about variability in the context of those as well. These are use cases which we have given, but an X-ray system like this could be deployable at a million other use cases! Think about queryability in the context of those as well.

   **Performance & Scale**

   - Consider a step that takes 5,000 candidates as input and filters down to 30. Capturing full details for all 5,000 (including rejection reasons) might be prohibitively expensive. How does your system handle this? Describe the trade-offs between completeness, performance, and storage cost. Who decides what gets captured in full vs. summarized—the system or the developer?

   **Developer Experience**

   - Imagine a developer has an existing pipeline they want to instrument. Walk us through what changes they need to make to their code. Specifically: (a) What's the minimal instrumentation to get *something* useful? (b) What does full instrumentation look like? (c) What happens to the pipeline if the X-Ray backend is unavailable?

   **Real-World Application (optional):**

   - Describe a system you've worked on where X-Ray-style visibility would have saved debugging time. How would you retrofit this solution into that system? 

   **What Next??**

   - If you were to ship this SDK for real world use cases, what are other technical aspects you would want to work on?

4. **Video Walkthrough** (10 minutes max, Loom, unlisted YouTube, or similar)

   **Hard limit: 10 minutes.** We will stop watching at the 10-minute mark. There's a real human on the other side reviewing these—please respect our time.

   **Please have your face on camera.** We want to see you explain your work, not just hear a voiceover.

   Your video should cover:
   - **Architecture:** Walk us through your architecture—your data model, design decisions, and trade-offs. Don't just read your document aloud. Talk to us like you're explaining it to a colleague. We want to see that you *understand* it, not that you can recite it.
   - **Live demo:** Show a simple user interaction with your SDK. We want to see it actually work.
   - **Reflection:** Show us one moment where you were stuck or uncertain—how did you work through it?
   - (Optional) If AI tools helped you think about the problem differently, show us an example

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

---

## Example Scenarios

We've consciously made the choice not to give you example data which the SDK should be capable of taking in. That is your job to architect a data model which is fairly extensible. And we would want to know the reason you've made certain choices. But here are scenarios and SDK like this would be very useful.

### Scenario A: Competitor Discovery
Given a seller's product, find the most relevant competitor product to benchmark against.

- Generate search keywords from title, category, and attributes
- Retrieve candidate products from catalog
- Filter by price range, ratings, review velocity, category fit
- Rank remaining candidates by relevance
- Select the single best match

**Why X-Ray matters:** When the selected competitor is irrelevant (a **phone case** matched against a **laptop stand**), you need to know—was it bad keywords? Over-aggressive filters? Poor ranking logic?

### Scenario B: Listing Quality Optimization
Given an existing product listing, generate an optimized version.

- Analyze current listing (title, bullets, description, images)
- Extract high-performing patterns from top competitors
- Identify gaps and opportunities
- Generate improved content variations
- Score and select the best version

**Why X-Ray matters:** If the optimized listing underperforms, you need to trace back—did we learn from the wrong competitors? Miss key attributes? Generate content that didn't match the product?

### Scenario C: Product Categorization
Given a new product, assign it to the correct category in a taxonomy of 10,000+ categories.

- Extract product attributes from title and description
- Match against category requirements and signals
- Handle ambiguous cases (product fits multiple categories)
- Score confidence for top candidates
- Select best-fit category

**Why X-Ray matters:** Miscategorization hurts discoverability. When a "wireless phone charger" ends up in "office supplies," you need to see exactly where the classification logic went wrong.

## Evaluation Criteria

We're evaluating (in order of importance):

1. **System Design**
   - How is the SDK architected?
   - Is it genuinely general-purpose and extensible?
   - How clean is the integration API?

2. **First Principles Thinking**
   - Did you break down the problem from fundamentals, or just pattern-match to familiar solutions?
   - Can you clearly articulate *why* you made specific design choices?
   - How do you handle ambiguity and trade-offs?

3. **Communication & Writing**
   - Is your architecture document clear, concise, and well-structured?
   - Can you explain complex ideas simply in the video?
   - In the age of AI-assisted development, clear thinking and communication matter more than ever.

4. **Code Quality**
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

## Questions?

If anything is unclear, please reach out. We're happy to clarify.
