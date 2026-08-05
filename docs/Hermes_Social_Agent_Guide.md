# Hermes Social Agent --- Complete 0→100 Build Guide

**Project:** Hermes Social Agent\
**Purpose:** Build a 24/7, quality-first, self-improving social content
agent for LinkedIn, Instagram, and X (Twitter), controlled through
Telegram and designed to operate at the lowest practical marginal cost
using the user's existing infrastructure/subscriptions.

> **Important cost rule:** The architecture is designed for **₹0
> marginal cost wherever possible**, using existing Hermes/EC2/model
> access and free/local software. It is **not valid to promise permanent
> 100% free operation** because social-platform APIs, quotas, account
> permissions, cloud free tiers, and consumer AI subscription
> capabilities can change. Never silently switch to a paid API or
> service. If a required action would cost money, stop and notify the
> user through Telegram.

------------------------------------------------------------------------

# 1. What We Are Building

This is **not a social-media scheduler** and not a basic AI content
generator.

The target system is a persistent **Social Content Intelligence Agent**
that:

1.  Discovers emerging and trending topics from high-quality sources.
2.  Filters trends against the brand's audience and content pillars.
3.  Identifies content gaps rather than blindly copying trends.
4.  Performs multi-source research.
5.  Separates verified facts, opinions, predictions, and user-provided
    personal experience.
6.  Fact-checks important claims before content generation.
7.  Decides whether the idea should become:
    -   text-only post,
    -   single-image post,
    -   carousel/document,
    -   X thread,
    -   or be rejected entirely.
8.  Writes a master narrative.
9.  Adapts the narrative separately for LinkedIn, Instagram, and X.
10. Applies a permanent brand system.
11. Researches visual inspiration without copying designs.
12. Generates artwork/design assets where appropriate.
13. Uses deterministic rendering/composition for final branded assets.
14. Runs a multi-stage quality gate.
15. Schedules/publishes one primary post per day.
16. Collects post-performance data at multiple time windows.
17. Compares results against historical baselines.
18. Runs controlled content experiments.
19. Records hypotheses and learns only when enough evidence exists.
20. Updates strategy memory.
21. Gives the user full natural-language control through Telegram.
22. Maintains a human-readable Google Sheets command center.
23. Maintains a human-readable Obsidian strategy/knowledge vault.
24. Uses SQLite as the authoritative machine database.
25. Runs continuously on the existing Hermes EC2 server.

The long-term goal is:

> **Post #100 should be better informed by the account's own evidence
> than Post #1.**

------------------------------------------------------------------------

# 2. Existing Infrastructure We Will Reuse

The existing Hermes installation already runs 24/7 on EC2 and already
has Telegram/gateway functionality.

Current model routing observed during planning:

``` text
Primary:
nvidia/nemotron-3-ultra-550b-a55b via NVIDIA

Fallback 1:
z-ai/glm-5.2 via NVIDIA

Fallback 2:
nvidia/nemotron-3-ultra-550b-a55b:free via OpenRouter

Fallback 3:
stepfun/step-3.7-flash:free via Nous
```

Do **not** add more models merely because they are free.

First build instrumentation that tells us: - which model handled which
job, - latency, - failures, - retries, - quality score, - and whether
another model had to repair its output.

Add another model only when measured evidence shows a specific weakness.

------------------------------------------------------------------------

# 3. AI Responsibilities During Development

We will use **Google Antigravity** as the coding environment.

## Claude Opus 4.6 --- Primary Builder

Use Claude Opus 4.6 for:

-   repository architecture;
-   database design implementation;
-   state machines;
-   orchestration;
-   Python modules;
-   integrations;
-   adapters;
-   Telegram command routing;
-   scheduling;
-   tests;
-   migrations;
-   logging;
-   error handling;
-   retry/idempotency logic;
-   configuration;
-   Hermes skill files;
-   documentation;
-   refactoring;
-   fixing issues found by audits.

Claude is the **implementation engineer**.

## Gemini 3.1 Pro --- Architecture/Audit/Adversarial Reviewer

Use Gemini 3.1 Pro for:

-   reviewing this guide before implementation;
-   challenging architecture;
-   finding missing requirements;
-   identifying overengineering;
-   security review;
-   API/integration review;
-   concurrency review;
-   state-transition review;
-   duplicate-post risks;
-   analytics methodology review;
-   self-learning logic review;
-   prompt/brand-system review;
-   test coverage audit;
-   final repository audit before deployment;
-   reviewing generated visual/design workflows.

Gemini is the **independent reviewer**, not the main coder.

## Development Rule

Never let the same model both implement a major subsystem and be the
only model that approves it.

Use:

``` text
Guide
  ↓
Gemini architecture audit
  ↓
Claude implementation
  ↓
Automated tests
  ↓
Gemini adversarial audit
  ↓
Claude fixes
  ↓
Tests
  ↓
Deployment
```

------------------------------------------------------------------------

# 4. User Responsibilities vs AI Responsibilities

## The user must do

The user handles account-side or judgment-sensitive work:

-   approve the final brand positioning;
-   provide logo files and real brand assets;
-   define initial content pillars;
-   provide examples of content/designs they genuinely like;
-   provide personal stories/experiences that the agent is allowed to
    use;
-   authorize Google/Meta/LinkedIn/X accounts where required;
-   create/download OAuth credentials;
-   configure platform developer applications if needed;
-   review platform permissions/terms;
-   connect Google Sheets;
-   create/choose the Obsidian vault;
-   approve first production posts;
-   approve any paid service before use;
-   decide when a platform can move from approval mode to autopilot;
-   monitor initial production behavior.

## AI/Antigravity should do

-   build the entire repository;
-   create schemas/migrations;
-   create all local services;
-   build the trend/research/content/design/analytics pipeline;
-   build the Google Sheets synchronization layer;
-   build Obsidian Markdown synchronization;
-   build Telegram command handlers;
-   build platform adapter interfaces;
-   implement available official publishing adapters;
-   build manual-fallback publishing flow;
-   build metrics collectors where authorized;
-   build content-quality gates;
-   build learning/experiment engine;
-   write tests;
-   write setup scripts;
-   write `.env.example`;
-   write Hermes `SKILL.md`;
-   write deployment scripts/docs;
-   never hard-code user secrets.

------------------------------------------------------------------------

# 5. Non-Negotiable Product Principles

## 5.1 Quality over volume

Default target:

``` text
1 primary content idea per day
≈ 30 primary ideas/month
```

The system is allowed to **skip a day** if no candidate passes the
quality gate.

Never manufacture filler merely to satisfy a schedule.

## 5.2 One idea, platform-native executions

Never generate one caption and paste it everywhere.

Pipeline:

``` text
Master researched idea
    ├── LinkedIn execution
    ├── Instagram execution
    └── X execution
```

Each platform adapter can choose a different format.

## 5.3 Brand consistency is a first-class metric

The optimizer must never maximize impressions at the expense of brand
quality.

## 5.4 No fake personal experience

Content must classify statements as:

-   `FACT`
-   `OPINION`
-   `PREDICTION`
-   `PERSONAL_EXPERIENCE`

`PERSONAL_EXPERIENCE` is allowed only when the user supplied it or
explicitly approved it.

## 5.5 No unsupported certainty

Important factual claims must retain source provenance.

## 5.6 No uncontrolled self-modification

The agent may update **strategy rules/data**, but must not autonomously
rewrite production code, credentials, security rules, publishing
permissions, or core quality thresholds.

## 5.7 User always has final authority

Priority:

``` text
Telegram user command
    >
User-created/manual schedule
    >
Approved scheduled content
    >
Autonomous content plan
```

------------------------------------------------------------------------

# 6. System Architecture

``` text
                       HERMES SOCIAL AGENT
                               │
          ┌────────────────────┴────────────────────┐
          │                                         │
   AUTONOMOUS MODE                           TELEGRAM COMMAND MODE
          │                                         │
          └────────────────────┬────────────────────┘
                               ▼
                         SOCIAL SUPERVISOR
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
               TREND ENGINE        ACCOUNT MEMORY
                     │                   │
                     └─────────┬─────────┘
                               ▼
                      OPPORTUNITY SCORER
                               │
                               ▼
                         DEEP RESEARCH
                               │
                               ▼
                          FACT CHECKER
                               │
                               ▼
                         KNOWLEDGE PACK
                               │
                               ▼
                      CONTENT STRATEGIST
                               │
                               ▼
                          BRAND BRAIN
                               │
                               ▼
                      MASTER CONTENT WRITER
                               │
                               ▼
                         CONTENT COUNCIL
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
    Skeptic              Audience Critic        Growth Critic
        └──────────────────────┼──────────────────────┘
                               ▼
                       EDITOR-IN-CHIEF GATE
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
                POST                     CAROUSEL
                  │                         │
                  └────────────┬────────────┘
                               ▼
                       CREATIVE DIRECTOR
                               │
                     Inspiration research
                               │
                         Design brief
                               │
                         Image assets
                               │
                   Pillow/ImageMagick layer
                               │
                         CREATIVE QA
                               │
                               ▼
                       PLATFORM ADAPTERS
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
           LinkedIn        Instagram           X
               │               │               │
               └───────────────┼───────────────┘
                               ▼
                            PUBLISH
                               │
                  2h / 24h / 72h snapshots
                               │
                               ▼
                     PERFORMANCE ANALYZER
                               │
                               ▼
                       EXPERIMENT ENGINE
                               │
                               ▼
                        STRATEGY MEMORY
                               │
                               └──────► future content
```

------------------------------------------------------------------------

# 7. Storage Architecture

Use different tools for different jobs.

## SQLite --- Authoritative Machine Memory

SQLite is the source of truth for structured operational data.

Why: - free; - local; - reliable; - transactional; - easy backups; -
excellent for one-agent scale; - no external database bill.

## Google Sheets --- Human Command Center

Sheets is for visibility, not authoritative transactional state.

Recommended tabs:

1.  `Dashboard`
2.  `Content Calendar`
3.  `Topic Queue`
4.  `Research`
5.  `Posts`
6.  `Assets`
7.  `Publishing`
8.  `Performance`
9.  `Experiments`
10. `Learnings`
11. `Platform Strategy`
12. `Errors & Alerts`

The user should be able to open one sheet and understand: - what
posted; - what is scheduled; - what is waiting for approval; - current
topics; - performance; - current experiments; - major lessons; -
failures.

## Obsidian --- Human-Readable Strategy Brain

Obsidian remains local/free. Do not require paid Sync or Publish.

Suggested vault:

``` text
Hermes-Social-Agent/
├── 00-Brand/
│   ├── Brand-Identity.md
│   ├── Voice.md
│   ├── Audience.md
│   ├── Visual-System.md
│   ├── Content-Pillars.md
│   └── Banned-Patterns.md
├── 01-Platform-Intelligence/
│   ├── LinkedIn.md
│   ├── Instagram.md
│   └── X.md
├── 02-Research/
├── 03-Winning-Patterns/
├── 04-Failed-Patterns/
├── 05-Experiments/
├── 06-Competitor-Intelligence/
├── 07-Strategy/
├── 08-Monthly-Reviews/
└── 09-Decision-Log/
```

Hermes may update these Markdown files only through a controlled
knowledge writer.

## NotebookLM --- Research Laboratory

NotebookLM is supplementary.

Use it for: - deep human review of research corpora; - studying
platform/algorithm material; - interrogating curated source
collections; - understanding long documents; - comparing research
sources.

Do **not** make the autonomous production pipeline dependent on
NotebookLM unless a supported automation interface is explicitly
available and verified.

The system must continue functioning if NotebookLM is unavailable.

------------------------------------------------------------------------

# 8. Proposed SQLite Schema

Claude should normalize this where useful, but preserve these concepts.

## `topics`

``` text
id
canonical_topic
summary
category
content_pillar
discovered_at
trend_started_at
trend_velocity
audience_relevance
saturation_score
unique_angle_score
visual_potential
source_authority
opportunity_score
status
rejection_reason
created_at
updated_at
```

## `topic_sources`

``` text
id
topic_id
source_type
source_name
url
published_at
discovered_at
authority_score
raw_excerpt_hash
notes
```

## `research_runs`

``` text
id
topic_id
started_at
completed_at
model_route
status
confidence
research_summary
```

## `research_claims`

``` text
id
research_run_id
claim
claim_type
confidence
verification_status
contradiction_status
source_count
created_at
```

## `claim_sources`

Maps claims to sources.

## `content_ideas`

``` text
id
topic_id
angle
audience_problem
core_value
format_recommendation
originality_score
brand_fit_score
information_value_score
status
```

## `posts`

``` text
id
content_idea_id
platform
format
master_post_id
version
hook
body
cta
hashtags
word_count
slide_count
brand_score
quality_score
approval_status
scheduled_at
published_at
platform_post_id
platform_url
status
```

## `assets`

``` text
id
post_id
asset_type
path
width
height
checksum
generation_method
prompt_reference
design_system
qa_status
```

## `performance_snapshots`

``` text
id
post_id
window
captured_at
impressions
reach
likes
comments
shares
saves
clicks
profile_visits
follows
reposts
other_metrics_json
```

Store unavailable metrics as null, not zero.

## `experiments`

``` text
id
name
hypothesis
platform
variable
variant_a
variant_b
start_date
end_date
minimum_samples
status
confidence
conclusion
```

## `post_experiment_assignments`

Maps posts to experiment variants.

## `strategy_rules`

``` text
id
platform
rule
evidence_summary
sample_size
confidence
status
created_at
last_validated_at
```

Statuses:

``` text
HYPOTHESIS
TESTING
PROVISIONAL
CONFIRMED
RETIRED
```

## `brand_rules`

Permanent or user-approved brand rules.

## `scheduled_actions`

Used for user-requested future actions.

## `telegram_commands`

Audit trail for commands and resulting actions.

## `model_runs`

Record: - task type; - model route; - start/end; - success; - retry; -
quality; - token/usage metadata if available; - error.

## `system_events`

Operational audit log.

------------------------------------------------------------------------

# 9. Trend Intelligence Engine

The Trend Hunter should search multiple categories rather than one feed.

Potential categories: - technical/news sources; - forums; - community
discussions; - developer communities; - selected industry
publications; - RSS feeds; - Google Trends where practical; - public
social discussions where access permits; - creator/account watchlists; -
product launch communities.

Never rely on a single source.

## Opportunity formula

Do not hard-code a fake "scientific" formula permanently. Start with a
transparent weighted score and calibrate it from real outcomes.

Initial conceptual factors:

``` text
Freshness
× Trend Velocity
× Audience Relevance
× Source Authority
× Unique-Angle Potential
× Visual Potential
× Content-Pillar Fit
× (1 - Saturation)
```

The system must record the component scores so we can later determine
whether the opportunity model predicts performance.

## Content-gap analysis

For high-scoring topics ask:

1.  What is everybody repeating?
2.  What important fact/context is missing?
3.  What is misunderstood?
4.  What questions are users repeatedly asking?
5.  What opposing interpretation exists?
6.  What can our audience actually use?
7.  Can we contribute something original?
8.  Is this already over-saturated?

A trending topic without a useful angle should be rejected.

------------------------------------------------------------------------

# 10. Research Engine

For each accepted candidate:

1.  collect multiple independent sources;
2.  prefer primary/authoritative sources;
3.  capture publication dates;
4.  identify key claims;
5.  identify numerical claims;
6.  identify uncertainty;
7.  identify disagreements;
8.  identify what is confirmed vs speculation;
9.  store provenance;
10. create a compact knowledge pack.

Research output:

``` text
TOPIC
WHY NOW
AUDIENCE RELEVANCE
VERIFIED FACTS
IMPORTANT NUMBERS
CONTEXT
WHAT PEOPLE ARE GETTING WRONG
OPPOSING VIEW
UNCERTAINTIES
POTENTIAL ANGLES
SOURCE MAP
```

## Fact-checking rule

High-impact factual claims should have strong source support.

Never create citations/sources that were not actually retrieved.

------------------------------------------------------------------------

# 11. Content Pillars

Before production, the user must approve 4--6 content pillars.

Example structure only:

``` text
Pillar
Purpose
Target audience
Allowed topics
Disallowed topics
Typical formats
Brand objective
```

Trend discovery must map candidates to a pillar.

A viral topic outside the brand's pillars should normally be rejected.

------------------------------------------------------------------------

# 12. Brand Brain

Branding is equally important to reach.

Create a dedicated Hermes skill and knowledge folder.

Brand Brain must include:

## Brand identity

-   brand purpose;
-   positioning;
-   target audience;
-   expertise;
-   values;
-   differentiators;
-   desired perception.

## Voice

-   sentence style;
-   vocabulary;
-   level of technical depth;
-   humor policy;
-   opinion policy;
-   punctuation tendencies;
-   preferred opening styles;
-   preferred closing styles.

## Banned writing patterns

Examples: - fake personal stories; - generic motivational filler; -
unsupported superlatives; - "game changer" style clichés unless
justified; - repetitive AI transitions; - meaningless CTAs; -
manufactured controversy; - excessive hashtags; - fake certainty; -
copied creator phrasing.

## Visual system

Define: - logo rules; - primary/secondary palette; - typography; -
spacing; - border/radius style; - illustration style; - photography
style; - icon style; - chart style; - carousel grid; - title
hierarchy; - footer/signature; - safe areas; - platform dimensions; -
accessibility/contrast rules.

## Visual families

Create 3--5 recognizable design families, for example:

``` text
Editorial Explainer
Technical Diagram
Bold Opinion
Data/Insight
Product/News Breakdown
```

The agent may choose among approved families but cannot invent an
unrelated visual identity every day.

------------------------------------------------------------------------

# 13. Human Writing System

Do not use a prompt that merely says "sound human."

Build a reusable writer skill from: - user-approved examples; -
preferred language; - banned phrases; - structural rules; - content
pillars; - prior successful content; - brand voice.

## Master content

First create one platform-neutral narrative:

``` text
Hook idea
Core thesis
Why it matters
Evidence
Insight
Practical takeaway
Optional CTA
```

Then adapt it.

## LinkedIn adapter

Optimize for: - professional relevance; - clear narrative; - useful
insight; - readable formatting; - meaningful discussion; -
document/carousel when appropriate.

## Instagram adapter

Optimize for: - visual storytelling; - strong first slide; - save/share
utility; - concise caption; - carousel progression; - brand recognition.

## X adapter

Optimize for: - compressed clarity; - sharp hook; - conversational
language; - standalone post vs thread decision; - no unnecessary
LinkedIn-style formatting.

------------------------------------------------------------------------

# 14. Content Council

Every candidate final draft passes independent review roles.

## Research Critic

Checks: - factual accuracy; - source support; - misleading
simplification; - stale information.

## Skeptic

Asks: - what could be wrong? - what would a knowledgeable critic
challenge? - are we overstating anything?

## Audience Critic

Asks: - why should the target audience care? - what do they gain? - is
this obvious/common knowledge?

## Human-Writing Critic

Detects: - AI clichés; - repetitive rhythm; - generic hook; -
unnecessary drama; - unnatural transitions; - fake authority; - filler.

## Brand Critic

Checks: - voice; - positioning; - visual identity; - content pillar; -
brand risk.

## Growth Critic

Checks: - stop-scroll strength; - clarity; - share/save potential; -
discussion potential; - format choice.

## Editor-in-Chief

Makes final decision:

``` text
PASS
REVISE
REJECT
NEEDS_USER_INPUT
```

------------------------------------------------------------------------

# 15. Quality Gate

Initial thresholds should be configurable, not buried in code.

Suggested starting gate:

``` text
Research confidence       >= 90
Audience relevance        >= 80
Originality               >= 80
Information value         >= 80
Brand fit                 >= 90
Writing quality           >= 85
Visual quality            >= 85 (when visual)
Claim verification        PASS
Duplicate check           PASS
Personal-experience check PASS
```

Do not endlessly regenerate.

Maximum automatic revision loops should be configurable (e.g. 2--3).
After that:

``` text
NEEDS_USER_REVIEW
```

------------------------------------------------------------------------

# 16. Creative Director & Inspiration System

The agent may research Pinterest, Dribbble, design publications, and
other visual references **for inspiration**.

It must not: - reproduce a creator's layout pixel-for-pixel; - copy
logos/illustrations; - remove watermarks; - present copied artwork as
original.

The Creative Director outputs a structured design brief:

``` text
Platform
Format
Dimensions
Design family
Visual objective
Typography hierarchy
Grid/layout
Slide-by-slide content
Image requirements
Illustration requirements
Charts/data
Brand elements
Accessibility
Export requirements
Generation prompts
```

------------------------------------------------------------------------

# 17. Why Pillow / ImageMagick Are Needed

AI image generation should not be responsible for precise final
typography and layout.

Use Pillow and/or ImageMagick for deterministic production work:

-   exact canvas dimensions;
-   resize/crop;
-   safe-area handling;
-   background placement;
-   overlays;
-   brand logo placement;
-   typography;
-   slide numbers;
-   consistent margins;
-   image compression;
-   format conversion;
-   assembling generated artwork into templates;
-   validating dimensions;
-   exporting carousel images;
-   generating thumbnails/previews.

Rule:

``` text
AI = creative artwork/visual concepts
Pillow/ImageMagick = precise production assembly
```

Prefer one primary renderer where possible to reduce complexity. Claude
should benchmark which is simpler for the final design system.

------------------------------------------------------------------------

# 18. Image Generation

Use existing ChatGPT/Gemini consumer access manually or through
officially supported integration paths available to the user.

**Critical:** A consumer subscription must never be assumed to include
an automatable API.

Therefore create an abstraction:

``` text
ImageProvider
├── SupportedAutomatedProvider
├── HermesImageProvider
└── ManualImageRequestProvider
```

If no zero-cost supported automation route exists, Telegram should send
the user: - the approved image prompt; - design brief; - required
dimensions; - reference context.

The user can generate the image in their existing subscription and
return/save the asset.

This keeps the architecture functional without secretly adding API
charges.

------------------------------------------------------------------------

# 19. Publishing Layer

Create a generic interface:

``` text
PublisherAdapter
├── LinkedInPublisher
├── InstagramPublisher
├── XPublisher
└── ManualApprovalPublisher
```

Each platform adapter must support:

``` text
validate_credentials()
validate_permissions()
prepare_payload()
publish()
verify_publish()
fetch_post_reference()
handle_failure()
```

Never mark a post `PUBLISHED` merely because an API call was attempted.

Require verification or a returned platform post identifier.

## Platform-access rule

During implementation, Gemini must verify current official API
capabilities, permissions, pricing, rate limits, and content-format
support from official documentation.

Do not encode assumptions from this guide as permanent truth.

If official zero-cost publishing is unavailable: - do not use a paid API
without approval; - do not build brittle
credential-stealing/session-cookie automation; - fall back to
`READY_FOR_MANUAL_PUBLISH`; - send the complete post/assets to Telegram.

------------------------------------------------------------------------

# 20. Scheduling

Default:

``` text
1 primary post/day
```

The scheduler must support: - platform-specific times; - user-specified
dates; - pause; - skip; - reschedule; - cancel; - approval deadlines; -
blackout dates; - emergency stop.

Never create duplicate scheduled jobs after restart.

Use idempotency keys.

------------------------------------------------------------------------

# 21. Telegram --- Full Remote Control

Telegram is a first-class interface.

The user should be able to speak naturally, not memorize commands.

Examples:

``` text
What are you posting tomorrow?
Show me today's research.
Give me the five best topic candidates.
Why did yesterday's LinkedIn post underperform?
What have you learned this month?
Create a carousel about AI agents.
Use this topic tomorrow instead.
Post this on LinkedIn next Friday at 10 AM.
Do not post tomorrow.
Pause Instagram for one week.
Cancel the August 12 post.
Rewrite only slide 1.
Make the design more minimal.
Show me the final assets.
Approve tomorrow's post.
Reject this idea.
Switch tomorrow to a single-image post.
Show this week's performance.
What experiment are you currently running?
Stop autopilot.
Resume autopilot.
```

## Telegram command interpreter

Natural language → intent parser → validated action.

Possible intents:

``` text
QUERY_STATUS
QUERY_PERFORMANCE
QUERY_LEARNINGS
QUERY_RESEARCH
CREATE_TOPIC
CREATE_POST
SCHEDULE_POST
RESCHEDULE_POST
CANCEL_POST
PAUSE_PLATFORM
RESUME_PLATFORM
PAUSE_AUTOPILOT
RESUME_AUTOPILOT
APPROVE_POST
REJECT_POST
REVISE_POST
REVISE_ASSET
CHANGE_FORMAT
FORCE_RESEARCH
FORCE_ANALYSIS
EMERGENCY_STOP
```

## Confirmation policy

Require confirmation for destructive/high-impact actions such as: - bulk
cancellation; - deleting historical data; - enabling full autopilot; -
publishing immediately outside schedule; - changing brand rules; -
changing credentials; - enabling paid services.

------------------------------------------------------------------------

# 22. Approval Mode

Start production in:

``` text
APPROVAL_MODE=REQUIRED
```

Telegram card/message:

``` text
CONTENT READY

Topic:
Why AI Agents Fail in Production

Platforms:
LinkedIn / Instagram / X

LinkedIn:
7-slide carousel

Instagram:
7-slide carousel

X:
Single post

Scheduled:
10:00 AM IST

Quality:
94/100

Research confidence:
96/100

[APPROVE]
[REVISE]
[RESCHEDULE]
[REJECT]
```

Natural-language replies must also work.

After 20--30 successful controlled posts, the user may selectively
enable autopilot.

Example:

``` text
LinkedIn = approval required
Instagram = approval required
X = autopilot
```

Never enable this automatically.

------------------------------------------------------------------------

# 23. Performance Collection

Capture metrics at configurable windows:

``` text
2 hours
24 hours
72 hours
7 days (optional)
```

Do not assume every platform exposes every metric.

Normalize carefully.

Do not compare raw LinkedIn impressions directly with Instagram reach as
though they are identical metrics.

Store raw metrics plus normalized platform-specific scores.

------------------------------------------------------------------------

# 24. Performance Model

Evaluate more than likes.

Potential dimensions:

``` text
Reach efficiency
Engagement quality
Save rate
Share rate
Meaningful comment rate
Click rate
Follower conversion
Profile-action rate
Brand quality
Content quality
```

Use medians/baselines rather than blindly comparing to the single best
viral post.

Compare a post to: - its platform; - its format; - similar topic
category; - account size/time period; - historical median; - experiment
cohort.

------------------------------------------------------------------------

# 25. Self-Learning Engine

The agent must not say:

> "This hook worked because the post got views."

Correlation is not proof.

Learning lifecycle:

``` text
Observation
  ↓
Hypothesis
  ↓
Controlled experiment
  ↓
Minimum sample threshold
  ↓
Analysis
  ↓
Confidence estimate
  ↓
Provisional rule
  ↓
Repeated validation
  ↓
Confirmed strategy rule
```

Example:

``` text
Observation:
Short hooks appear stronger.

Hypothesis:
5–8 word LinkedIn carousel hooks increase 24h impressions.

Experiment:
Short vs long hooks across comparable posts.

Sample:
18 posts.

Result:
Median +27%.

Confidence:
High.

Rule:
Prefer 5–8 word hooks for this content family.

Status:
CONFIRMED
```

------------------------------------------------------------------------

# 26. Experiment Engine

Only test a small number of variables at once.

Possible variables: - hook length; - hook type; - carousel vs image; -
slide count; - posting time; - CTA; - caption length; - visual family; -
technical vs narrative angle; - news vs opinion; - question vs
statement; - first-slide density.

Avoid changing five variables and pretending we learned which one
mattered.

The experiment engine should automatically prevent overlapping
experiments that make attribution useless.

------------------------------------------------------------------------

# 27. Algorithm / Platform Intelligence Diary

Create:

``` text
01-Platform-Intelligence/
├── LinkedIn.md
├── Instagram.md
└── X.md
```

Every strategy claim should contain:

``` text
Claim
Platform
Source
Source date
Discovered date
External confidence
Evidence from our account
Sample size
Last tested
Current status
```

Statuses:

``` text
EXTERNAL_ONLY
TESTING
SUPPORTED_BY_OUR_DATA
CONTRADICTED_BY_OUR_DATA
STALE
```

Our own account evidence should eventually outweigh generic internet
advice when the comparison is valid.

------------------------------------------------------------------------

# 28. Competitor / Creator Intelligence

Maintain an approved watchlist.

Purpose is **not copying**.

Analyze: - emerging topics; - recurring audience questions; - content
saturation; - format patterns; - discussion intensity; - unexplained
concepts; - audience objections; - content gaps.

The desired output:

``` text
Trending subject
+
Audience demand
+
Competitor coverage
-
Already-solved information
=
Content gap
```

------------------------------------------------------------------------

# 29. Duplicate & Repetition Prevention

Create semantic/history checks before publishing.

Check: - same topic recently posted; - same hook structure; - same core
thesis; - same carousel sequence; - repeated CTA; - repeated visual
family too frequently; - repeated generated image; - near-duplicate
platform copy.

The system should intentionally rotate formats without breaking brand
consistency.

------------------------------------------------------------------------

# 30. Safety & Reliability Controls

Implement:

## Global kill switch

``` text
AUTOPILOT_ENABLED=false
PUBLISHING_ENABLED=false
```

## Per-platform switches

``` text
LINKEDIN_ENABLED=
INSTAGRAM_ENABLED=
X_ENABLED=
```

## Cost guard

``` text
ALLOW_PAID_APIS=false
```

Any integration that reports a required paid operation must stop.

## Rate limits

Implement local rate limiting even when provider limits are higher.

## Idempotency

Every publish/schedule action gets an idempotency key.

## Locks

Prevent two cron runs from generating/publishing the same day's content
concurrently.

## Backups

Daily SQLite backup with retention.

## Audit log

Every publish, cancel, approval, strategy change, and Telegram command
should be traceable.

------------------------------------------------------------------------

# 31. Repository Structure

Claude should refine names but preserve separation of concerns.

``` text
hermes-social-agent/
├── README.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── config/
│   ├── default.yaml
│   ├── quality.yaml
│   ├── platforms.yaml
│   └── experiments.yaml
├── data/
│   ├── social.db
│   ├── backups/
│   └── assets/
├── docs/
│   ├── Hermes_Social_Agent_Guide.md
│   ├── architecture.md
│   ├── deployment.md
│   ├── telegram.md
│   └── platform-integrations.md
├── migrations/
├── src/
│   └── social_agent/
│       ├── config/
│       ├── db/
│       ├── models/
│       ├── supervisor/
│       ├── trends/
│       ├── research/
│       ├── content/
│       ├── brand/
│       ├── creative/
│       ├── publishing/
│       ├── analytics/
│       ├── experiments/
│       ├── learning/
│       ├── telegram/
│       ├── sheets/
│       ├── obsidian/
│       ├── scheduling/
│       ├── providers/
│       └── utils/
├── scripts/
│   ├── init_db.py
│   ├── verify_install.py
│   ├── backup_db.py
│   ├── sync_sheets.py
│   ├── collect_metrics.py
│   └── full_verify.py
├── hermes/
│   └── skills/
│       └── social-agent/
│           ├── SKILL.md
│           └── references/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── e2e/
└── obsidian-template/
```

------------------------------------------------------------------------

# 32. Hermes Skill Design

Create a primary:

``` text
social-agent
```

Do not create dozens of independent skills unless Hermes architecture
benefits from it.

The primary skill may internally expose capabilities such as:

``` text
trend-hunter
topic-scorer
deep-researcher
fact-checker
content-strategist
brand-brain
human-writer
content-critic
creative-director
carousel-architect
asset-qa
linkedin-adapter
instagram-adapter
x-adapter
metrics-collector
performance-analyzer
experiment-manager
strategy-optimizer
telegram-controller
```

The production skill should point to deterministic scripts/services
rather than trying to encode the whole system in one giant prompt.

------------------------------------------------------------------------

# 33. Cron / Background Jobs

Do not create a separate process manager merely because it is familiar
if Hermes gateway/cron already handles the required scheduling reliably.

Suggested logical jobs:

``` text
Morning trend discovery
Daily content planning
Scheduled publishing check
2h metric collection
24h metric collection
72h metric collection
Daily performance summary
Weekly experiment review
Weekly strategy review
Monthly deep review
Daily backup
Health check
```

Actual cron times should be configured after the user's posting timezone
and desired schedule are confirmed.

Never hard-code UTC assumptions.

------------------------------------------------------------------------

# 34. Google Sheets Sync Rules

SQLite remains source of truth.

Sheets synchronization should be one-way by default:

``` text
SQLite → Sheets
```

If editable control fields are later supported in Sheets, explicitly
whitelist columns such as:

``` text
user_priority
user_note
manual_schedule
approval_override
```

Never allow arbitrary spreadsheet edits to mutate critical database
state.

------------------------------------------------------------------------

# 35. Obsidian Sync Rules

Obsidian contains derived knowledge, not credentials.

Never write: - API keys; - OAuth tokens; - session cookies; - private
credentials.

Updates should be atomic where possible.

Keep a decision log so the user can see when/why a strategy document
changed.

------------------------------------------------------------------------

# 36. Cost Architecture

Target:

  -----------------------------------------------------------------------
  Component                           Plan
  ----------------------------------- -----------------------------------
  Hermes                              Existing

  EC2                                 Existing/free-tier assumption;
                                      monitor billing

  Primary/fallback LLMs               Existing free routes

  SQLite                              Free

  Python                              Free

  Pillow                              Free

  ImageMagick                         Free

  Obsidian local                      Free

  Google Sheets                       Free within account quotas

  Telegram                            Free for this use

  NotebookLM                          Existing/free availability

  Image generation                    Existing subscriptions/manual or
                                      supported no-extra-cost route

  Social APIs                         Must be verified before
                                      implementation
  -----------------------------------------------------------------------

**Do not claim social publishing is permanently free.**

Build the platform adapters so a pricing/permission change does not
break the rest of the agent.

------------------------------------------------------------------------

# 37. Secrets

`.env.example` contains placeholders only.

Potential categories:

``` text
APP_ENV=
APPROVAL_MODE=
AUTOPILOT_ENABLED=
PUBLISHING_ENABLED=
ALLOW_PAID_APIS=

DATABASE_PATH=
TIMEZONE=

GOOGLE_SHEETS_...
TELEGRAM_...

LINKEDIN_...
INSTAGRAM_...
X_...

OBSIDIAN_VAULT_PATH=
ASSET_PATH=
```

Do not commit: - `.env`; - OAuth credential files; - tokens; -
cookies; - private keys; - generated auth sessions.

If a secret is ever pushed to a remote repository, rotate/revoke it.

------------------------------------------------------------------------

# 38. Build Phases --- 0 to 100

## Phase 0 --- Freeze Requirements

**Use:** Gemini 3.1 Pro

### AI does

Give Gemini: - this guide; - existing Hermes paid blueprint; - existing
Sales Agent architecture summary; - screenshot/text of model fallback
chain.

Ask Gemini to produce only: - contradictions; - missing requirements; -
overengineering risks; - impossible assumptions; - platform/API items
requiring current verification; - security concerns; - recommended
changes.

### User does

Approve/reject changes.

### Exit gate

A final requirements document exists.

------------------------------------------------------------------------

## Phase 1 --- Repository Scaffold

**Use:** Claude Opus 4.6

### AI does

-   create repository;
-   folder structure;
-   configuration loader;
-   logging;
-   `.env.example`;
-   `.gitignore`;
-   package configuration;
-   base test setup;
-   CLI entry point.

### User does

Review folder structure only.

### Exit gate

``` text
tests run
config loads
no secrets committed
```

------------------------------------------------------------------------

## Phase 2 --- Database & State Machine

**Use:** Claude Opus 4.6\
**Audit:** Gemini 3.1 Pro

### AI does

-   schema;
-   migrations;
-   repositories;
-   transactions;
-   statuses;
-   idempotency;
-   audit events;
-   backup/restore;
-   test fixtures.

### Gemini checks

-   broken transitions;
-   duplicate publish paths;
-   race conditions;
-   data loss;
-   null metric handling;
-   migration safety.

### Exit gate

Full DB test suite passes.

------------------------------------------------------------------------

## Phase 3 --- Brand Brain

**Use:** Gemini 3.1 Pro for brand-system design\
**Use:** Claude Opus 4.6 for implementation

### User does

Provide: - Prathvi Sharma; - logo; - brand colors if existing - find one pinterests; - desired
perception from pinterest; - audience - GenZ, Professioal, others; - content examples - AI, Web development, Gen AI, Automations, Agentic AI, Designing, Web Design, Frontend Development, Full stack development, Gen AI Development; - visual examples - Creative, Vinrant, professnoil, Modern; -
disliked examples; - content pillars.

### AI does

Create: - brand schema; - brand Markdown files; - brand validation; -
writing rules; - visual families; - brand score.

### Exit gate

User approves a brand-system document before content generation.

------------------------------------------------------------------------

## Phase 4 --- Trend Discovery

**Use:** Claude Opus 4.6

Build: - source adapters; - normalization; - dedupe; - freshness; -
opportunity scoring; - content-gap analysis; - topic queue.

### Gemini audit

Check: - source bias; - score logic; - recency handling; -
spam/manipulated trends; - duplicate detection.

### Exit gate

Run in read-only mode for several cycles and inspect candidates.

------------------------------------------------------------------------

## Phase 5 --- Research + Fact Checking

**Use:** Claude Opus 4.6\
**Audit:** Gemini 3.1 Pro

Build: - research runner; - source provenance; - claims; - claim/source
mapping; - contradiction detection; - confidence; - knowledge pack.

### User does

Inspect at least 10 research packs.

### Exit gate

No fabricated sources in test corpus.

------------------------------------------------------------------------

## Phase 6 --- Content Strategy + Writing

**Use:** Claude Opus 4.6 for implementation\
**Use:** Gemini 3.1 Pro to stress-test prompts/rubrics

Build: - format decision; - master narrative; - LinkedIn adapter; -
Instagram adapter; - X adapter; - content council; - Editor-in-Chief; -
revision loop; - duplicate-content checks.

### Exit gate

Generate 20 offline drafts without publishing.

User rates them.

------------------------------------------------------------------------

## Phase 7 --- Creative System

**Use:** Gemini 3.1 Pro for visual-system critique\
**Use:** Claude Opus 4.6 for renderer/code

Build: - creative brief; - inspiration record; - design families; -
carousel schema; - Pillow/ImageMagick renderer; - image-provider
abstraction; - asset QA; - exports.

### User does

Approve templates/design families.

### Exit gate

Generate sample carousels for multiple topics and verify consistency.

------------------------------------------------------------------------

## Phase 8 --- Google Sheets

**Use:** Claude Opus 4.6

Build: - workbook initializer or setup instructions; - tabs; -
formatting; - SQLite→Sheets sync; - sync error handling; - last-sync
indicators.

### User does

Authorize Google account/OAuth where required.

### Exit gate

Sheet accurately reflects local database state.

------------------------------------------------------------------------

## Phase 9 --- Obsidian

**Use:** Claude Opus 4.6

Build: - vault template; - Markdown writers; - strategy-rule pages; -
experiment pages; - monthly review; - decision log.

### User does

Open vault locally and confirm readability.

### Exit gate

Strategy updates appear correctly without secrets.

------------------------------------------------------------------------

## Phase 10 --- Telegram Command Center

**Use:** Claude Opus 4.6\
**Audit:** Gemini 3.1 Pro

Build: - natural-language intents; - read queries; - schedule
commands; - approvals; - revisions; - pause/resume; - emergency stop; -
confirmations; - command audit log.

### Test

At minimum test every example command in Section 21.

### Exit gate

User can control the entire non-publishing workflow from Telegram.

------------------------------------------------------------------------

## Phase 11 --- Publishing Adapters

**First use:** Gemini 3.1 Pro to research/audit current official
platform requirements.\
**Then:** Claude Opus 4.6 implements only verified paths.

### User does

-   create developer apps where necessary;
-   authorize accounts;
-   provide credentials on EC2;
-   approve permissions.

### AI does

-   adapter implementation;
-   validation;
-   dry run;
-   idempotency;
-   publish verification;
-   manual fallback.

### Exit gate

Each platform successfully publishes a controlled test post or correctly
falls back to manual publishing.

------------------------------------------------------------------------

## Phase 12 --- Metrics

**Use:** Claude Opus 4.6

Build: - raw metric collectors; - snapshot windows; - normalization; -
baselines; - Sheets dashboards; - Telegram summaries.

### Exit gate

Metrics from controlled posts are captured correctly.

------------------------------------------------------------------------

## Phase 13 --- Experiment Engine

**Use:** Gemini 3.1 Pro to review methodology\
**Use:** Claude Opus 4.6 to implement

Build: - hypothesis lifecycle; - variant assignment; - sample
minimums; - overlap prevention; - analysis; - confidence; - strategy
promotion.

### Exit gate

Run simulated historical tests before allowing real strategy updates.

------------------------------------------------------------------------

## Phase 14 --- Self-Learning

**Use:** Claude Opus 4.6\
**Audit:** Gemini 3.1 Pro

Build: - observation generator; - hypothesis generator; - strategy
rules; - Obsidian updates; - confidence decay; - stale-rule
revalidation; - rollback/retire rule.

### Exit gate

Agent cannot promote a rule based on one post.

------------------------------------------------------------------------

## Phase 15 --- Full Local/Dev Verification

**Use:** Claude Opus 4.6 to create `full_verify.py`.

Test:

``` text
configuration
database
migrations
topic ingestion
dedupe
opportunity scoring
research
fact provenance
content generation
brand checks
creative rendering
asset validation
Sheets sync
Obsidian sync
Telegram queries
Telegram mutations
approval
scheduling
idempotency
manual publisher
mock platform publishers
metrics
experiments
learning
backup
restore
kill switch
```

------------------------------------------------------------------------

## Phase 16 --- Independent Final Audit

**Use:** Gemini 3.1 Pro

Give Gemini: - complete repository; - this guide; - test output; -
architecture docs.

Ask it to audit:

``` text
requirements coverage
security
secrets
state machine
concurrency
idempotency
duplicate posting
API assumptions
cost risks
brand consistency
hallucination risk
source provenance
Telegram permissions
scheduler
metrics correctness
experiment methodology
self-learning overfitting
backup/restore
failure recovery
test coverage
```

Claude fixes every accepted issue.

Repeat until clean.

------------------------------------------------------------------------

## Phase 17 --- Git & Deployment Preparation

**Use:** Claude Opus 4.6

Ensure:

``` text
.env ignored
credentials ignored
tokens ignored
database ignored if appropriate
generated assets ignored or intentionally stored
tests green
README complete
deployment guide complete
```

User creates/uses private Git repository.

------------------------------------------------------------------------

## Phase 18 --- EC2 Deployment

The existing Hermes installation should be reused.

Do not reinstall Hermes unnecessarily.

Suggested location:

``` text
~/apps/hermes-social-agent
```

Create a dedicated Python virtual environment.

Install only project dependencies.

Create production `.env` directly on EC2.

Protect secrets.

Initialize DB.

Install/copy the Hermes social-agent skill.

Verify Hermes gateway.

------------------------------------------------------------------------

## Phase 19 --- Production DRAFT Mode

Start:

``` text
PUBLISHING_ENABLED=false
APPROVAL_MODE=REQUIRED
AUTOPILOT_ENABLED=false
```

Run the complete pipeline for several days:

``` text
discover
research
write
design
schedule draft
Telegram approval simulation
Sheets
Obsidian
analytics simulation
```

No real posts.

------------------------------------------------------------------------

## Phase 20 --- Controlled Publishing

Publish to the user's own accounts under supervision.

Order:

1.  one LinkedIn test;
2.  verify;
3.  one Instagram test;
4.  verify;
5.  one X test if supported;
6.  verify;
7.  metrics collection;
8.  deletion/cancel behavior where applicable;
9.  Telegram reporting.

------------------------------------------------------------------------

## Phase 21 --- 20--30 Post Learning Period

Keep:

``` text
APPROVAL_MODE=REQUIRED
```

The user reviews every post.

The agent learns but does not gain new publishing authority.

Review weekly: - quality; - brand consistency; - source accuracy; -
performance; - failed hypotheses; - visual consistency; - user
revisions.

------------------------------------------------------------------------

## Phase 22 --- Selective Autopilot

Only the user can enable.

Possible:

``` text
LinkedIn: REQUIRED
Instagram: REQUIRED
X: AUTO
```

or keep all approval-required indefinitely.

Autopilot is not a success requirement.

------------------------------------------------------------------------

# 39. Testing Requirements

## Unit tests

Cover: - scoring; - dedupe; - state transitions; - quality thresholds; -
schedule parsing; - metric normalization; - experiment assignment; -
strategy promotion; - brand validation.

## Integration tests

Cover: - DB; - Sheets; - Obsidian; - Telegram; - model abstraction; -
platform mocks; - asset pipeline.

## E2E tests

Simulate:

``` text
trend
→ research
→ post
→ approval
→ schedule
→ publish
→ metrics
→ experiment
→ learning
```

## Failure tests

Explicitly test: - LLM unavailable; - all fallbacks unavailable; -
malformed LLM output; - research source unavailable; - duplicate
topic; - bad image; - Sheets unavailable; - Obsidian path unavailable; -
Telegram unavailable; - publisher timeout; - publisher returns ambiguous
result; - EC2 reboot during publish; - cron fires twice; - metrics
unavailable; - user cancels while content is generating; - user
overrides schedule; - database locked; - disk full/low; - paid API
required.

------------------------------------------------------------------------

# 40. Observability

Logs must be structured.

Track: - pipeline run ID; - topic ID; - post ID; - model route; -
stage; - duration; - retry; - result; - error.

Telegram should alert only on meaningful failures, not spam every
internal retry.

Daily health summary:

``` text
Agent health
Pipeline runs
Posts prepared
Posts published
Failures
Pending approvals
Next scheduled post
Model fallback events
Sheets sync
Backup status
```

------------------------------------------------------------------------

# 41. Daily Operating Flow

Example:

``` text
06:00
Trend scan

06:15
Opportunity scoring

06:30
Research top candidates

07:00
Select one best idea

07:10
Master content

07:20
Platform adaptations

07:30
Creative direction

07:45
Assets

08:00
Quality council

08:15
Telegram approval package

User approves/revises

Configured posting time
Publish

+2h
Snapshot

+24h
Snapshot

+72h
Final main snapshot

Night
Performance analysis

Weekly
Experiment review

Monthly
Deep strategy review
```

These times are examples only. Configure after the user chooses the
actual schedule/timezone.

------------------------------------------------------------------------

# 42. Daily Telegram Report

Example:

``` text
HERMES SOCIAL — DAILY

Today's topic:
Why AI Agents Fail in Production

Format:
LinkedIn carousel
Instagram carousel
X post

Status:
Published

Research:
8 sources
Confidence 96%

24h performance:
LinkedIn: ...
Instagram: ...
X: ...

Current experiment:
Short vs long carousel hooks

Observation:
Short hooks are currently ahead, but sample size is not sufficient.

Tomorrow:
3 candidate topics found.
Top candidate: ...

Pending:
1 approval
```

------------------------------------------------------------------------

# 43. Monthly Review

Generate:

``` text
Top posts
Worst posts
Best topics
Worst topics
Format performance
Visual-family performance
Hook performance
Posting-time performance
Follower growth
Share/save behavior
Meaningful comments
Experiments completed
Confirmed learnings
Rejected hypotheses
Stale rules
Brand-consistency score
Research-quality incidents
Publishing failures
Recommendations for next month
```

Write it to: - SQLite; - Google Sheets summary; - Obsidian monthly
review; - Telegram summary.

------------------------------------------------------------------------

# 44. What NOT to Build

Do not: - add five databases; - add Kubernetes; - add Redis unless
measured need appears; - add a vector database merely because it sounds
"AI"; - add another process manager without need; - add more LLM
providers without evidence; - use browser hacks as the primary
publishing architecture; - depend on NotebookLM for production
availability; - treat Google Sheets as the database; - let the agent
rewrite its own production code; - optimize purely for likes/views; -
post every trend; - copy competitor designs; - generate fake stories; -
silently use paid APIs.

------------------------------------------------------------------------

# 45. Definition of Done

The system is complete when:

-   Hermes runs it 24/7;
-   one high-quality idea/day can be produced;
-   trend discovery is multi-source;
-   research has provenance;
-   important claims are checked;
-   content maps to approved pillars;
-   brand rules are enforced;
-   platform-specific content is produced;
-   carousels/assets are consistently branded;
-   user can control everything important from Telegram;
-   schedules are visible in Google Sheets;
-   knowledge/strategy is readable in Obsidian;
-   SQLite holds authoritative state;
-   publishing is idempotent;
-   platform failures have safe fallbacks;
-   no paid service is silently invoked;
-   metrics are collected where available;
-   experiments are controlled;
-   one post cannot create a "confirmed" strategy rule;
-   learnings are auditable;
-   user can pause/kill publishing immediately;
-   backups work;
-   tests pass;
-   Gemini has independently audited the final implementation;
-   first 20--30 production posts are run in approval mode.

------------------------------------------------------------------------

# 46. First Prompt to Give Gemini 3.1 Pro

Use this **before coding**:

``` text
You are the independent principal architect and adversarial reviewer for the Hermes Social Agent project.

Read Hermes_Social_Agent_Guide.md completely.

Do NOT start coding.

Audit the blueprint for:
1. missing requirements,
2. architectural contradictions,
3. unnecessary complexity,
4. security/privacy problems,
5. concurrency and idempotency problems,
6. social-platform API assumptions that require current official verification,
7. hidden paid-cost risks,
8. Google Sheets/Obsidian/NotebookLM integration risks,
9. Telegram-control risks,
10. research/fact-checking weaknesses,
11. brand-consistency weaknesses,
12. analytics mistakes,
13. experiment-design mistakes,
14. self-learning/overfitting risks,
15. deployment/recovery weaknesses,
16. anything that could cause duplicate or incorrect publishing.

Separate your response into:
CRITICAL
HIGH
MEDIUM
LOW
RECOMMENDED CHANGES
QUESTIONS REQUIRING USER DECISION

Do not rewrite the entire guide.
Do not invent platform capabilities.
For current platform/API claims, verify against official documentation before recommending implementation.
```

------------------------------------------------------------------------

# 47. First Prompt to Give Claude Opus 4.6

Use only after Gemini's architecture audit has been reviewed and
accepted changes have been incorporated:

``` text
You are the lead implementation engineer for Hermes Social Agent.

Read these completely before writing code:
1. Hermes_Social_Agent_Guide.md
2. the final Gemini architecture audit
3. existing Hermes deployment documentation supplied in /docs

Do not attempt to build the entire project in one uncontrolled pass.

First:
1. produce an implementation plan mapped to the guide's phases;
2. identify external credentials/account actions that the USER must perform;
3. identify all assumptions that still require verification;
4. propose the final repository tree;
5. propose the database schema/migration plan;
6. propose the state machine;
7. propose the test strategy.

Do not request or hard-code real secrets.

After I approve the implementation plan, implement phase-by-phase.

For every phase:
- implement,
- add/update tests,
- run tests,
- report files changed,
- report assumptions,
- report anything the user must do,
- stop at the phase exit gate.

Non-negotiable:
- SQLite is authoritative machine state.
- Google Sheets is the human operations dashboard.
- Obsidian is human-readable strategy/knowledge.
- NotebookLM is supplementary, not a production dependency.
- Telegram is the remote-control interface.
- User commands override autonomous scheduling.
- No paid API may be enabled silently.
- No fake personal experiences.
- No unsupported factual claims.
- No duplicate publishing.
- All publish actions must be idempotent.
- Autopilot remains disabled until explicitly enabled by the user.
- Current platform API capabilities/pricing/permissions must be verified before implementation.
```

------------------------------------------------------------------------

# 48. Final Development Discipline

For every major phase:

``` text
Claude builds
    ↓
tests
    ↓
Gemini audits
    ↓
Claude fixes
    ↓
tests again
    ↓
commit
```

Do not jump directly from a successful code generation to production.

The Social Agent should earn autonomy gradually through evidence.

**The goal is not maximum automation. The goal is maximum useful
autonomy with the user retaining complete control.**
