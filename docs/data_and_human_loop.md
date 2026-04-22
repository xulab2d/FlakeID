# Data And Human Loop

## Short Answer

You do not need reinforcement learning to get this system off the ground.

What you need first is:

- calibration data,
- tile-level scan data,
- candidate-level human labels,
- a small number of high-confidence flake exemplars.

Reinforcement learning only becomes useful later, after the microscope can already detect and rank flakes reliably.

## Data You Need In The First Month

### 1. Background And Calibration Images

Collect for each material workflow and each commonly used objective:

- 30 to 50 blank-substrate images with no flakes
- 10 to 20 images at each exposure setting you may actually use
- 10 to 20 images at the beginning and end of a session to quantify drift

Why:

- build flat-field correction
- estimate background color statistics
- quantify lamp and white-balance variation

## 2. Real Scan Tiles

Collect full scans, not just cropped flakes:

- at least 20 whole-slide or partial-slide scans per substrate/material workflow
- include easy, hard, clean, dirty, sparse, and residue-heavy samples

Why:

- discovery systems fail on the negative space if they only ever see curated positives
- real scan statistics matter for false-positive control

## 3. Candidate Review Labels

For each detected candidate, a reviewer should ideally assign:

- `accept`
- `reject`
- `ambiguous`

Optional but high-value tags:

- `graphene`
- `hbn`
- `few_layer`
- `thick`
- `folded`
- `cracked`
- `tape_residue`
- `contaminated`
- `good_for_transfer`

Bootstrap target:

- 200 to 500 reviewed candidates per workflow is enough to start improving ranking
- 1000 to 2000 reviewed candidates makes a serious phase-two model realistic

## 4. Thickness-Oriented Labels

If you care about monolayer or few-layer prioritization, also collect:

- 50 to 100 confirmed examples per thickness bin you care about
- Raman/AFM confirmation for a smaller gold-standard subset

Why:

- optical appearance is correlated with thickness, but camera and illumination confound it
- even a small confirmed set is enough to calibrate cluster meanings

## 5. Focus Data For Autofocus

When you add Z:

- capture focus stacks at representative sample locations
- save the true best-focus index chosen by a human

Why:

- autofocus becomes much easier if you treat it as a supervised ranking problem over local Z stacks

## The Right Human Loop

### Phase 1

Human reviews every surfaced candidate.

Goal:

- high recall
- learn the lab's nuisance modes

### Phase 2

Human reviews only the top-scoring or uncertain candidates.

Goal:

- active learning
- reduce annotation load while improving the model

### Phase 3

Human mostly validates the best-ranked flakes and inspects unusual failures.

Goal:

- turn the system into a trustworthy assistant rather than a noisy generator of boxes

## Where RL Actually Fits

Use RL only after the basics work.

The first worthwhile RL-like problems are usually contextual-bandit problems, not full reinforcement learning:

- which tile should be rescanned at higher magnification?
- which candidate should be surfaced to a human first?
- which scan regions are worth revisiting after coarse screening?

Possible rewards:

- reviewer accepted candidate
- confirmed monolayer or target-thickness discovery
- successful transfer or device fabrication outcome

That is much later than basic flake discovery.

## Practical Labeling Guidance

Keep the first review interface minimal:

- single hotkey for `accept`
- single hotkey for `reject`
- single hotkey for `ambiguous`
- optional tag panel only when needed

If you make reviewers answer ten questions per candidate, the dataset will stall out.

## Suggested Dataset Targets

### Minimum viable

- 20 scans per workflow
- 300 reviewed candidates per workflow
- 50 confirmed positives per workflow

### Strong phase-two training set

- 50 to 100 scans per workflow
- 1500 or more reviewed candidates per workflow
- 200 or more confirmed positive flakes per workflow
- 100 or more gold-standard thickness labels across bins

## Validation Metrics That Matter

- recall of human-accepted flakes
- false positives per square millimeter scanned
- time-to-first-good-flake
- precision among top `k` ranked candidates
- consistency across days and lamp conditions

