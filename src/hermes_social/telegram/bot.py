"""Telegram Bot Application and Polling Loop."""

import logging
import sqlite3
from hermes_social.constants import TelegramIntent
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from hermes_social.config import AppConfig
from hermes_social.db.repositories.operations import OperationsRepository
from hermes_social.telegram.intents import TelegramIntentParser, ParsedIntent
from hermes_social.telegram.confirmation import ConfirmationManager
from hermes_social.telegram.handlers import handle_intent
from hermes_social.telegram.cards import build_confirmation_card

logger = logging.getLogger(__name__)


class TelegramBot:
    """Main Telegram bot interface for Hermes Social Agent."""

    def __init__(self, config: AppConfig, conn: sqlite3.Connection):
        self.config = config
        self.conn = conn
        
        if not self.config.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is missing from config.")
            
        self.app = Application.builder().token(self.config.telegram_bot_token).build()
        self.intent_parser = TelegramIntentParser()
        self.confirmation_manager = ConfirmationManager()
        self.ops_repo = OperationsRepository(conn)
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))

    def start_polling(self) -> None:
        """Start the bot in long-polling mode (blocking)."""
        logger.info("Starting Telegram Command Center in long-polling mode...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

    def _is_authorized(self, update: Update) -> bool:
        """Verify the message comes from the configured chat ID."""
        if not update.effective_chat:
            return False
            
        chat_id = str(update.effective_chat.id)
        # If no chat ID is configured yet, allow the first interaction and log it,
        # but ideally we want strict authorization.
        if self.config.telegram_chat_id and chat_id != self.config.telegram_chat_id:
            logger.warning(f"Unauthorized chat attempt from ID: {chat_id}")
            return False
        return True

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        if not self._is_authorized(update):
            return
            
        await update.message.reply_text(
            "👋 Hermes Social Agent Command Center is online.\n\n"
            "You can speak to me naturally. Ask for a status report, "
            "approve pending posts, or pause publishing."
        )

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Parse natural language and route to action handlers."""
        if not self._is_authorized(update):
            return
            
        raw_text = update.message.text
        chat_id = str(update.effective_chat.id)
        
        # 1. Parse intent
        parsed = self.intent_parser.parse(raw_text, self.conn)
        
        # 2. Audit log the incoming command
        self.ops_repo.log_telegram_command(
            chat_id=chat_id,
            raw_text=raw_text,
            parsed_intent=parsed.intent.value
        )
        self.conn.commit()
        
        # 3. Check for destructive confirmation
        if self.confirmation_manager.requires_confirmation(parsed.intent):
            pending = self.confirmation_manager.create_pending(parsed)
            text, keyboard = build_confirmation_card(
                action_description=f"{parsed.intent.value}", 
                action_id=pending.action_id
            )
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
            return
            
        # 4. Dispatch to handler
        response = handle_intent(parsed, self.conn, self.config)
        await update.message.reply_text(response, parse_mode="Markdown")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline keyboard button presses."""
        query = update.callback_query
        await query.answer()
        
        if not self._is_authorized(update):
            return

        data = query.data
        
        # Check if it's a confirmation callback
        if data.startswith("confirm_"):
            action_id = data.split("_", 1)[1]
            parsed = self.confirmation_manager.confirm(action_id)
            if parsed:
                # Execute the confirmed action
                response = handle_intent(parsed, self.conn, self.config)
                await query.edit_message_text(f"✅ Confirmed.\n\n{response}", parse_mode="Markdown")
            else:
                await query.edit_message_text("❌ Action expired or already processed.")
            return
            
        if data.startswith("cancel_"):
            action_id = data.split("_", 1)[1]
            self.confirmation_manager.cancel(action_id)
            await query.edit_message_text("❌ Action cancelled.")
            return
            
        # Handle Approve/Reject callbacks (shortcut bypassing NL parser)
        if data.startswith("approve_"):
            post_id = data.split("_", 1)[1]
            parsed = ParsedIntent(
                intent=TelegramIntent.APPROVE_POST,
                confidence=1.0, 
                raw_text="BUTTON_PRESS", 
                parameters={"post_id": post_id}
            )
            response = handle_intent(parsed, self.conn, self.config)
            await query.edit_message_text(response)
            return
            
        if data.startswith("reject_"):
            post_id = data.split("_", 1)[1]
            parsed = ParsedIntent(
                intent=TelegramIntent.REJECT_POST,
                confidence=1.0,
                raw_text="BUTTON_PRESS",
                parameters={"post_id": post_id}
            )
            response = handle_intent(parsed, self.conn, self.config)
            await query.edit_message_text(response)
            return

        await query.edit_message_text(f"Button '{data}' pressed (not fully implemented).")


def start_bot(config: AppConfig, conn: sqlite3.Connection) -> None:
    """Entry point to start the bot."""
    bot = TelegramBot(config, conn)
    bot.start_polling()
