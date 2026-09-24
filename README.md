# rss
A [maubot](https://github.com/maubot/maubot) that posts RSS feed updates to Matrix.

## Usage
Basic commands:

* `!rss subscribe <url>` - Subscribe the current room to a feed.
* `!rss unsubscribe <feed ID>` - Unsubscribe the current room from a feed.
* `!rss subscriptions` - List subscriptions (and feed IDs) in the current room.
* `!rss notice <feed ID> [true/false]` - Set whether the bot should send new
  posts as `m.notice` (if false, they're sent as `m.text`).
* `!rss template <feed ID> [new template]` - Change the post template for a
  feed in the current room. If the new template is omitted, the bot replies
  with the current template.
* `!rss profile <feed ID> [display name] [mxc://avatar]` - Change the
  per-message profile for a feed in the current room. If both are omitted,
  the bot replies with the current profile. Use `reset` (or `clear`) to go
  back to the feed's own title and icon.

### Per-message profiles
Posts are sent with a per-message profile ([MSC4144], unstable field
`com.beeper.per_message_profile`), so clients that support it show the feed's
title as the sender name and the feed's icon (RSS `<image>`, Atom `<icon>`, or
JSON Feed `icon`) as the avatar. Feeds that don't provide an icon get one
from a favicon lookup service instead (`favicon_service_url` in the config,
Google by default; set it to an empty string to disable). The lookup uses the
hostname of the feed's home page and falls back to its parent domains. Icons are uploaded
to the homeserver and cached in the `avatar` table; they are re-checked every
`avatar_refresh_days` days and only re-uploaded when the image changed. Both fields can be
overridden per subscription with `!rss profile`; the avatar override must be
an `mxc://` URI. Clients without support show the post exactly as before,
unless `profile_fallback` is enabled in the config, which prefixes every post
with the display name as described in the MSC.

[MSC4144]: https://github.com/matrix-org/matrix-spec-proposals/pull/4144

### Templates
The default template is `New post in $feed_title: [$title]($link)`.

Templates are interpreted as markdown with some simple variable substitution.
The following variables are available:

* `$feed_url` - The URL that was used to subscribe to the feed.
* `$feed_link` - The home page of the feed.
* `$feed_title` - The title of the feed.
* `$feed_subtitle` - The subtitle of the feed.
* `$id` - The unique ID of the entry.
* `$date` - The date of the entry.
* `$title` - The title of the entry.
* `$summary` - The summary/description of the entry.
* `$link` - The link of the entry.
