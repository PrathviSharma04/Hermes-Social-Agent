---
name: telegram-social
description: Handles Telegram command queries for the Social Agent — status checks, pending post reviews, and publishing control.
version: 1.0.0
metadata:
  hermes:
    tags: [social, telegram, control, approval]
    category: business
---
# Telegram Social Commander

When the user asks you (the Hermes AI Agent) about Telegram or social media statuses, respond with appropriate data from the social database.

Database: ~/Hermes-Social-Agent/data/hermes.db

## Commands for the User

### "show pending posts" / "what needs approval"
Query `hermes.db` for posts with `status='PENDING_APPROVAL'`. 
Show the Topic, the LinkedIn draft, and the X draft.
Tell the user to open their Telegram app to click the Approve/Reject buttons. (You cannot click them for the user here).

### "show today's posts" / "what did we publish"
Query `hermes.db` for posts with `status='PUBLISHED'` created today (`date('now')`).
Show the Topic and the text.

### "inspect post [ID]"
Query `hermes.db` where `id=[ID]`.
Show all fields: Topic, LinkedIn text, X text, Image Prompt, Status, and Timestamps.

## Internal Mechanics
The Telegram bot itself is run via `python -m hermes_social.cli telegram start` on the EC2 server (usually managed by systemd or a background worker).
If the user complains the Telegram bot is offline, check if that python process is running on the server.
