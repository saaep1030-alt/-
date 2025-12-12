import os
import discord
import asyncio
import requests
from bs4 import BeautifulSoup

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1448567374667055124  # 여기에 알림 보낼 채널 ID

BASE_URL = "https://elsword.nexon.com"
NOTICE_URL = "https://elsword.nexon.com/News/Notice/List?n4ArticleCategorySN=3"
EVENT_URL = "https://elsword.nexon.com/News/Events/List"

CHECK_INTERVAL = 60  # 60초마다 체크

intents = discord.Intents.default()
client = discord.Client(intents=intents)

last_notice_id = None
last_event_id = None


def get_latest_post(url):
    """엘소드 공지 리스트에서 최신 글 1개 가져오기"""
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        first = soup.select_one(".bd_lst li")
        if not first:
            return None

        link_tag = first.select_one("a")
        title_tag = first.select_one(".tit")
        thumb_tag = first.select_one("img")

        href = link_tag.get("href")
        full_url = BASE_URL + href

        return {
            "id": href,
            "title": title_tag.get_text(strip=True),
            "url": full_url,
            "thumb": BASE_URL + thumb_tag.get("src") if thumb_tag else None
        }

    except Exception as e:
        print("오류:", e)
        return None


async def check_updates():
    global last_notice_id, last_event_id

    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    print(f"🔍 모니터링 시작: {channel.name}")

    while not client.is_closed():

        # 🔔 공지 체크
        notice = get_latest_post(NOTICE_URL)
        if notice and notice["id"] != last_notice_id:
            last_notice_id = notice["id"]
            embed = discord.Embed(
                title="📢 새 공지/점검 안내!",
                description=notice["title"],
                color=0x00BFFF
            )
            embed.add_field(name="링크", value=notice["url"])

            if notice["thumb"]:
                embed.set_thumbnail(url=notice["thumb"])

            await channel.send(embed=embed)
            print("공지 감지됨!")

        # 🛒 캐시샵(이벤트) 체크
        evt = get_latest_post(EVENT_URL)
        if evt and evt["id"] != last_event_id:
            last_event_id = evt["id"]
            embed = discord.Embed(
                title="🛒 새 캐시샵 업데이트!",
                description=evt["title"],
                color=0xFF69B4
            )
            embed.add_field(name="링크", value=evt["url"])

            if evt["thumb"]:
                embed.set_thumbnail(url=evt["thumb"])

            await channel.send(embed=embed)
            print("캐시샵 감지됨!")

        await asyncio.sleep(CHECK_INTERVAL)


@client.event
async def on_ready():
    print("봇 로그인:", client.user)

    # ⬇⬇⬇ 여기! 이 한 줄만 넣는 거야
    await client.change_presence(
        activity=discord.Game(name="누붕이 작동 중")
    )


async def main():
    async with client:
        client.loop.create_task(check_updates())
        await client.start(TOKEN)


asyncio.run(main())
