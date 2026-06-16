const { Telegraf, Markup } = require("telegraf");
const axios = require("axios");
const config = require("./config");

const bot = new Telegraf(config.BOT_TOKEN);

// memory
const users = new Map();
const userVideos = new Map();
const savedMedia = new Map(); // NEW ADDED

/* ================= START ================= */
bot.start(async (ctx) => {
  const id = ctx.from.id;

  if (users.get(id) === "joined") {
    return ctx.reply(
`✅ Welcome!

🇧🇩 বাংলায়:
আপনি এখন বট ব্যবহার করতে পারবেন।
TikTok ভিডিও ডাউনলোড করতে ভিডিও লিংক পাঠান 📥

🇬🇧 English:
You can now use the bot. Send a TikTok link to download video 📥`
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
TikTok ভিডিও ডাউনলোড করতে ভিডিও লিংক পাঠান 📥

🇬🇧 English:
You can now use the bot. Send a TikTok link to download video 📥`
  );

  // MENU BUTTON (NEW)
  ctx.reply(
    "📁 Menu:",
    Markup.keyboard([
      ["📁 Media Save Video"]
    ]).resize()
  );
});

/* ================= VIDEO API ================= */
async function getVideo(url) {
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
    console.log("Download error:", err.message);
    return null;
  }
}

/* ================= MESSAGE HANDLER ================= */
bot.on("text", async (ctx) => {
  const id = ctx.from.id;
  const url = ctx.message.text;

  if (url.startsWith("/")) return;

  if (users.get(id) !== "joined") {
    return ctx.reply("❌ Please join first and click I Joined button!");
  }

  // MENU CLICK HANDLER
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

  if (!url.includes("tiktok.com")) {
    return ctx.reply("❌ Please send a valid TikTok link!");
  }

  ctx.reply("⏳ Downloading TikTok video...");

  const data = await getVideo(url);

  if (!data?.video) {
    return ctx.reply("❌ Failed to download video!");
  }

  userVideos.set(id, data);

  return ctx.replyWithVideo(
    { url: data.video },
    {
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
    }
  );
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

  return ctx.answerCbQuery("📌 Video saved successfully!");
});

/* ================= MP3 ================= */
bot.action("get_mp3", async (ctx) => {
  const data = userVideos.get(ctx.from.id);

  if (!data?.audio) {
    return ctx.reply("❌ No audio found! Send video again.");
  }

  return ctx.replyWithAudio(
    { url: data.audio },
    {
      caption: "🎧 MP3 Downloaded Successfully!"
    }
  );
});

/* ================= ERROR ================= */
bot.catch((err) => console.log("Bot Error:", err));

bot.launch();

console.log("🚀 Bot is running...");
