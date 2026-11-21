# AI Safety Roadmap: setup

This folder is a small website that lives inside your portfolio repo, `Abi-Boyce/abi-boyce.github.io`. Once it's added, it will be at:

**https://abi-boyce.github.io/roadmap/**

## 1. Add it to your portfolio (one time, about 5 minutes)
1. Go to https://github.com/Abi-Boyce/abi-boyce.github.io
2. Click **Add file → Upload files**.
3. Drag in this whole `roadmap` folder (it holds `index.html`, `progress.json` and this README).
4. Click **Commit changes**. After 1–2 minutes the page is live at the address above.
5. Link it from your portfolio's main page, for example as a "My learning roadmap" button.

## 2. Create a save key (one time)
The page saves your checkmarks to `progress.json` in your repo, so everyone who visits sees your current progress.
1. Go to https://github.com/settings/personal-access-tokens/new (a "fine-grained token").
2. Name: `roadmap`. Expiration: 1 year.
3. Under **Repository access**, choose **Only select repositories** and pick `abi-boyce.github.io`.
4. Under **Permissions → Repository permissions → Contents**, choose **Read and write**.
5. Click **Generate token** and copy it.
6. Open **https://abi-boyce.github.io/roadmap/#edit**, click **Settings**, paste the token, enter your start date (for example `2026-11-30`) and save.

The token is stored only in your own browser, and it can only change files in this one repo. Never paste it anywhere else. If you think it has leaked, delete it on the same GitHub settings page.

## 3. Daily use
- Open **https://abi-boyce.github.io/roadmap/#edit**. Bookmark this address. It's your private edit view.
- Tick off each day as you finish it. You earn XP, keep a streak, and get confetti when you finish a week.
- Each week, add **proof links** (a GitHub repo, a certificate or a write-up), a short **reflection** and the **hours** you studied.
- Click **Save to GitHub**. Visitors see your update within a couple of minutes.

## Stickers, games and low-energy days
- **Mystery packs:** each finished day earns a pack, and a full week earns a rare pack. Open them with **Open packs** in the black bar. Stickers come in a set for each phase plus an Everyday set, with common, rare and shiny ones. Milestone stickers (First Day, First Week, 7-Day Streak and more) are awarded automatically.
- **Practice games:** Flashcard flip (3 right in a row) and Bug hunt (tap the broken line). Winning each game earns one pack a day. Visitors can play the games too.
- **Low-energy day:** on a rough day, do one small thing (the 25-minute timer, a game round, or a two-sentence reflection), then click **I did my minimum today**. It keeps your streak going but doesn't mark a full study day done, so your public progress stays accurate.
- **Sticker shelf:** your collection is shown publicly. Remember to click **Save to GitHub** after opening packs.

Visitors who open the normal address (without `#edit`) see a read-only view. Anyone who adds `#edit` to the address can tick boxes in their own browser, but they can't save anything without your token.

If **Save to GitHub** ever fails, click **Copy progress JSON**, open `roadmap/progress.json` on GitHub, click the pencil icon, paste over the old contents and commit.
