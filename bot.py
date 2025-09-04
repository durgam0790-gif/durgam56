# bot.py
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import aiohttp
import io
import os

# استدعاء التوكن من ملف خارجي
from config import TOKEN

# ------------------- إعدادات البوت -------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

WELCOME_CHANNEL_ID = 1412259665995370579
ANIME_GIF_PATH = "gif.gif"
OUTPUT_PATH = "welcome.gif"
FONT_PATH = "StoryScript-Regular.ttf"  # ضع ملف الخط هنا

# ------------------- دالة إنشاء بطاقة الترحيب -------------------
async def create_welcome(member):
    if not os.path.exists(ANIME_GIF_PATH):
        print(f"❌ ملف GIF غير موجود: {ANIME_GIF_PATH}")
        return None

    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(str(avatar_url)) as resp:
            avatar_bytes = await resp.read()

    avatar_image = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar_image = avatar_image.resize((100,100))  # حجم الصورة أصغر

    avatar_mask = Image.new("L", avatar_image.size, 0)
    draw_mask = ImageDraw.Draw(avatar_mask)
    draw_mask.ellipse((0,0,avatar_image.size[0], avatar_image.size[1]), fill=255)

    bg_gif = Image.open(ANIME_GIF_PATH)
    frames = []

    for frame in ImageSequence.Iterator(bg_gif):
        frame = frame.convert("RGBA")

        frame_width, frame_height = frame.size
        avatar_x = 10
        avatar_y = frame_height // 2 - avatar_image.size[1] // 2
        frame.paste(avatar_image, (avatar_x, avatar_y), mask=avatar_mask)

        draw = ImageDraw.Draw(frame)

        try:
            font_small = ImageFont.truetype(FONT_PATH, 20)
        except Exception as e:
            print(f"❌ لم يتم تحميل الخط، سيتم استخدام الخط الافتراضي: {e}")
            font_small = ImageFont.load_default()

        text = f"Welcome {member.name}"
        text_bbox = font_small.getbbox(text)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_x = avatar_x
        text_y = avatar_y + avatar_image.size[1] + 5

        for offset in [(2,0), (-2,0), (0,2), (0,-2), (1,1), (-1,-1), (1,-1), (-1,1)]:
            draw.text((text_x+offset[0], text_y+offset[1]), text, fill="black", font=font_small)

        draw.text((text_x, text_y), text, fill="white", font=font_small)

        frames.append(frame)

    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=bg_gif.info.get('duration', 100)
    )

    return OUTPUT_PATH

# ------------------- أحداث البوت -------------------
@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_member_join(member):
    path = await create_welcome(member)
    if path:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(file=discord.File(path))

@bot.command()
async def welcome(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    path = await create_welcome(member)
    if path:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(file=discord.File(path))

# ------------------- تشغيل البوت -------------------
bot.run(TOKEN)