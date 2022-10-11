import asyncio
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import datetime
import os
import shutil

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import redis
# import socks
from telethon import TelegramClient, events, Button
from urllib import parse

import util
from pyp import page91

captionTemplate = '''标题: %s
收藏: %s
作者: %s
关键词： %s
'''
captionTemplateMd = '''标题: %s
'''

REDIS_HOST = os.getenv('REDIS_HOST', "127.0.0.1")
REDIS_PORT = int(os.getenv('REDIS_PORT', "6379"))
REDIS_PASS = os.getenv('REDIS_PASS', "")
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_ID = int(os.getenv('GROUP_ID'))
bot = TelegramClient(None, API_ID, API_HASH,
                     # proxy=(socks.HTTP, '127.0.0.1', 10809)
                     ).start(
    bot_token=BOT_TOKEN)
redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=1, decode_responses=True)


async def saveToredis(key, message_id, user_id):
    redis_conn.set(key, str(message_id) + ',' + str(user_id))


async def getFromredis(key):
    get = redis_conn.get(key)
    if get is not None:
        messList = get.split(',')
        return int(messList[0]), int(messList[1])
    else:
        return 0, 0


@bot.on(events.NewMessage(pattern='/start'))
async def send_welcome(event):
    await event.client.send_message(event.chat_id, '向我发送91视频链接，获取视频,有问题请留言 @bzhzq')


@bot.on(events.NewMessage(pattern='/get91home'))
async def send_welcome(event):
    await event.client.send_message(event.chat_id, '免翻地址: ' + await page91.get91Home())


@bot.on(events.NewMessage(pattern='/help'))
async def send_welcome(event):
    await event.client.send_message(event.chat_id, '''常见问题:
         1.如何设置用户名?

           点击头像设置.

         2.我发送的链接后,没收到视频

           部分高清视频刚发布后还在转码，大概在视频发布时间一小时后再尝试发送链接下载.  

''')


@bot.on(events.NewMessage)
async def echo_all(event):
    text = event.text
    sender = await event.get_sender()

    if event.is_private:
        if 'viewkey' in text:  # 处理91的视频
            params = parse.parse_qs(parse.urlparse(text).query)
            viewkey = params['viewkey'][0]
            viewkey_url = 'https://91porn.com/view_video.php?viewkey=' + viewkey

            # redis查询历史数据
            mid, uid = await getFromredis(viewkey)
            try:
                await event.client.forward_messages(event.chat_id, mid, uid)
                return
            except:
                print("消息已被删除或不存在，无法转发")
            await handle91(event, viewkey, viewkey_url)
        elif 'hsex.men/video-' in text:  # 补充,不向redis存了
            sender = await event.get_sender()
            await handleHs(event, sender, text)
        elif '/vod/play/id' in text:
            # 解析视频id
            path = parse.urlparse(text).path
            viewkey = 'md' + path.split('/')[5]
            viewkey_url = text

            # redis查询历史数据
            mid, uid = await getFromredis(viewkey)
            try:
                await event.client.forward_messages(event.chat_id, mid, uid)
                return
            except:
                print("消息已被删除或不存在，无法转发")
            await handleMd(event, viewkey, viewkey_url)
    else:
        print("None")


async def handleMd(event, viewkey, viewkey_url):
    # 获取视频信息
    try:
        m3u8Url, title = await page91.getMaDou(viewkey_url)
        msg1 = await event.client.send_message(event.chat_id,
                                               '真实视频地址:' + m3u8Url + ' ,正在下载中... ,请不要一次性发送大量链接,被发现后会被封禁! ! !')

        await util.download91(m3u8Url, viewkey)
        # 截图
        await util.imgCoverFromFile(viewkey + '/' + viewkey + '.mp4', viewkey + '/' + viewkey + '.jpg')
        msg = await event.reply(
            '视频下载完成，正在上传。。。如果长时间没收到视频，请重新发送链接')

        # 发送视频
        message = await event.client.send_file(event.chat_id,

                                               viewkey + '/' + viewkey + '.mp4',
                                               supports_streaming=True,
                                               thumb=viewkey + '/' + viewkey + '.jpg',
                                               caption=captionTemplateMd % (title),
                                               reply_to=event.id,
                                               )
        await msg.delete()
        await msg1.delete()
        await saveToredis(viewkey, message.id, message.peer_id.user_id)

        print(str(datetime.datetime.now()) + ':' + title + ' 发送成功')
    finally:
        shutil.rmtree(viewkey, ignore_errors=True)


async def handleHs(event, sender, text):
    p = parse.urlparse(text)
    viewkey = p.path.replace('/', '')
    print("消息来自:" + str(sender.username), ":", text)
    try:
        videoInfo = await page91.getHs(text)
        await util.download91(videoInfo.realM3u8, viewkey, 5)
        # 截图
        await util.imgCover(videoInfo.imgUrl, viewkey + '/' + viewkey + '.jpg')
        segstr = await util.seg(videoInfo.title)
        msg = await event.reply(
            '视频下载完成，正在上传。。。如果长时间没收到视频，请重新发送链接')
        # 发送视频
        await event.client.send_file(event.chat_id,
                                     viewkey + '/' + viewkey + '.mp4',
                                     supports_streaming=True,
                                     thumb=viewkey + '/' + viewkey + '.jpg',
                                     caption=captionTemplate % (
                                         videoInfo.title, '000', '#' + videoInfo.author, segstr),
                                     reply_to=event.id,
                                     )
        await msg.delete()

        print(str(datetime.datetime.now()) + ':' + videoInfo.title + ' 发送成功')
    finally:
        shutil.rmtree(viewkey, ignore_errors=True)

async def cut_video91(is_seg, viewkey):
    if is_seg:
        # 获取视频时长
        duration = util.getVideoDuration(viewkey + '/' + viewkey + '.mp4')
        endPoint = duration - 15 - 24
        await util.segVideo(viewkey + '/' + viewkey + '.mp4', viewkey + '/' + 'seg_' + viewkey + '.mp4',
                            end=str(endPoint))


async def handle91(event, viewkey, viewkey_url):
    try:
        videoinfo = await page91.getVideoInfo91(viewkey_url)
        msg1 = await event.client.send_message(event.chat_id,
                                               '真实视频地址:' + videoinfo.realM3u8 + ' ,正在下载中... ,请不要一次性发送大量链接,被发现后会被封禁! ! !')
        title = videoinfo.title
        if '.mp4' in videoinfo.realM3u8:
            await  util.run(videoinfo.realM3u8, viewkey)
        else:
            try:
                await util.download91(videoinfo.realM3u8, viewkey)
            except ValueError:
                await event.reply(
                    '该视频高清版转码未完成,请等待转码完成后再发送链接,转码完成一般在视频发布1小时后')
                return
        # 截图
        await util.imgCoverFromFile(viewkey + '/' + viewkey + '.mp4', viewkey + '/' + viewkey + '.jpg')
        segstr = await util.seg(title)

        is_seg = '付费' in titles[i]
        await cut_video91(is_seg, viewkey)


        msg = await event.reply(
            '视频下载完成，正在上传。。。如果长时间没收到视频，请重新发送链接')
        # 发送视频
        message = await event.client.send_file(event.chat_id,
                                               viewkey + '/' + 'seg_' + viewkey + '.mp4' if is_seg else viewkey + '/' + viewkey + '.mp4',
                                               supports_streaming=True,
                                               thumb=viewkey + '/' + viewkey + '.jpg',
                                               caption=captionTemplate % (
                                                   title, videoinfo.scCount, '#' + videoinfo.author, segstr),
                                               reply_to=event.id,
                                               )
        await msg.delete()
        await msg1.delete()
        await saveToredis(viewkey, message.id, message.peer_id.user_id)

        print(str(datetime.datetime.now()) + ':' + title + ' 发送成功')
    finally:
        shutil.rmtree(viewkey, ignore_errors=True)


# 首页视频下载发送
async def page91DownIndex():
    urls, titles, authors, scCounts = await page91.page91Index()
    # print(urls)
    for i in range(len(urls)):
        url = urls[i]
        params = parse.parse_qs(parse.urlparse(url).query)
        viewkey = params['viewkey'][0]

        try:
            videoinfo = await page91.getVideoInfo91(url)

            # 下载视频
            await util.download91(videoinfo.realM3u8, viewkey)
        except:
            print('转码失败')
            shutil.rmtree(viewkey, ignore_errors=True)
            continue

        # 截图
        await util.imgCoverFromFile(viewkey + '/' + viewkey + '.mp4', viewkey + '/' + viewkey + '.jpg')
        segstr = await util.seg(titles[i])
        # 发送视频
        is_seg = '付费' in titles[i]
        await cut_video91(is_seg, viewkey)

        message = await bot.send_file(GROUP_ID,
                                      viewkey + '/' + 'seg_' + viewkey + '.mp4' if is_seg else viewkey + '/' + viewkey + '.mp4',
                                      supports_streaming=True,
                                      thumb=viewkey + '/' + viewkey + '.jpg',
                                      caption=captionTemplate % (
                                          titles[i], scCounts[i], '#' + authors[i].strip(), segstr),

                                      )
        shutil.rmtree(viewkey, ignore_errors=True)
        await saveToredis(viewkey, message.id, GROUP_ID)


async def main():
    scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(page91DownIndex, 'cron', hour=6, minute=50)
    scheduler.start()
    print('bot启动了!!!')


loop = asyncio.get_event_loop()
try:
    loop.create_task(main())
    loop.run_forever()
except KeyboardInterrupt:
    pass
