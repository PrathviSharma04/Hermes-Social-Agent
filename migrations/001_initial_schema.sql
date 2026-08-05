-- Migration 001: Initial Schema for Hermes Social Agent
-- Creates 17 normalized tables covering all domain entities per Section 8 & 30 of the guide.

PRAGMA foreign_keys = ON;

-- 1. topics
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_topic TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    content_pillar TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trend_started_at TIMESTAMP,
    trend_velocity REAL DEFAULT 0.0,
    audience_relevance REAL DEFAULT 0.0,
    saturation_score REAL DEFAULT 0.0,
    unique_angle_score REAL DEFAULT 0.0,
    visual_potential REAL DEFAULT 0.0,
    source_authority REAL DEFAULT 0.0,
    opportunity_score REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
CREATE INDEX IF NOT EXISTS idx_topics_opportunity ON topics(opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_topics_pillar ON topics(content_pillar);

-- 2. topic_sources
CREATE TABLE IF NOT EXISTS topic_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    url TEXT,
    published_at TIMESTAMP,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    authority_score REAL DEFAULT 0.0,
    raw_excerpt_hash TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_topic_sources_topic ON topic_sources(topic_id);

-- 3. research_runs
CREATE TABLE IF NOT EXISTS research_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    model_route TEXT,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    confidence REAL DEFAULT 0.0,
    research_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_runs_topic ON research_runs(topic_id);
CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs(status);

-- 4. research_claims
CREATE TABLE IF NOT EXISTS research_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_run_id INTEGER NOT NULL,
    claim TEXT NOT NULL,
    claim_type TEXT NOT NULL DEFAULT 'FACT',
    confidence REAL DEFAULT 0.0,
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    contradiction_status TEXT,
    source_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(research_run_id) REFERENCES research_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_research_claims_run ON research_claims(research_run_id);
CREATE INDEX IF NOT EXISTS idx_research_claims_status ON research_claims(verification_status);

-- 5. claim_sources (mapping table)
CREATE TABLE IF NOT EXISTS claim_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(claim_id) REFERENCES research_claims(id) ON DELETE CASCADE,
    FOREIGN KEY(source_id) REFERENCES topic_sources(id) ON DELETE CASCADE,
    UNIQUE(claim_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_claim_sources_claim ON claim_sources(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_sources_source ON claim_sources(source_id);

-- 6. content_ideas
CREATE TABLE IF NOT EXISTS content_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL,
    angle TEXT NOT NULL,
    audience_problem TEXT,
    core_value TEXT,
    format_recommendation TEXT,
    originality_score REAL DEFAULT 0.0,
    brand_fit_score REAL DEFAULT 0.0,
    information_value_score REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_content_ideas_topic ON content_ideas(topic_id);
CREATE INDEX IF NOT EXISTS idx_content_ideas_status ON content_ideas(status);

-- 7. posts (with UNIQUE idempotency_key per Section 30)
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_idea_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    format TEXT NOT NULL,
    master_post_id INTEGER,
    version INTEGER DEFAULT 1,
    hook TEXT,
    body TEXT NOT NULL,
    cta TEXT,
    hashtags TEXT,
    word_count INTEGER DEFAULT 0,
    slide_count INTEGER DEFAULT 0,
    brand_score REAL DEFAULT 0.0,
    quality_score REAL DEFAULT 0.0,
    approval_status TEXT NOT NULL DEFAULT 'REQUIRED',
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    platform_post_id TEXT,
    platform_url TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(content_idea_id) REFERENCES content_ideas(id) ON DELETE CASCADE,
    FOREIGN KEY(master_post_id) REFERENCES posts(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_idea ON posts(content_idea_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
CREATE INDEX IF NOT EXISTS idx_posts_scheduled_at ON posts(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_posts_idempotency ON posts(idempotency_key);

-- 8. assets
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    asset_type TEXT NOT NULL,
    path TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    checksum TEXT,
    generation_method TEXT,
    prompt_reference TEXT,
    design_system TEXT,
    qa_status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_assets_post ON assets(post_id);
CREATE INDEX IF NOT EXISTS idx_assets_qa ON assets(qa_status);

-- 9. performance_snapshots (nullable metrics per Section 8 & 23)
CREATE TABLE IF NOT EXISTS performance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    window TEXT NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    impressions INTEGER,
    reach INTEGER,
    likes INTEGER,
    comments INTEGER,
    shares INTEGER,
    saves INTEGER,
    clicks INTEGER,
    profile_visits INTEGER,
    follows INTEGER,
    reposts INTEGER,
    other_metrics_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    UNIQUE(post_id, window)
);

CREATE INDEX IF NOT EXISTS idx_performance_post ON performance_snapshots(post_id);
CREATE INDEX IF NOT EXISTS idx_performance_window ON performance_snapshots(window);

-- 10. experiments
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    platform TEXT,
    variable TEXT NOT NULL,
    variant_a TEXT NOT NULL,
    variant_b TEXT NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    minimum_samples INTEGER DEFAULT 10,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    confidence REAL DEFAULT 0.0,
    conclusion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_platform ON experiments(platform);

-- 11. post_experiment_assignments
CREATE TABLE IF NOT EXISTS post_experiment_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    experiment_id INTEGER NOT NULL,
    variant TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE,
    UNIQUE(post_id, experiment_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_post ON post_experiment_assignments(post_id);
CREATE INDEX IF NOT EXISTS idx_assignments_experiment ON post_experiment_assignments(experiment_id);

-- 12. strategy_rules
CREATE TABLE IF NOT EXISTS strategy_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    rule TEXT NOT NULL,
    evidence_summary TEXT,
    sample_size INTEGER DEFAULT 0,
    confidence REAL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'HYPOTHESIS',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategy_rules_platform ON strategy_rules(platform);
CREATE INDEX IF NOT EXISTS idx_strategy_rules_status ON strategy_rules(status);

-- 13. brand_rules
CREATE TABLE IF NOT EXISTS brand_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_brand_rules_active ON brand_rules(is_active);

-- 14. scheduled_actions
CREATE TABLE IF NOT EXISTS scheduled_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    idempotency_key TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scheduled_actions_time ON scheduled_actions(scheduled_for);
CREATE INDEX IF NOT EXISTS idx_scheduled_actions_status ON scheduled_actions(status);

-- 15. telegram_commands
CREATE TABLE IF NOT EXISTS telegram_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_intent TEXT,
    result_action TEXT,
    result_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telegram_commands_chat ON telegram_commands(chat_id);
CREATE INDEX IF NOT EXISTS idx_telegram_commands_time ON telegram_commands(created_at);

-- 16. model_runs
CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    model_route TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    success BOOLEAN NOT NULL DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    quality_score REAL,
    tokens_used INTEGER,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_runs_task ON model_runs(task_type);
CREATE INDEX IF NOT EXISTS idx_model_runs_success ON model_runs(success);
CREATE INDEX IF NOT EXISTS idx_model_runs_time ON model_runs(created_at);

-- 17. system_events
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL DEFAULT 'INFO',
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_events_level ON system_events(level);
CREATE INDEX IF NOT EXISTS idx_system_events_category ON system_events(category);
CREATE INDEX IF NOT EXISTS idx_system_events_time ON system_events(created_at);
