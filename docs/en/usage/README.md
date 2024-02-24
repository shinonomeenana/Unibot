# Feature List

> This document will guide you in using UniBot.

- UniBot is a functional Discord bot that mainly provides query services related to "Project SEKAI Colorful Stage" Japanese server, international server, Traditional Chinese server and Korean Server.
- By using this bot, you agree to the [Terms of Use](/en/licence/) and [Privacy Policy](/en/privacy/).
- If you have any comments, you can join the feedback server (just opened)：[https://discord.gg/R74mYeCG](https://discord.gg/R74mYeCG)


## Query Project Sekai Song Information
### pjskinfo
- `pjskinfo+song name` to view detailed information about the current song.
- `pjskbpm+song name` to view the BPM.
- `findbpm+number` to query all songs with the corresponding BPM.

### Chart Preview
- `pjskchart [song title] [difficulty]` to preview the chart of the corresponding song and difficulty (Source: [ぷろせかもえ！](https://pjsekai.moe/)
  - Supported difficulty inputs: `easy`, `normal`, `hard`, `expert`, `master`, `append`, `ez`, `nm`, `hd`, `ex`, `ma`, `ap`, `apd`
  - If querying for `master`, the difficulty can be omitted.
- `pjskchart2 [song title] [difficulty]` to preview the chart of the corresponding song and difficulty (Source: [プロセカ譜面保管所](https://sdvx.in/prsk.html)).

### alias Settings

- `pjskset[alias]to[musictitle]`
- `pjskdel[alias]` to delete the corresponding alias.
- `charaset[alias]to[character name](existing alias can be used)` to set a common alias for the character across all groups, e.g., `charasetkndto宵崎奏`
- `charadel[alias]` to delete the common alias for the character across all groups.
- `grcharaset[new alias]to[exist alias]` to set a alias for the character that is only usable in the current group.
- `grcharadel[exist alias]` to delete the alias for the character that is only usable in the current group.
- `charainfo[alias]` to view the alias for the character in the group and across all groups.

::: warning Note
All song alias settings and character alias settings will be publicly displayed daily on the [Real-time Log](/dailylog/) page.
:::


## Query Player Information

> Add `en` before the command to query international server information, e.g., `enbind`, `ensk`, `enpjskcheck`, `enpjskprogress`, `enpjskprofile`.

> Add `tw` before the command to query Traditional Chinese server information, e.g., `twbind`, `twsk`, `twpjskcheck`, `twpjskprogress`, `twpjskprofile`.

> Add `kr` before the command to query Korean server information, e.g., `krbind`, `krsk`, `krpjskcheck`, `krpjskprogress`, `krpjskprofile`.

- `bind+id` to bind an ID.
### Event Query
- `sk+id` to query rankings if you are in top 100 ranking.
- `sk+rank` to query the score corresponding to the ranking in top 100 (jp server supports specific ranking lines).
- `pjskpredict` to view the prediction line, prediction information is sourced from [3-3.dev](https://3-3.dev/) (Japanese server only).
- `pjskpeek+id` or `pjskpeek+rank` to query the weekly play count, speed, average points, etc. for the top 100 players (Japanese server, Traditional Chinese server).
- `stoptime+id` or `stoptime+rank` to query the parking situation for the top 100 players (Japanese server, Traditional Chinese server).
- `scoreline+id` or `scoreline+rank` to plot the score trend for the top 100 players over time (Japanese server, Traditional Chinese server).

### User Query
- `pjskcheck+id` to view the FC and AP count, as well as ranking information for the EX and Master difficulties of the corresponding ID.
- `pjskcheck` to view the FC and AP count, as well as ranking information for the EX and Master difficulties of the bound ID.
- `pjskprofile` to generate a profile image for the bound ID
### Privacy-related
- `pjskprivate` Your ID will not be displayed when checking scores or `pjskcheck` yourself.
- `pjskpublic` to allow others to see.

### Card and Event Information Query
> The `findcard/event` functionalities were written by [Yozora](https://github.com/cYanosora). Many thanks.
- `findcard [character alias]`: Get all cards of the current character.
- `cardinfo [card ID]`: Get detailed information about the card with the specified ID.
- `event [event ID]`: View information about the specified event (can use `event` to view current event information directly).
- `findevent [keywords]`: Filter events by keywords and return a summary image. If no keywords are provided, a prompt image will be returned.
  - Single keyword method:
    - `findevent 5v5`: Return events with the 5v5 type.
    - `findevent mysterious`: Return events with the Purple Moon attribute.
    - `findevent knd`: Return events that include knd cards (including rewards).
    - `findevent miku`: Return events with any combination of Miku cards.
    - `findevent 25miku`: Return events with White Leek cards.
    - `findevent 25h`: Return events with any 25 members (excluding vs), not limited to the 25-box event.
  - Multiple keyword method:
    - `findevent pure 5v5`: Return events with the 5v5 type and Green Grass attribute.
    - `findevent knd cool`: Return events with the Blue Star attribute and knd cards.
    - `findevent marathon mysterious knd`: Return Marathon-type events with the Purple Moon attribute and knd cards (even if knd cards have different attributes, they will be displayed).
  - Examples:
    - `findevent 25h`: Only return events related to the 25-box event.
    - `findevent 25h 25miku`: Return events related to the 25-box event with White Leek cards.
    - `findevent knd ick`: Return events with mixed knd and ick cards.
- `findevent all`: Return a summary of all current events. This functionality cannot be used in channel bots due to large image size.

## Project Sekai Guessing
- Guessing with cropped colored song illustrations: `pjskguess`
- Guessing with cropped black and white song illustrations: `pjskguess2`
- Guessing with lyrics (Japanese): `lyricsguess`
- Guessing with very small cut (30*30): `pjsk非人类猜曲`
- Guessing the song with chart: `chartguess`
- Guessing the card's character with cropped card's image: `charaguess`

- End song guessing: `endpjskguess`
- End character guessing: `endcharaguess`

Top 10 users：guess command + `rank`, for example `pjskguessrank`、`chartguessrank`

## Project Sekai Card Drawing (Gacha) Simulation
> Ten consecutive card draws will generate an image.
- `pjskgacha`: Simulate ten consecutive draws.
- `sekaiXXpull`: Simulate `XX` draws (only display rarity-4 cards). `XX` accepts values from `1` to `200` (from `1` to `400` in channels).
- `pjskgacha2`: Reverse the probability of two-star and rarity-4 cards.
- `pjskgacha+[card pool id]`: Simulate ten consecutive draws in the corresponding card pool.
- `sekai100pull+[card pool id]`: Simulate 100 draws (only display rarity-4 cards) in the corresponding card pool.
- `sekai200pull+[card pool id]`: Simulate 200 draws (only display rarity-4 cards) in the corresponding card pool.
- `pjskgacha2+[card pool id]`: Reverse the probability of rarity-2 and rarity-4 cards in the corresponding card pool.

::: tip About Card Pool ID
The card pool ID can be found by visiting <https://sekai.best/gacha> and checking the number at the end of the URL. For example, if the URL is <https://sekai.best/gacha/159>, the card pool ID is `159`.
:::


## About
- Developer: [綿菓子ウニ](https://space.bilibili.com/622551112)
### Framework Used
- [discord.py](https://discordpy.readthedocs.io/en/stable)
### Data Sources
- Prediction line: [33Kit](https://3-3.dev/)
- Chart preview: [ぷろせかもえ！](https://pjsekai.moe/), [プロセカ譜面保管所](https://sdvx.in/prsk.html)
- honor images for Traditional Chinese and EN servers: [Sekai Viewer](https://sekai.best/)