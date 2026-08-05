"""Command-line interface entry point for Hermes Social Agent."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from hermes_social import __version__
from hermes_social.config import load_config, AppConfig
from hermes_social.db.backup import backup_database
from hermes_social.db.connection import get_connection, init_db
from hermes_social.db.migrations import get_current_version
from hermes_social.logging_setup import setup_logging
from hermes_social.services.brand import load_brand_system
from hermes_social.trends.config import load_sources_config
from hermes_social.trends.pipeline import run_discovery_cycle
from hermes_social.research.pipeline import run_research_for_topic
from hermes_social.generation.pipeline import generate_content_for_topic
from hermes_social.constants import TopicStatus


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hermes-social",
        description="Hermes Social Agent — 24/7 Quality-First Social Content Intelligence Agent",
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Path to custom .env file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Override log level (DEBUG, INFO, WARNING, ERROR)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Start the Hermes Social Agent")
    run_parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single pipeline iteration and exit (useful for cron/dev)",
    )

    # 'config' subcommand
    subparsers.add_parser(
        "config", help="Validate and inspect current application configuration"
    )
    
    # 'telegram' subcommand
    telegram_parser = subparsers.add_parser("telegram", help="Manage the Telegram Command Center")
    telegram_subparsers = telegram_parser.add_subparsers(dest="telegram_action", help="Telegram actions")
    telegram_subparsers.add_parser("start", help="Start the Telegram bot in long-polling mode")
    telegram_subparsers.add_parser("test", help="Send a test message to the configured chat_id")

    # 'publish' subcommand
    publish_parser = subparsers.add_parser("publish", help="Manage publishing")
    publish_parser.add_argument("post_id", type=int, nargs="?", help="ID of the post to publish")
    publish_parser.add_argument("--check", action="store_true", help="Check credentials for all platforms")
    publish_parser.add_argument("--dry-run", action="store_true", help="Prepare payload without publishing")

    # 'metrics' subcommand
    metrics_parser = subparsers.add_parser("metrics", help="Manage performance metrics")
    metrics_subparsers = metrics_parser.add_subparsers(dest="metrics_action", help="Metrics actions")
    metrics_subparsers.add_parser("collect", help="Run the snapshot pipeline to fetch missing metrics")
    metrics_subparsers.add_parser("analyze", help="Calculate and display current platform/format baselines")
    
    # 'experiments' subcommand
    exp_parser = subparsers.add_parser("experiments", help="Manage experiments")
    exp_subparsers = exp_parser.add_subparsers(dest="exp_action", help="Experiment actions")
    exp_subparsers.add_parser("evaluate", help="Evaluate all active experiments")
    exp_subparsers.add_parser("simulate", help="Run the simulated historical test")
    
    # 'learning' subcommand
    learning_parser = subparsers.add_parser("learning", help="Manage self-learning engine")
    learning_subparsers = learning_parser.add_subparsers(dest="learning_action", help="Learning actions")
    learning_subparsers.add_parser("cycle", help="Run observe -> hypothesize -> decay cycle")
    learning_subparsers.add_parser("sync", help="Sync strategy rules to Obsidian vault")

    # 'version' subcommand
    subparsers.add_parser("version", help="Print package version")

    # 'db' subcommand
    db_parser = subparsers.add_parser("db", help="Database management commands")
    db_parser.add_argument(
        "action",
        choices=["init", "backup"],
        help="Database action to perform (init, backup)",
    )

    # 'brand' subcommand
    subparsers.add_parser("brand", help="Validate and inspect current brand configuration")

    # 'discover' subcommand
    discover_parser = subparsers.add_parser("discover", help="Run a trend discovery cycle (Phase 4)")
    discover_parser.add_argument(
        "--commit",
        action="store_true",
        help="Write accepted topics to the database (default is dry-run read-only)",
    )

    # 'research' subcommand
    research_parser = subparsers.add_parser("research", help="Run the research engine (Phase 5)")
    research_group = research_parser.add_mutually_exclusive_group(required=True)
    research_group.add_argument("topic_id", type=int, nargs="?", help="Topic ID to research")
    research_group.add_argument("--all", action="store_true", help="Research all pending topics")
    research_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving to DB or Obsidian",
    )

    # 'generate' subcommand
    generate_parser = subparsers.add_parser("generate", help="Run the content generation engine (Phase 6)")
    generate_group = generate_parser.add_mutually_exclusive_group(required=True)
    generate_group.add_argument("topic_id", type=int, nargs="?", help="Topic ID to generate content for")
    generate_group.add_argument("--all", action="store_true", help="Generate content for all researched topics")
    generate_parser.add_argument("--limit", type=int, default=20, help="Max topics to process (default 20)")

    # 'design' subcommand
    design_parser = subparsers.add_parser("design", help="Run the creative pipeline (Phase 7)")
    design_group = design_parser.add_mutually_exclusive_group(required=True)
    design_group.add_argument("post_id", type=int, nargs="?", help="Post ID to design")
    design_group.add_argument("--all", action="store_true", help="Design all DRAFT posts")
    design_parser.add_argument("--provider", type=str, default="mock", choices=["mock", "openai", "gemini", "manual"], help="Image provider to use")

    # 'sync' subcommand
    sync_parser = subparsers.add_parser("sync", help="Sync database to Google Sheets (Phase 8)")
    sync_parser.add_argument("--init", action="store_true", help="Initialize a new spreadsheet and set up tabs")
    sync_parser.add_argument("--sheet-name", type=str, default="Hermes Dashboard", help="Name of the Google Sheet")
    sync_parser.add_argument("--share", type=str, help="Email address to share the sheet with on init")
    sync_parser.add_argument("--status", action="store_true", help="View the status of the last sync")

    # 'vault' subcommand
    vault_parser = subparsers.add_parser("vault", help="Obsidian Vault sync (Phase 9)")
    vault_parser.add_argument("action", choices=["init", "sync", "review"], help="Action to perform")
    vault_parser.add_argument("--month", type=str, help="Month to generate review for (YYYY-MM), defaults to current")

    return parser


def handle_config_command(args: argparse.Namespace) -> int:
    """Handle the 'config' command by printing non-secret config values."""
    config = load_config(args.env_file)
    print("Hermes Social Agent — Configuration Summary")
    print("=" * 45)
    print(f"Environment:        {config.app_env.value}")
    print(f"Log Level:          {config.app_log_level}")
    print(f"Approval Mode:      {config.approval_mode.value}")
    print(f"Autopilot Enabled:  {config.autopilot_enabled}")
    print(f"Publishing Enabled: {config.publishing_enabled}")
    print(f"Allow Paid APIs:    {config.allow_paid_apis}")
    print(f"Database Path:      {config.database_path}")
    print(f"Timezone:           {config.timezone}")
    print(f"Obsidian Vault:     {config.obsidian_vault_path}")
    print(f"Asset Path:         {config.asset_path}")
    print("=" * 45)
    print("Status: Configuration validated successfully.")
    return 0


def handle_run_command(args: argparse.Namespace) -> int:
    """Handle the 'run' command to start the agent pipeline."""
    config = load_config(args.env_file)
    log_level = args.log_level or config.app_log_level
    logger = setup_logging(log_level=log_level)

    logger.info(
        "Starting Hermes Social Agent",
        extra={
            "stage": "INIT",
            "app_env": config.app_env.value,
            "version": __version__,
            "approval_mode": config.approval_mode.value,
            "publishing_enabled": config.publishing_enabled,
        },
    )

    # In Phase 1, we scaffold the loop and report status.
    # Future phases will initialize SQLite, scheduled jobs, Telegram bot, etc.
    if args.once:
        logger.info("Executing single pipeline pass")
        try:
            from hermes_social.metrics import run_metrics_collection
            with get_connection(config.database_path) as conn:
                run_metrics_collection(config, conn)
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")
            
        logger.info(
            "Single pipeline pass completed",
            extra={"stage": "EXECUTE", "result": "SUCCESS"},
        )
        return 0

    logger.info(
        "Hermes Social Agent scaffold running. (Pipeline loop will be integrated in future phases)",
        extra={"stage": "IDLE"},
    )
    return 0


def handle_db_command(args: argparse.Namespace) -> int:
    """Handle the 'db' subcommand (init, backup)."""
    config = load_config(args.env_file)
    db_path = config.database_path

    if args.action == "init":
        print("Initializing Hermes Social Agent Database...")
        applied_versions = init_db(db_path)
        with get_connection(db_path) as conn:
            current_ver = get_current_version(conn)
            cursor = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            table_count = int(cursor.fetchone()[0])
        print("=============================================")
        print(f"Database Path:      {db_path}")
        print(f"Migrations Applied: {len(applied_versions)} {applied_versions}")
        print(f"Schema Version:     {current_ver}")
        print(f"Table Count:        {table_count}")
        print("=============================================")
        print("Status: Database initialized successfully.")
        return 0
    elif args.action == "backup":
        backup_dir = db_path.parent / "backups"
        if not db_path.exists():
            print(f"Error: Database {db_path} does not exist. Run init first.")
            return 1
        print(f"Backing up database from {db_path}...")
        backup_path = backup_database(db_path, backup_dir)
        stat = backup_path.stat()
        print("=============================================")
        print(f"Backup File:  {backup_path.name}")
        print(f"Backup Path:  {backup_path}")
        print(f"Size (bytes): {stat.st_size}")
        print("=============================================")
        print("Status: Database backup completed successfully.")
        return 0
    return 1


def handle_brand_command(args: argparse.Namespace) -> int:
    """Handle the 'brand' command by printing brand system summary."""
    try:
        config = load_config(args.env_file)
        # Assuming brand.yaml is in the project root / config directory
        project_root = Path(__file__).resolve().parent.parent.parent
        brand_path = project_root / "config" / "brand.yaml"
        
        brand = load_brand_system(brand_path)
        
        print("Hermes Social Agent — Brand System Summary")
        print("=" * 45)
        print(f"Creator Name:       {brand.identity.creator_name}")
        print(f"Content Pillars:    {len(brand.content_pillars)}")
        print(f"Visual Families:    {len(brand.visual_families)}")
        print(f"Banned Phrases:     {len(brand.banned_patterns.phrases)}")
        print(f"Banned Behaviors:   {len(brand.banned_patterns.behaviors)}")
        print("-" * 45)
        print("Scoring Thresholds:")
        print(f"  Brand Fit:        {brand.scoring.brand_fit_threshold}")
        print(f"  Writing Quality:  {brand.scoring.writing_quality_threshold}")
        print(f"  Visual Quality:   {brand.scoring.visual_quality_threshold}")
        print("=" * 45)
        print("Status: Brand configuration validated successfully.")
        return 0
    except Exception as e:
        print(f"Error loading brand system: {e}")
        return 1


def handle_discover_command(args: argparse.Namespace) -> int:
    """Handle the 'discover' command by running a trend discovery cycle."""
    try:
        config = load_config(args.env_file)
        project_root = Path(__file__).resolve().parent.parent.parent
        brand_path = project_root / "config" / "brand.yaml"
        sources_path = project_root / "config" / "sources.yaml"
        
        brand = load_brand_system(brand_path)
        sources_config = load_sources_config(sources_path)
        
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        
        print("Hermes Social Agent — Trend Discovery (Phase 4)")
        print(f"Mode: {'COMMIT' if args.commit else 'DRY RUN (Read-only)'}")
        print("=" * 60)
        
        result = run_discovery_cycle(
            conn=conn,
            brand=brand,
            sources_config=sources_config,
            min_opportunity_score=50.0,
            dry_run=not args.commit
        )
        
        print(f"Total Fetched:  {result.total_fetched}")
        print(f"After Dedup:    {result.after_dedup}")
        print(f"After Freshness:{result.after_freshness}")
        print(f"Accepted:       {result.accepted}")
        print(f"Rejected:       {result.rejected}")
        print("-" * 60)
        
        if result.accepted > 0:
            print("Top Accepted Candidates:")
            for sc in result.candidates:
                if sc.rejection_reason is None:
                    print(f"[{sc.opportunity_score:.1f}] {sc.candidate.title[:50]}... ({sc.candidate.source_name})")
                    print(f"      Pillar: {sc.matched_pillar} | URL: {sc.candidate.url}")
                    
        return 0
    except Exception as e:
        print(f"Error running discovery cycle: {e}")
        return 1


def handle_research_command(args: argparse.Namespace) -> int:
    """Handle the 'research' command by running the research engine."""
    try:
        config = load_config(args.env_file)
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        vault_path = Path(config.obsidian_vault_path)
        
        print("Hermes Social Agent — Research Engine (Phase 5)")
        print(f"Mode: {'DRY RUN' if args.dry_run else 'COMMIT'}")
        print("=" * 60)
        
        topic_ids = []
        if args.all:
            # Find all DISCOVERED topics
            cursor = conn.execute(
                "SELECT id FROM topics WHERE status IN (?, ?)",
                (TopicStatus.DISCOVERED.value, TopicStatus.ACCEPTED.value)
            )
            topic_ids = [row[0] for row in cursor.fetchall()]
        elif args.topic_id:
            topic_ids = [args.topic_id]
            
        if not topic_ids:
            print("No topics to research.")
            return 0
            
        for tid in topic_ids:
            print(f"Researching topic {tid}...")
            result = run_research_for_topic(conn, tid, vault_path, dry_run=args.dry_run)
            print(f"  Confidence:     {result.confidence:.1f}/100")
            print(f"  Total Claims:   {result.claims_count}")
            print(f"  Verified Claims:{result.verified_count}")
            print(f"  Disputed Claims:{result.disputed_count}")
            if not args.dry_run:
                print(f"  Saved to Vault: 01-Research/{result.knowledge_pack.topic[:20]}.md")
            print("-" * 40)
            
        print(f"\nSuccessfully researched {len(topic_ids)} topics.")
        return 0
    except Exception as e:
        print(f"Error running research engine: {e}")
        return 1


def handle_generate_command(args: argparse.Namespace) -> int:
    """Handle the 'generate' command by running the generation engine."""
    try:
        config = load_config(args.env_file)
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        
        # Load brand context
        brand_sys = load_brand_system(Path("config/brand.yaml"))
        brand_config = {
            "brand_voice": brand_sys.voice.sentence_style,
            "content_pillars": [p.name for p in brand_sys.content_pillars],
            "banned_phrases": brand_sys.banned_patterns.phrases,
        }
        
        print("Hermes Social Agent — Content Generation Engine (Phase 6)")
        print("=" * 60)
        
        topic_ids = []
        if args.all:
            # Find all RESEARCHED topics
            cursor = conn.execute(
                "SELECT id FROM topics WHERE status = ? LIMIT ?",
                (TopicStatus.RESEARCHED.value, args.limit)
            )
            topic_ids = [row[0] for row in cursor.fetchall()]
        elif args.topic_id:
            topic_ids = [args.topic_id]
            
        if not topic_ids:
            print("No topics to generate content for.")
            return 0
            
        success_count = 0
        for tid in topic_ids:
            print(f"Generating content for topic {tid}...")
            # For this MVP, we use the mock model route unless configured otherwise.
            # In a real environment, you might read the model from config.
            model_route = "mock" # Or "gemini/gemini-1.5-pro" if API keys are set
            
            success, msgs = generate_content_for_topic(conn, tid, brand_config, model_route=model_route)
            for msg in msgs:
                print(f"  - {msg}")
            if success:
                success_count += 1
            print("-" * 40)
            
        print(f"\nSuccessfully generated content for {success_count}/{len(topic_ids)} topics.")
        return 0
    except Exception as e:
        print(f"Error running generation engine: {e}")
        return 1


def handle_design_command(args: argparse.Namespace) -> int:
    """Handle the 'design' command by running the creative pipeline."""
    try:
        from hermes_social.constants import PostStatus
        from hermes_social.db.repositories.posts import PostRepository
        from hermes_social.creative.pipeline import generate_assets_for_post
        
        config = load_config(args.env_file)
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        
        from hermes_social.services.brand import load_brand_system
        brand_sys = load_brand_system(Path("config/brand.yaml"))
        brand_config = {
            "visual_families": [f.name for f in brand_sys.visual_families]
        }
        
        output_base_dir = Path("data/assets")
        
        print("Hermes Social Agent — Creative Pipeline (Phase 7)")
        print("=" * 60)
        
        post_repo = PostRepository(conn)
        
        posts_to_process = []
        if args.all:
            # Find all DRAFT posts
            cursor = conn.execute("SELECT * FROM posts WHERE status = ?", (PostStatus.DRAFT.value,))
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                posts_to_process.append(dict(zip(columns, row)))
        elif getattr(args, 'post_id', None):
            cursor = conn.execute("SELECT * FROM posts WHERE id = ?", (args.post_id,))
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                posts_to_process.append(dict(zip(columns, row)))
                
        if not posts_to_process:
            print("No DRAFT posts found to design.")
            return 0
            
        success_count = 0
        for p in posts_to_process:
            print(f"Generating assets for post {p['id']}...")
            try:
                if generate_assets_for_post(conn, p, brand_config, output_base_dir, image_provider_type=args.provider, model_route="mock"):
                    print("  - Success")
                    success_count += 1
            except Exception as e:
                print(f"  - Failed: {e}")
                
        print("-" * 40)
        print(f"Successfully generated assets for {success_count}/{len(posts_to_process)} posts.")
        return 0
        
    except Exception as e:
        print(f"Error running creative pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1


def handle_sync_command(args: argparse.Namespace) -> int:
    """Handle the 'sync' command for Google Sheets."""
    try:
        from hermes_social.sheets.client import get_sheets_client
        from hermes_social.sheets.initializer import init_workbook
        from hermes_social.sheets.sync import sync_database_to_sheets
        
        print("Hermes Social Agent — Google Sheets Sync (Phase 8)")
        print("=" * 60)
        
        credentials_path = Path("config/google-credentials.json")
        client = get_sheets_client(credentials_path)
        
        config = load_config(args.env_file)
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        
        if args.status:
            try:
                spreadsheet = client.open(args.sheet_name)
                ws = spreadsheet.worksheet("Sync_Status")
                records = ws.get_all_records()
                print("\nLast Sync Status:")
                print("-" * 60)
                for rec in records:
                    print(f"{rec.get('Tab Name', 'Unknown'):<15} | {rec.get('Status', 'Unknown'):<10} | Rows: {rec.get('Rows Synced', 0):<5} | Duration: {rec.get('Duration (ms)', '0'):>7}ms")
                print("-" * 60)
            except Exception as e:
                print(f"Failed to fetch status: {e}")
            return 0

        if args.init:
            print(f"Initializing workbook: {args.sheet_name}...")
            spreadsheet = init_workbook(client, args.sheet_name, share_email=args.share)
            print(f"Workbook Ready. URL: {spreadsheet.url}")
        else:
            try:
                spreadsheet = client.open(args.sheet_name)
            except Exception:
                print(f"Spreadsheet '{args.sheet_name}' not found. Run with --init first.")
                return 1
                
        sync_result = sync_database_to_sheets(conn, spreadsheet)
        print(f"\nSync complete. Overall Status: {sync_result.overall_status}")
        print("-" * 60)
        for tab in sync_result.tab_results:
            print(f"{tab.tab_name:<15} | {tab.status:<10} | Rows: {tab.rows_synced:<5} | Duration: {tab.duration_ms:>7.2f}ms")
        print("-" * 60)
        return 0 if sync_result.overall_status == "SUCCESS" else 1
        
    except Exception as e:
        print(f"Error running Sheets sync: {e}")
        import traceback
        traceback.print_exc()
        return 1


def handle_vault_command(args: argparse.Namespace) -> int:
    """Handle the 'vault' command for Obsidian (Phase 9)."""
    try:
        from hermes_social.obsidian import initialize_vault, sync_vault
        import datetime
        
        config = load_config(args.env_file)
        vault_path = Path(config.obsidian_vault_path)
        db_path = Path(config.database_path)
        conn = get_connection(db_path)
        
        print("Hermes Social Agent — Obsidian Vault (Phase 9)")
        print("=" * 60)
        
        if args.action == "init":
            print(f"Initializing vault structure at {vault_path}...")
            initialize_vault(vault_path)
            print("Vault structure created successfully.")
            return 0
            
        if not vault_path.exists():
            print(f"Error: Vault path {vault_path} does not exist. Run 'init' first.")
            return 1
            
        if args.action == "sync":
            print(f"Syncing SQLite database state to vault...")
            result = sync_vault(conn, vault_path)
            print(f"\nSync complete. Files written: {result.files_written}")
            if result.errors:
                print("\nErrors encountered:")
                for e in result.errors:
                    print(f"- {e}")
            return 0 if not result.errors else 1
            
        elif args.action == "review":
            from hermes_social.obsidian.sync import generate_monthly_review
            if args.month:
                year, month = map(int, args.month.split('-'))
            else:
                now = datetime.datetime.now()
                year, month = now.year, now.month
                
            print(f"Generating review for {year}-{month:02d}...")
            generate_monthly_review(conn, vault_path, year, month)
            print("Monthly review generated.")
            return 0
            
    except Exception as e:
        print(f"Error executing vault command: {e}")
        import traceback
        traceback.print_exc()
        return 1


def handle_telegram_command(args: argparse.Namespace, config: AppConfig) -> int:
    """Handle the 'telegram' CLI subcommand."""
    action = getattr(args, "telegram_action", None)
    if not action:
        print("[!] No telegram action specified. Use 'start' or 'test'.")
        return 1
        
    try:
        if action == "start":
            if not config.telegram_bot_token:
                print("[!] TELEGRAM_BOT_TOKEN must be set to start the bot.")
                return 1
                
            from hermes_social.telegram import start_bot
            with get_connection(config.database_path) as conn:
                start_bot(config, conn)
                
        elif action == "test":
            if not config.telegram_bot_token or not config.telegram_chat_id:
                print("[!] TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set.")
                return 1
                
            import asyncio
            from telegram import Bot
            
            async def send_test():
                bot = Bot(token=config.telegram_bot_token)
                await bot.send_message(
                    chat_id=config.telegram_chat_id,
                    text="👋 Hermes Social Agent: Test message from CLI."
                )
            
            print(f"[*] Sending test message to chat {config.telegram_chat_id}...")
            asyncio.run(send_test())
            print("[+] Test message sent successfully.")
            
    except Exception as e:
        print(f"Telegram command failed: {e}")
        import traceback
        traceback.print_exc()
        print(f"[!] Error: {e}")
        return 1
        
    return 0


def handle_publish_command(args: argparse.Namespace, config: AppConfig) -> int:
    """Handle the 'publish' CLI subcommand."""
    from hermes_social.publishing import get_publisher, validate_all_publishers
    from hermes_social.constants import Platform
    
    if args.check:
        print("[*] Validating credentials for all platforms...")
        results = validate_all_publishers(config)
        for platform, is_valid in results.items():
            status = "✅ VALID" if is_valid else "❌ INVALID/MISSING"
            print(f"  {platform.title()}: {status}")
        return 0
        
    if not args.post_id:
        print("[!] Must provide a post_id to publish, or use --check")
        return 1
        
    with get_connection(config.database_path) as conn:
        from hermes_social.db.repositories.posts import PostRepository
        repo = PostRepository(conn)
        post = repo.get_by_id(args.post_id)
        
        if not post:
            print(f"[!] Post {args.post_id} not found.")
            return 1
            
        try:
            platform = Platform(post["platform"])
        except ValueError:
            platform = Platform.LINKEDIN
            
        publisher = get_publisher(platform, config)
        payload = publisher.prepare_payload(post, [])
        
        print(f"[*] Publishing post {args.post_id} to {platform.value}...")
        is_dry_run = getattr(args, "dry_run", config.publishing_dry_run)
        
        result = publisher.publish(payload, dry_run=is_dry_run)
        
        if result.success:
            print(f"[+] Publish successful! ID: {result.platform_post_id}")
            if result.platform_url:
                print(f"    URL: {result.platform_url}")
        else:
            print(f"[-] Publish failed: {result.error}")
            
        if result.fallback_triggered:
            print("[!] Fallback to manual publishing was triggered.")
            
    return 0


def handle_metrics_command(args: argparse.Namespace, config: AppConfig) -> int:
    """Handle the 'metrics' CLI subcommand."""
    from hermes_social.metrics import run_metrics_collection, calculate_median_baselines
    
    if args.metrics_action == "collect":
        print("[*] Running metrics snapshot pipeline...")
        with get_connection(config.database_path) as conn:
            run_metrics_collection(config, conn)
        return 0
    elif args.metrics_action == "analyze":
        print("[*] Calculating historical medians...")
        with get_connection(config.database_path) as conn:
            baselines = calculate_median_baselines(conn)
            if not baselines:
                print("No baseline data available yet.")
                return 0
            
            for key, data in baselines.items():
                print(f"[{key}]")
                print(f"  Median Impressions: {data['impressions']}")
                print(f"  Median Likes:       {data['likes']}")
                print()
        return 0
    else:
        print("[!] Unknown metrics action.")
        return 1


def handle_experiments_command(args: argparse.Namespace, config: AppConfig) -> int:
    """Handle the 'experiments' CLI subcommand."""
    from hermes_social.db.repositories.experiments import ExperimentRepository
    from hermes_social.experiments.engine import evaluate_experiment
    
    if args.exp_action == "evaluate":
        print("[*] Evaluating active experiments...")
        with get_connection(config.database_path) as conn:
            repo = ExperimentRepository(conn)
            active = repo.list_active()
            if not active:
                print("No active experiments found.")
                return 0
            for exp in active:
                evaluate_experiment(exp["id"], conn)
        print("[*] Evaluation complete.")
        return 0
    elif args.exp_action == "simulate":
        print("[*] Running Exit Gate Simulation...")
        import subprocess
        import sys
        result = subprocess.run([sys.executable, "scripts/simulate_experiments.py"])
        return result.returncode
    else:
        print("[!] Unknown experiments action.")
        return 1


def handle_learning_command(args: argparse.Namespace, config: AppConfig) -> int:
    """Handle the 'learning' CLI subcommand."""
    from hermes_social.learning.observer import generate_observations
    from hermes_social.learning.hypothesizer import generate_hypotheses
    from hermes_social.learning.decay import decay_confidence
    from hermes_social.learning.obsidian import sync_vault
    
    if args.learning_action == "cycle":
        print("[*] Running Learning Cycle...")
        with get_connection(config.database_path) as conn:
            print("  - Generating observations...")
            obs = generate_observations(conn)
            print(f"    -> Found {len(obs)} anomalies.")
            
            print("  - Generating hypotheses...")
            generate_hypotheses(conn, config, obs)
            
            print("  - Decaying confidence on old rules...")
            decay_confidence(conn)
            
        print("[*] Learning cycle complete.")
        return 0
    elif args.learning_action == "sync":
        print("[*] Syncing Obsidian vault...")
        with get_connection(config.database_path) as conn:
            sync_vault(conn, config)
        return 0
    else:
        print("[!] Unknown learning action.")
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI execution entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        print(f"hermes-social {__version__}")
        return 0
    elif args.command == "config":
        return handle_config_command(args)
    elif args.command == "run":
        return handle_run_command(args)
    elif args.command == "db":
        return handle_db_command(args)
    elif args.command == "brand":
        return handle_brand_command(args)
    elif args.command == "discover":
        return handle_discover_command(args)
    elif args.command == "research":
        return handle_research_command(args)
    elif args.command == "generate":
        return handle_generate_command(args)
    elif args.command == "design":
        return handle_design_command(args)
    elif args.command == "sync":
        return handle_sync_command(args)
    elif args.command == "vault":
        return handle_vault_command(args)
    elif args.command == "telegram":
        config = load_config(args.env_file)
        return handle_telegram_command(args, config)
    elif args.command == "publish":
        config = load_config(args.env_file)
        return handle_publish_command(args, config)
    elif args.command == "metrics":
        config = load_config(args.env_file)
        return handle_metrics_command(args, config)
    elif args.command == "experiments":
        config = load_config(args.env_file)
        return handle_experiments_command(args, config)
    elif args.command == "learning":
        config = load_config(args.env_file)
        return handle_learning_command(args, config)
    else:
        # Default behavior when no subcommand is given: print help
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
