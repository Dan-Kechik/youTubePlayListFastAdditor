# coding=utf-8

from __future__ import unicode_literals
import requests
import json
from lxml import etree
from datetime import datetime
import os
import traceback
from convenientServer import echoServer
import copy
import warnings
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import webbrowser
import numpy as np

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
api_service_name = "youtube"
api_version = "v3"
CLIENT_SECRETS_FILE = "client_secret_apps.googleusercontent.com.json"  # OAuth data.
deployOAuthServ = True  # Server or console authentification
MAX_ELEMENTS_ON_PAGE = 150

def runAuth():
    # webbrowser.open_new_tab('')  # For convenience.
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes)
    if deployOAuthServ:
        credentials = flow.run_local_server()
    else:
        credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)
    return youtube

def sendVideo(youtube, playListID, videoID, position=0):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playListID,
                # "position": position,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": videoID
                }
            }
        }
    )
    try:
        response = request.execute()
        print(response)
        return (response, None)
    except Exception as e:
        print(traceback.format_exc())
        return (None, e)

def getAPIkey():
    with open('APIkey.txt', "rt") as f:
        YOUTUBE_API_KEY = f.read()
    return YOUTUBE_API_KEY


def dateComparison(dateElement):
    if type(dateElement) is tuple:
        currEl = dateElement[1]
    else:
        currEl = dateElement
    date = currEl.get('publishedAt').split('.')
    date = date[0].split('Z')
    return datetime.strptime(date[0], '%Y-%m-%dT%H:%M:%S')


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

        if not data.get('error') is None:
            warnings.warn("Error of data retrieving from youtube.", UserWarning)
            print(data)
            return []

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
            try:
                preview = item.get('snippet').get('thumbnails').get('high').get('url')
                width = item.get('snippet').get('thumbnails').get('high').get('width')
                height = item.get('snippet').get('thumbnails').get('high').get('height')
            except:  # Put in default "no thumblail" image.
                preview = 'https://i.ytimg.com/img/no_thumbnail.jpg'
                width = 200
                height = 100

            values = videoId, title, publishedAt, channelTitle, description, preview, width, height

            if id:
                video_item =dict(zip(keys, values))
                video_list.append(video_item)

        return video_list
    except Exception as e:
        print(traceback.format_exc())
        return []

def updateDB(delIndex=None):
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

    videoList = databaseXml.xpath('//commonList')[0]
    sortVideos(videoList, key=dateComparison, reverse=True)
    # Get the date of the latest saved video.
    latestDate = dateComparison(videoList[0])
    # Sort by dates.
    sortVideos(foundVideos, key=dateComparison, reverse=True)
    # foundVideos.sort(key=dateComparison, reverse=True)
    outdatedID = -1  # len(foundVideos)+1
    for currID, currVid in enumerate(foundVideos):
        currTime = dateComparison(currVid)
        if currTime < latestDate:
            break
        outdatedID = currID
    else:
        outdatedID = len(foundVideos)-1  # No outdated videos - take the whole list.
    if outdatedID < 0:
        foundVideos = []
    else:
        foundVideos = foundVideos[:outdatedID+1]

    # Get and sort previous version of  full data base for displaying on page.
    databaseXmlFull = copy.deepcopy(databaseXml)
    videoListFullOld = databaseXmlFull.xpath('//commonList')[0]
    sortVideos(videoListFullOld, key=dateComparison, reverse=False)
    # Write full list to database.
    if not delIndex is None:
        for ai in range(0, delIndex):
            videoList.remove(videoList[-1])
    for viDict in foundVideos:
        videoElement = etree.Element('video')  # New video tag.
        videoList.append(videoElement)
        for keyz in viDict.keys():
            videoElement.set(keyz, viDict.get(keyz).encode('utf-8').decode())
    # videoList.sort(key=dateComparison, reverse=False)
    sortVideos(videoList, key=dateComparison, reverse=False)

    databaseFile.write(pathToDB, encoding='utf-8', xml_declaration=True)
    return databaseXml, len(foundVideos), databaseXmlFull

def sendSelected(signedCheckNumber, databaseXmlFull):
    signedCheckNumber = signedCheckNumber.strip(',').split(',')  # Get numbers of selected for sending videos.
    videoList = databaseXmlFull.xpath('//commonList')[0]
    playListID = databaseXmlFull.xpath('//playListID')[0]
    playListID = playListID.get('value')
    youtube = runAuth()
    for ai in range(0, len(signedCheckNumber)):
        if signedCheckNumber[ai] == '':
            continue
        currentIndex = int(signedCheckNumber[ai])
        videoId = videoList[currentIndex].get('videoId')
        print(videoId)
        title = videoList[currentIndex].get('title')
        print(title)
        sendVideo(youtube, playListID, videoId)

def prepareDataBase(databaseXml):
    # Collect database to HTML tags.
    videoList = databaseXml.xpath('//commonList/video')
    attribs = ['title', 'publishedAt', 'channelTitle', 'description', 'preview'] #, 'width', 'height'
    videosBase = []
    num = min(MAX_ELEMENTS_ON_PAGE, len(videoList))  # Number of videos to add to prevent too high resources consumption.
    [videosBase.append({}) for ai in range(0, num, 1)]
    for keyz in attribs:
        currAttrib = databaseXml.xpath('//commonList/video/@'+keyz)
        for ai in range(0, num, 1):
            videosBase[ai].update(dict.fromkeys([keyz], currAttrib[ai]))

    tableTag = ''
    for ai in range(0, len(videosBase), 1):
        tableTag = tableTag+'<tr>\n'
        pickString = '<img src="' + videosBase[ai].get('preview') + '">\n'
        # + '" width="' + videosBase[ai].get('width') + '" height="' + videosBase[ai].get('height')
        checkString = f'<label><input type="checkbox" id="{ai}">Add</label>'  # onchange="checkAction("{ai}")
        tableTag = tableTag + '<td>' + checkString + '</td>\n'
        buttonString = f'<button onclick="sendAnswer(\'{ai}\')">Finish</button>'
        tableTag = tableTag + '<td>' + buttonString + '</td>\n'
        tableTag = tableTag + '<td>' + pickString + '</td>\n'
        for keyz in ['title', 'publishedAt', 'channelTitle', 'description']:
            tableTag = tableTag + '<td>' +  videosBase[ai].get(keyz) + '</td>\n'
        tableTag = tableTag + '</tr>\n'

    return tableTag

def getDatesList(videoList):
    dates = []
    for vid in videoList:
        dates.append(dateComparison(vid))
    return dates

def sortVideos(videoList, key=dateComparison, reverse=False):
    # Remove erroneous elements
    nonez = []
    for ai, vid in enumerate(videoList):
        if vid.get('publishedAt') is None:
            nonez.append(ai)
    for ai in nonez:
        videoList.remove(videoList[ai])
    # res = sorted(enumerate(videoList), key=key, reverse=reverse)
    # idxs = [i[0] for i in res]
    # replaceList(videoList, idxs)
    videoList[:] = sorted(videoList, key=key, reverse=reverse)
    # return idxs

def packToTuple(initialList):
    outList = []
    for ai in range(len(initialList)):
        outList.append(ai, initialList[ai])
    return outList

def replaceList(myList, ids):
    usedIdxs = np.array([])
    for ai in range(len(myList)):
        if np.any(usedIdxs == ai):
            continue
        currIdx = ids[ai]
        try:
            myList[ai], myList[currIdx] = myList[currIdx], myList[ai]
        except:
            print(ai)
        usedIdxs = np.hstack([usedIdxs, ai, currIdx])

def main():
    myDBserver = echoServer()
    myDBserver.updateTask(myDBserver.processRequests, 'serveToDatabase')
    pageFeedback = myDBserver.events['received']
    while 1:
        command = myDBserver.pop('fromClient')
        if not command is None:
            # Get all updated list if it's the page loading/updating request; update with clearing and update playlist otherwise.
            command = json.loads(command)
            if not command.get('name', '') == 'Grzegorz':
                warnings.warn("Some stranger trying to connect.", UserWarning)
                continue
            signedCheckNumber = command.get('signedCheckNumber', None)
            viewedButtonNum = command.get('viewedButtonNum', None)
            if not viewedButtonNum is None and not signedCheckNumber is None:
                (databaseXml, len_foundVideos, databaseXmlFull) = updateDB(int(viewedButtonNum))
                sendSelected(signedCheckNumber, databaseXmlFull)
            else:
                (databaseXml, len_foundVideos, databaseXmlFull) = updateDB()
                print(f'Obtained {len_foundVideos} videos.')
            # Send webpage updaating on load or viewed button click.
            pageText = prepareDataBase(databaseXml)
            myDBserver.push('toClient', pageText)
            # Join feedback queue.
            myQ = myDBserver.queue['fromClient']
            myQ.task_done()
        else:
            (databaseXml, len_foundVideos, databaseXmlFull) = updateDB()
            print(f'Obtained {len_foundVideos} videos.')
        pageFeedback.clear()
        pageFeedback.wait(timeout=3000)


if __name__ == "__main__":
    main()
