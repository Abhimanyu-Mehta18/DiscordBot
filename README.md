# 🤖 Astra Discord Bot (Legacy Project)

**Astra** is a multifunctional Discord bot I developed in **2021** using the `discord.ext.commands` module of the now-archived `discord.py` library. Despite being outdated, this project showcases my passion for real-time API integrations, asynchronous programming, and bot development in Python.

> ⚠️ NOTE: This project is no longer maintained and may not work with the latest Discord API changes. It uses the now-deprecated `discord.py` library.

---

## 🧠 Key Features

### 🎮 Games & Fun
- `tictactoe`: 2-player emoji-based tic-tac-toe game
- `coin`, `dice`, `guess`, `rps`: casual games
- `meme`, `gif`, `quote`, `joke`, `lol`, `fact`: fun & random content
- `wanted`, `rip`, `kill`: image manipulation using user avatars
- `basically`, `8ball`: magic 8-ball responses
- `rainbow`: color-changing embed animation
- `yt`: fetch YouTube video links via search

### 🛠 Moderation
- `kick`, `ban`, `unban`, `mute`, `unmute`
- `addrole`, `removerole`, `createrole`, `deleterole`
- `warn`, `warnings`, `clear`, `lockdown`, `unlock`
- Custom channel creation/deletion: text and voice
- Change nicknames, set server-specific prefixes

### 📚 Utility
- `poll`, `vote`, `dm`, `tts`, `userinfo`, `serverinfo`, `stats`
- `covid`: fetch COVID-19 stats (2020-era API)
- `wiki`: Wikipedia summaries
- `emojiinfo`, `avatar`, `top_role`, `permissions`
- `snipe`: recover recently deleted messages
- `md5`: generate MD5 hash of a string

### 🖼 Image APIs
- Random cat, dog, fox images
- GIPHY GIFs
- Custom emoji creation from image URL

### 🧪 Developer Tools
- `eval`: safely evaluate Python code (with output)
- `help`: custom embedded help command

---

## 🚀 Getting Started

### 🔧 Prerequisites
- Python 3.6+
- `discord.py==1.7.3` (or compatible version)
- Discord bot token
- Some APIs require keys (e.g. GIPHY, prsaw)

### 🛠 Installation

```bash
git clone https://github.com/yourusername/astra-discord-bot.git
cd astra-discord-bot
pip install -r requirements.txt
