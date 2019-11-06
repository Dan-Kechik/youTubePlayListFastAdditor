# coding=utf-8

from __future__ import unicode_literals
import requests
import json
from lxml import etree
from xml.dom import minidom as MD
from datetime import datetime
import os

YOUTUBE_API_KEY = 'AIzaSyAnXtSOPb7O8vXmpCaTO76IfcAy-ZssO-c'

# Read sources from DB
channels = ['https://www.youtube.com/channel/UCFzJjgVicCtFxJ5B0P_ei8A'] # , 'https://www.youtube.com/channel/UC_IEcnNeHc_bwd92Ber-lew'
playlists = ['https://www.youtube.com/playlist?list=PLLHjKKyQ4OaSC1VyglWYcGtY5pwqX1wVv']


def dateComparison(dateElement):
    return datetime.strptime(dateElement.get('publishedAt')[:-5], '%Y-%m-%dT%H:%M:%S')


def get_video_list(channelLink):
    """ Get channel's/playlist's upload videos| 50 limit"""

    try:
        YOUTUBE_URI_CHANNEL = 'https://www.googleapis.com/youtube/v3/search?key={}&channelId={}&part=snippet,id&order=date&maxResults=50'
        YOUTUBE_URI_LIST = 'https://www.googleapis.com/youtube/v3/playlistItems?key={}&playlistId={}&part=snippet&maxResults=50'
        if channelLink.find('/channel/') != -1: # https://ru.stackoverflow.com/questions/516312/python-youtube-api-v2-%d0%9f%d0%be%d0%bb%d1%83%d1%87%d0%b5%d0%bd%d0%b8%d1%8f-%d1%81%d0%bf%d0%b8%d1%81%d0%ba%d0%b0-%d0%b2%d0%b8%d0%b4%d0%b5%d0%be-%d0%bf%d0%be-%d0%b8%d0%bc%d0%b5%d0%bd%d0%b8-%d0%ba%d0%b0%d0%bd%d0%b0%d0%bb%d0%b0
            CHANNEL_ID = channelLink.rsplit('/', 1)[-1]
            FORMAT_YOUTUBE_URI = YOUTUBE_URI_CHANNEL.format(YOUTUBE_API_KEY, CHANNEL_ID)
        elif channelLink.find('playlist?') != -1: # https://a-panov.ru/youtube-api-v3-api-key/
            LIST_ID = channelLink.rsplit('playlist?list=', 1)[-1]
            FORMAT_YOUTUBE_URI = YOUTUBE_URI_LIST.format(YOUTUBE_API_KEY, LIST_ID)
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
            preview = item.get('snippet').get('thumbnails').get('high').get('url')

            values = videoId, title, publishedAt, channelTitle, description, preview

            if id:
                video_item =dict(zip(keys, values))
                video_list.append(video_item)

        return video_list
    except:
        return {}


# Read old data.
pathToDB = os.path.normpath(os.getcwd() + os.sep + 'Database.xml')
try:
    databaseFile = etree.parse(pathToDB)
except:
    pathToDBSample = os.path.normpath(os.getcwd() + os.sep + 'DatabaseSample.xml')
    databaseFile = etree.parse(pathToDB)
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
        videoElement.set(keyz, viDict.get(keyz).encode('utf-8').decode())  # .encode('ascii','replace').decode()

databaseFile.write(pathToDB, encoding='utf-8', xml_declaration=True)
