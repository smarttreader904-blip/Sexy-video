const { Telegraf, Markup } = require("telegraf");
const axios = require("axios");
const { exec } = require("child_process");
const fs = require("fs");
const config = require("./config");

const bot = new Telegraf(config.BOT_TOKEN);

// memory
const users = new Map();
const userVideos = new Map();
const savedMedia = new Map();

/* ================= START ================= */
bot.start(async (ctx) => {
const id = ctx.from.id;

if (users.get(id) === "joined") {
return ctx.reply(
`✅ Welcome!

🇧🇩 বাংলায়:
আপনি এখন বট ব্যবহার করতে পারবেন।
TikTok / YouTube Shorts ভিডিও ডাউনলোড করতে লিংক পাঠান 📥

🇬🇧 English:
You can now use the bot. Send a TikTok or YouTube Shorts link 📥`
);
}

return ctx.reply(
"👋 Welcome!\n\nPlease join our channels to use the bot:",
Markup.inlineKeyboard([
[Markup.button.url("🌍 Global Channel", "https://t.me/Global_Method_Channel")],
[Markup.button.url("📩 Support Owner", "https://t.me/Smart_Method_Owner")],
[Markup.button.callback("✅ I Joined", "joined_check")]
])
);
});

/* ================= JOIN ================= */
bot.action("joined_check", (ctx) => {
users.set(ctx.from.id, "joined");

ctx.reply(
`✅ Welcome!

🇧🇩 বাংলায়:
আপনি এখন বট ব্যবহার করতে পারবেন।
TikTok / YouTube Shorts ভিডিও ডাউনলোড করতে লিংক পাঠান 📥

🇬🇧 English:
You can now use the bot. Send a TikTok or YouTube Shorts link 📥`
);

// MENU
ctx.reply(
"📁 Menu:",
Markup.keyboard([
["📁 Media Save Video"]
]).resize()
);
});

/* ================= TIKTOK ================= */
async function getTikTok(url) {
try {
const api = `https://www.tikwm.com/api/?url=${encodeURIComponent(url)}`;
const res = await axios.get(api);

if (res?.data?.data?.play) {
return {
video: res.data.data.play,
audio: res.data.data.music
};
}

return null;
} catch (err) {
console.log("TikTok error:", err.message);
return null;
}
}

/* ================= YOUTUBE DOWNLOAD (STABLE) ================= */
function getYouTube(url, callback) {
const file = `yt_${Date.now()}.mp4`;

const cmd = `yt-dlp -f "mp4/best" -o "${file}" "${url}"`;

exec(cmd, (err) => {
if (err) {
console.log("YT error:", err.message);
return callback(null);
}

if (!fs.existsSync(file)) return callback(null);

callback({ video: file });
});
}

/* ================= MESSAGE HANDLER ================= */
bot.on("text", async (ctx) => {
const id = ctx.from.id;
const url = ctx.message.text;

if (url.startsWith("/")) return;

if (users.get(id) !== "joined") {
return ctx.reply("❌ Please join first and click I Joined button!");
}

/* ================= MENU ================= */
if (url === "📁 Media Save Video") {
const list = savedMedia.get(id);

if (!list || list.length === 0) {
return ctx.reply("❌ No saved media found!");
}

for (let i = 0; i < list.length; i++) {
await ctx.replyWithVideo(list[i], {
caption: `📁 Saved Video #${i + 1}`
});
}

return;
}

/* ================= YOUTUBE ================= */
if (url.includes("youtube.com") || url.includes("youtu.be")) {

ctx.reply("⏳ Downloading YouTube Shorts...");

return getYouTube(url, async (data) => {
if (!data?.video) return ctx.reply("❌ Failed to download!");

userVideos.set(id, data);

await ctx.replyWithVideo({ source: data.video }, {
caption:
"📥 Download Completed Successfully!\n🎬 YouTube Shorts Ready\n\n🎧 Want MP3? Click below",
reply_markup: {
inline_keyboard: [
[{ text: "💾 Save Media", callback_data: "save_media" }],
[{ text: "🟢 Need MP3", callback_data: "get_mp3" }]
]
}
});
});
}

/* ================= TIKTOK ================= */
if (!url.includes("tiktok.com")) {
return ctx.reply("❌ Please send a valid TikTok or YouTube link!");
}

ctx.reply("⏳ Downloading TikTok video...");

const data = await getTikTok(url);

if (!data?.video) {
return ctx.reply("❌ Failed to download!");
}

userVideos.set(id, data);

return ctx.replyWithVideo({ url: data.video }, {
caption:
"📥 Download Completed Successfully!\n🎬 Your video is ready to watch and save.\n\n🎧 Want only MP3? Click button below",
reply_markup: {
inline_keyboard: [
[{ text: "💾 Save Media", callback_data: "save_media" }],
[{ text: "📩 Support ID", url: "https://t.me/Smart_Method_Owner" }],
[{ text: "👥 Support Team", url: "https://www.tiktok.com/@mdraju_3m" }],
[{ text: "🟢 Need MP3", callback_data: "get_mp3" }]
]
}
});
});

/* ================= SAVE MEDIA ================= */
bot.action("save_media", (ctx) => {
const id = ctx.from.id;
const data = userVideos.get(id);

if (!data?.video) {
return ctx.reply("❌ No video found!");
}

if (!savedMedia.has(id)) {
savedMedia.set(id, []);
}

savedMedia.get(id).push(data.video);

ctx.answerCbQuery("📌 Video saved successfully!");
});

/* ================= SHOW SAVED ================= */
bot.hears("📁 Media Save Video", async (ctx) => {
const id = ctx.from.id;
const list = savedMedia.get(id);

if (!list || list.length === 0) {
return ctx.reply("❌ No saved media found!");
}

for (let i = 0; i < list.length; i++) {
await ctx.replyWithVideo(list[i], {
caption: `📁 Saved Video #${i + 1}`
});
}
});

/* ================= MP3 ================= */
bot.action("get_mp3", async (ctx) => {
const data = userVideos.get(ctx.from.id);

if (!data?.audio) {
return ctx.reply("❌ No audio found!");
}

return ctx.replyWithAudio({ url: data.audio }, {
caption: "🎧 MP3 Downloaded Successfully!"
});
});

/* ================= ERROR ================= */
bot.catch((err) => console.log("Bot Error:", err));

bot.launch();

console.log("🚀 Bot is running...");
