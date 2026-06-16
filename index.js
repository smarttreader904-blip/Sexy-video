const { Telegraf, Markup } = require("telegraf");
const axios = require("axios");
const config = require("./config");

const bot = new Telegraf(config.BOT_TOKEN);

// memory
const users = new Map();
const userVideos = new Map();

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

  return ctx.reply(
`✅ Welcome!

🇧🇩 বাংলায়:
আপনি এখন বট ব্যবহার করতে পারবেন।
TikTok ভিডিও ডাউনলোড করতে ভিডিও লিংক পাঠান 📥

🇬🇧 English:
You can now use the bot. Send a TikTok link to download video 📥`
  );
}); // ✅ FIXED BRACKET HERE

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
          [{ text: "📩 Support ID", url: "https://t.me/Smart_Method_Owner" }],
          [{ text: "👥 Support Team", url: "https://www.tiktok.com/@mdraju_3m" }],
          [{ text: "🟢 Need MP3", callback_data: "get_mp3" }]
        ]
      }
    }
  );
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
