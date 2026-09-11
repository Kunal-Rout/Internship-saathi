# Recommendation Engine & Scoring Logic

## 1. Design Philosophy

The recommendation engine in **Internship Saathi** is a **deterministic, content-based hybrid recommender**. It is designed with the following civic principles:

1. **Accessibility First**: Applicants with minimal schooling or zero prior experience are never penalized. Listings designed for beginners receive full score compatibility.
2. **Honesty & Explainability**: Every recommended opportunity provides 2–3 truthful, human-understandable reason codes (e.g. Same District, Sector Match, Beginner Friendly) in both English and Hindi.
3. **No Deceptive Percentages**: Scores are presented as **relative match tiers** ("Strong Match", "Good Match", "Relevant Opportunity") rather than "chances of admission" or "selection probability".
4. **No LLM Hallucinations**: Recommendations and explanations are generated deterministically using mathematical scoring formulas and structured locale dictionaries.

---

## 2. Recommendation Pipeline

```
Candidate Submission
        │
        ▼
[Step 1: Normalization & Validation]
  - Map education alias to canonical code (e.g., "12th" -> "twelfth_pass")
  - Deduplicate & clean skills and sectors
  - Resolve home state and district
        │
        ▼
[Step 2: Hard Eligibility Filters]
  - Exclude inactive (is_active == False)
  - Exclude expired (deadline < today)
  - Check education category (internship accepts candidate's education or 'any')
  - Apply mandatory constraints ONLY if candidate flagged them (is_work_mode_mandatory, is_location_mandatory)
        │
        ▼
[Step 3: Component Scoring (Bounded [0.0, 1.0])]
  - Skill Overlap Score (S_skill)
  - Sector Interest Match (S_sector)
  - Location Compatibility (S_loc)
  - TF-IDF Text Cosine Similarity (S_text)
        │
        ▼
[Step 4: Dynamic Weight Renormalization]
  - Non-applicable components have their base weights redistributed proportionally
        │
        ▼
[Step 5: Deterministic Tie-Breaking & Top-5 Selection]
  - Sorted by: (-Total_Score, Deadline ASC, ID ASC)
  - Limit to top 5 results
```

---

## 3. Mathematical Formulation

### 3.1 Base Weights
The default baseline weights are:
- **Skill Overlap**: $W_{skill} = 0.40$
- **Sector Interest**: $W_{sector} = 0.30$
- **Location Compatibility**: $W_{loc} = 0.20$
- **TF-IDF Similarity**: $W_{text} = 0.10$

$$\sum W_{base} = 1.00$$

### 3.2 Component Definitions

#### A. Skill Overlap ($S_{skill}$)
Let $C_{skills}$ be the candidate's normalized skills, and $I_{skills}$ be the internship's required skills:
- If $|I_{skills}| == 0$ or the internship has `allows_no_skills == True`:
  - If candidate has no skills: $S_{skill} = 1.0$ (perfect beginner match).
  - If candidate has skills: $S_{skill} = 0.8$.
  - Reason code: `NO_PRIOR_SKILLS_REQUIRED`.
- If $|I_{skills}| > 0$ and $|C_{skills}| > 0$:
  $$S_{skill} = \frac{|C_{skills} \cap I_{skills}|}{|I_{skills}|}$$
  - Reason code: `SKILL_MATCH` (lists up to 3 matched skills).
- If $|C_{skills}| == 0$ and $|I_{skills}| > 0$:
  - $S_{skill}$ is marked **Not Applicable (N/A)**. Its weight is redistributed via renormalization.

#### B. Sector Interest Match ($S_{sector}$)
Let $C_{sectors}$ be the set of sectors selected by the candidate:
- If $|C_{sectors}| > 0$:
  $$S_{sector} = \begin{cases} 1.0 & \text{if } I_{sector} \in C_{sectors} \\ 0.0 & \text{otherwise} \end{cases}$$
  - Reason code: `SECTOR_INTEREST` when $1.0$.
- If $|C_{sectors}| == 0$:
  - $S_{sector}$ is marked **Not Applicable (N/A)**.

#### C. Location Compatibility ($S_{loc}$)
Based on a documented deterministic preference matrix:
- **Remote Internships**:
  - Preferred mode is Remote: $S_{loc} = 1.0$ (`REMOTE_MATCH`).
  - Preferred mode is Any or Hybrid: $S_{loc} = 0.95$ (`REMOTE_FRIENDLY`).
  - Preferred mode is Onsite: $S_{loc} = 0.50$.
- **Onsite / Hybrid Internships**:
  - Same State + Same District: $S_{loc} = 1.0$ (`SAME_DISTRICT`).
  - Same State + Different District: $S_{loc} = 0.85$ (if willing to relocate) or $0.75$ (`SAME_STATE`).
  - Different State: $S_{loc} = 0.70$ (if willing to relocate, `RELOCATION_FRIENDLY`) or $0.20$.
- If no state/district was selected and mode is "any":
  - $S_{loc}$ is marked **Not Applicable (N/A)**.

#### D. TF-IDF Text Cosine Similarity ($S_{text}$)
- A `TfidfVectorizer(stop_words='english', max_features=1000)` is pre-fitted over the active internship corpus (concatenation of title, sector, description, and skills).
- The candidate's query document combines their normalized skills and sector names.
- Cosine similarity is computed between the query vector and the cached internship document vector:
  $$S_{text} = \cos(\mathbf{q}, \mathbf{d}_i) = \frac{\mathbf{q} \cdot \mathbf{d}_i}{\|\mathbf{q}\| \|\mathbf{d}_i\|}$$
  Bounded within $[0.0, 1.0]$.
- If candidate provided neither skills nor sectors:
  - $S_{text}$ is marked **Not Applicable (N/A)**.

---

## 4. Dynamic Weight Renormalization

When optional inputs are omitted or a component is Not Applicable, the engine **never scores the missing input as zero**. Instead, it dynamically renormalizes the remaining active components so the effective weights always sum to $1.00$:

$$\Omega_{active} = \{k \in \{\text{skill, sector, loc, text}\} \mid S_k \neq \text{N/A}\}$$

$$W_{eff, k} = \frac{W_{base, k}}{\sum_{j \in \Omega_{active}} W_{base, j}}$$

$$S_{total} = \sum_{k \in \Omega_{active}} S_k \times W_{eff, k}$$

### Example
If a candidate only provides education and sector interests (omitting skills and location):
- Active: Sector (0.30) and Text (0.10).
- Sum active = 0.40.
- $W_{eff, sector} = 0.30 / 0.40 = 0.75$
- $W_{eff, text} = 0.10 / 0.40 = 0.25$
- Effective weights sum to $1.00$.

---

## 5. Match Tiers and Categorization

Total relative score is translated into clear qualitative tiers:
- **Strong Match**: $S_{total} \ge 0.75$
- **Good Match**: $0.50 \le S_{total} < 0.75$
- **Relevant Opportunity**: $0.25 \le S_{total} < 0.50$
- **General Suggestion**: $S_{total} < 0.25$

When a candidate submits only education and no other preferences, the system returns eligible starter opportunities with `has_limited_profile = True` and an explicit note:
> *"Limited profile information provided. Showing eligible starter opportunities based on your education."*
