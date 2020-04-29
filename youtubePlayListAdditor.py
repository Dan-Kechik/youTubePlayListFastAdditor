# coding=utf-8

from __future__ import unicode_literals
import requests
import json
from lxml import etree
from datetime import datetime
import os
import traceback
import socket
import time


def getAPIkey():
    with open('APIkey.txt', "rt") as f:
        YOUTUBE_API_KEY = f.read()
    return YOUTUBE_API_KEY


def dateComparison(dateElement):
    return datetime.strptime(dateElement.get('publishedAt')[:-5], '%Y-%m-%dT%H:%M:%S')


def get_video_list(channelLink):
    """ Get channel's/playlist's upload videos| 50 limit"""

    try:
        YOUTUBE_URI_CHANNEL = 'https://www.googleapis.com/youtube/v3/search?key={}&channelId={}&part=snippet,id&order=date&maxResults=50'
        YOUTUBE_URI_LIST = 'https://www.googleapis.com/youtube/v3/playlistItems?key={}&playlistId={}&part=snippet&maxResults=50'
        if channelLink.find('/channel/') != -1: # https://ru.stackoverflow.com/questions/516312/python-youtube-api-v2-%d0%9f%d0%be%d0%bb%d1%83%d1%87%d0%b5%d0%bd%d0%b8%d1%8f-%d1%81%d0%bf%d0%b8%d1%81%d0%ba%d0%b0-%d0%b2%d0%b8%d0%b4%d0%b5%d0%be-%d0%bf%d0%be-%d0%b8%d0%bc%d0%b5%d0%bd%d0%b8-%d0%ba%d0%b0%d0%bd%d0%b0%d0%bb%d0%b0
            CHANNEL_ID = channelLink.rsplit('/', 1)[-1]
            FORMAT_YOUTUBE_URI = YOUTUBE_URI_CHANNEL.format(getAPIkey(), CHANNEL_ID)
        elif channelLink.find('playlist?') != -1: # https://a-panov.ru/youtube-api-v3-api-key/
            LIST_ID = channelLink.rsplit('playlist?list=', 1)[-1]
            FORMAT_YOUTUBE_URI = YOUTUBE_URI_LIST.format(getAPIkey(), LIST_ID)
        else:
            raise ValueError('Wrong request: youtube channels or playlists addresses are accepted.')

        content = requests.get(FORMAT_YOUTUBE_URI).text
        data = json.loads(content)

        video_list =[]
        keys = 'videoId', 'title', 'publishedAt', 'channelTitle', 'description', 'preview'

        for item in data.get('items'):
            try:
                videoId = item.get('id').get('videoId')
            except:
                videoId = item.get('snippet').get('resourceId').get('videoId')
            title = item.get('snippet').get('title')
            publishedAt = item.get('snippet').get('publishedAt')
            channelTitle = item.get('snippet').get('channelTitle')
            description = item.get('snippet').get('description')
            thumbnails = item.get('snippet').get('thumbnails')
            if thumbnails == None:
                continue
            preview = item.get('snippet').get('thumbnails').get('high').get('url')
            width = item.get('snippet').get('thumbnails').get('high').get('width')
            height = item.get('snippet').get('thumbnails').get('high').get('height')

            values = videoId, title, publishedAt, channelTitle, description, preview, width, height

            if id:
                video_item =dict(zip(keys, values))
                video_list.append(video_item)

        return video_list
    except Exception as e:
        print(traceback.format_exc())
        return {}


def updateDB():
    # Read old data.
    pathToDB = os.path.normpath(os.getcwd() + os.sep + 'Database.xml')
    try:
        databaseFile = etree.parse(pathToDB)
    except:
        pathToDBSample = os.path.normpath(os.getcwd() + os.sep + 'DatabaseSample.xml')
        databaseFile = etree.parse(pathToDBSample)
    databaseXml = databaseFile.getroot()
    # Get the common data.
    channels = databaseXml.xpath('//channels/channel/@link')
    playlists = databaseXml.xpath('//lists/list/@link')

    playlists.extend(channels)
    videos = []
    for ai in range(0, len(playlists), 1):
        currSource = str(playlists[ai])
        videos.extend(get_video_list(currSource))

    # ..Check existing videos..
    # Get an previously saved videos ID strings.
    oldVideos = databaseXml.xpath('//commonList/video/@videoId')
    for ai in range(0, len(oldVideos), 1):
        oldVideos[ai] = str(oldVideos[ai])
    # Find each new video ID in an old videos IDs list.
    foundVideos = []
    for ai in range(0, len(videos), 1):
        if not videos[ai].get('videoId') in oldVideos:
            foundVideos.append(videos[ai])

    # Sort by dates.
    foundVideos.sort(key=dateComparison, reverse=True)

    # Write full list to database.
    videoList = databaseXml.xpath('//commonList')[0]
    for viDict in foundVideos:
        videoElement = etree.Element('video')  # New video tag.
        videoList.append(videoElement)
        for keyz in viDict.keys():
            videoElement.set(keyz, viDict.get(keyz).encode('utf-8').decode())

    databaseFile.write(pathToDB, encoding='utf-8', xml_declaration=True)
    return databaseXml, len(foundVideos)

def sendDataBase(databaseXml):
    # Send database to socket.
    sock = socket.socket()
    ready2send = True
    try:
        sock.bind(('localhost', 9090))
        sock.listen(1)
        print('listen')
        conn, addr = sock.accept()
        print('connected:', addr)
    except ConnectionRefusedError:
        ready2send = False
    # Collect database to HTML tags.
    videoList = databaseXml.xpath('//commonList/video')
    attribs = ['title', 'publishedAt', 'channelTitle', 'description', 'preview'] #, 'width', 'height'
    videosBase = []
    [videosBase.append({}) for ai in range(0, len(videoList), 1)]
    for keyz in attribs:
        currAttrib = databaseXml.xpath('//commonList/video/@'+keyz)
        for ai in range(0, len(videoList), 1):
            videosBase[ai].update(dict.fromkeys([keyz], currAttrib[ai]))

    tableTag = ''
    for ai in range(0, len(videosBase), 1):
        tableTag = tableTag+'<tr>\n'
        pickString = '<img src="' + videosBase[ai].get('preview') + '">\n'
        # + '" width="' + videosBase[ai].get('width') + '" height="' + videosBase[ai].get('height')
        tableTag = tableTag + '<td>' + pickString + '</td>\n'
        for keyz in ['title', 'publishedAt', 'channelTitle', 'description']:
            tableTag = tableTag + '<td>' +  videosBase[ai].get(keyz) + '</td>\n'
        tableTag = tableTag + '</tr>\n'

    if ready2send:
        sock.send('hello, world!'.encode())
        # Receive delete date request.
        data = sock.recv(1024)
    #sock.close()


def main():
    while 1:
        (databaseXml, len_foundVideos) = updateDB()
        sendDataBase(databaseXml)
        time.sleep(3)


if __name__ == "__main__":
    main()
