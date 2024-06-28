import customtkinter
from datetime import datetime
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth
import time
import lyricsgenius
import syncedlyrics

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

def binarySearch(lyricsDict, progSecs):
   keyList = list(lyricsDict.keys())
   low, high = 0, len(keyList) - 1

   while low <= high:
      mid = (low + high) // 2
      midKey = keyList[mid]
      midSecs = converttoSec(lyricsDict[midKey]['minute'], lyricsDict[midKey]['second'])

      if midSecs == progSecs:
         return mid
      elif midSecs < progSecs:
         low = mid + 1
      else:
         high = mid - 1

   return high  # high is the index of the last key whose time is less than or equal to progSecs

def changeLabelSL(prog_m, prog_s, lyricsDict):
   lyrics = ""
   progSecs = converttoSec(prog_m, prog_s)
   first_key = list(lyricsDict.keys())[0]
   if progSecs - converttoSec(lyricsDict[first_key]['minute'], lyricsDict[first_key]['second']) >= -3 and progSecs - converttoSec(lyricsDict[first_key]['minute'], lyricsDict[first_key]['second']) <= 0:
      lyrics = lyricsDict[first_key]['lyric']
   elif progSecs - converttoSec(lyricsDict[first_key]['minute'], lyricsDict[first_key]['second']) < -3:
      lyrics = "\n\n"
   else:
      index = binarySearch(lyricsDict, progSecs)
      lyrics = lyricsDict[index]["lyric"]

      if index < len(lyricsDict) -1:
         lyrics = lyrics + "\n\n" + lyricsDict[index + 1]["lyric"]
   topLyrLab.configure(text=lyrics, wraplength=topLyrLab.winfo_width() - 40)

def converttoSec(m, s):
    return int(m)*60 + int(s)

def converttoMinSec(sec):
    return sec//60, sec%60


def parseSLyrics(data):
   lyrics_dict = {}
   cleaned_data = [line for line in data.split("\n") if all(term not in line for term in ["length:", "re:", "ve:", "by:", "ve:", "length:", "-", 'au:', 'ti:', 'ar:', "al:", "re:"])]
   for idx, line in enumerate(cleaned_data):
      if line == '':
         continue
      parts = line.split("]")
      timestamp = parts[0][1:]

      minute = timestamp.split(":")[0]
      second = int(float(timestamp.split(":")[1]))
      frac_second = int(float(parts[0].split(".")[1]))
      lyric = parts[1].strip()

      nested_dict = {
         "timestamp" : timestamp,
         "minute": minute,
         "second": second,
         "frac_second": frac_second,
         "lyric": lyric
      }

      lyrics_dict[idx] = nested_dict
   return lyrics_dict

def gotSyncedLyrics(track, artist):
    try:
        return syncedlyrics.search(f"{track} {artist}") #how does 1 line affect errors?
    except:
        print("Synced Lyrics Failed")
        return None

def isCurrentlyPlaying(state):
    return state and 'item' in state

def getTrackInfo(cp):
    track = cp['item']
    track_name = track['name']
    artist = track['artists'][0]['name']
    return track, track_name, artist

def isNewSong(old_track, old_artist, track_name, artist):
    return old_track != track_name or old_artist != artist

def getSongProg(currently_playing):
    try:
        progress = currently_playing['progress_ms']
        prog_m, prog_s = divmod(progress // 1000, 60)
    except Exception as e:
        prog_m = prog_s = ""
        print("progress failure", e)
    try:
        duration = currently_playing['item']['duration_ms']
        dur_m, dur_s = divmod(duration // 1000, 60)
    except Exception as e:
        dur_m =  dur_s = ""
        print("progress failure", e)
    return prog_m, prog_s, dur_m, dur_s

def frameSetup():
    fonttype = "Aharoni"
    global app
    app = customtkinter.CTk()
    app.geometry("600x500")

    global dateLabel, songLabel, progLabel, topLyrLab, botLyrLab
    dateLabel = customtkinter.CTkLabel(
        app,
        text="",
        fg_color="transparent",
        font=(fonttype, 30, "bold"),
        padx=10,
        pady=10,
        justify="center")
    dateLabel.grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="nesw")

    songLabel = customtkinter.CTkLabel(
        app,
        text="",
        fg_color="transparent",
        font=(fonttype, 30),
        padx=10,
        pady=10,
        justify="left")
    songLabel.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="nw")

    progLabel = customtkinter.CTkLabel(
        app,
        text="",
        fg_color="transparent",
        font=(fonttype, 25),
        padx=10,
        pady=10,
        justify="right")
    progLabel.grid(
        row=1,
        column=2,
        sticky="e")

    lyrFram = customtkinter.CTkFrame(
        app,
        width=600,
        height=300,
        fg_color="#123456",
        border_color="#aaa"
    )
    lyrFram.grid(
        row=3,
        column=0,
        columnspan=3,
        sticky="nsew")

    # Configure row and column weights for the frame
    lyrFram.grid_rowconfigure(0, weight=2)
    lyrFram.grid_columnconfigure(0, weight=1)
    empLab1 = customtkinter.CTkLabel(
        lyrFram,
        text="",
        font=(fonttype, 40),
        fg_color="transparent",
        bg_color="transparent")
    empLab1.grid(
        row=0,
        column=0,
        sticky="nsew")

    topLyrLab = customtkinter.CTkLabel(
        lyrFram,
        text="",
        fg_color="transparent",
        bg_color="transparent",
        font=(fonttype, 40),
        padx=10,
        pady=10,
        justify="center",
        wraplength=600)
    topLyrLab.grid(
        row=1,
        column=0,
        sticky="nsew")  # Adjust the sticky parameter for label4

    empLab2 = customtkinter.CTkLabel(
        lyrFram,
        text="\n\n",
        font=(fonttype, 80),
        fg_color="transparent",
        bg_color="transparent")
    empLab2.grid(
        row=2,
        column=0,
        sticky="nsew")

    playPauseButton = customtkinter.CTkButton(
        app,
        text="⏯",
        command=playPause,
        fg_color="transparent",
        font=(fonttype, 30),
    )
    playPauseButton.grid(row=2, column=1, sticky="nsew")
    app.grid_columnconfigure(1, weight=1)

    nextButton = customtkinter.CTkButton(
        app,
        text="⏭",
        command=nextTrack,
        fg_color="transparent",
        font=(fonttype, 30)
    )
    nextButton.grid(row=2, column=2, sticky="ew")
    app.grid_columnconfigure(2, weight=1)

    prevButton = customtkinter.CTkButton(
        app,
        text="⏮",
        command=prevTrack,
        fg_color="transparent",
        font=(fonttype, 30),
    )
    prevButton.grid(row=2, column=0, sticky="we")
    app.grid_columnconfigure(0, weight=1)



def getTime():
    dateLabel.configure(text=datetime.today().strftime("%A | %B %d | %I:%M:%S%p"))
    dateLabel.after(800, getTime)

def setupSpotify():
   cid = '<ADD CID>'
   secret = '<ADD secret>'
   scope = "user-read-playback-state user-modify-playback-state"
   username = 'cohja00'  # Replace with your Spotify username
   redirect_uri = 'https://www.yahoo.com'  # Replace with your redirect URI

   sp_oauth = SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=redirect_uri, scope=scope)
   token_info = sp_oauth.get_cached_token()
   print(token_info)
   if not token_info or sp_oauth.is_token_expired(token_info):
      print("AAAAA")
      token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])


   return spotipy.Spotify(auth=token_info['access_token'])

def getGeniusLyrics(track_name, artist):
    song = lyricsgenius.Genius('<ADD Key>').search_song(track_name, artist)
    if song:
        return song.lyrics.split("Lyrics", 1)[1]
    else:
        return None

def changeLabelGen(prog_m, prog_s, dur_m, dur_s, lyrics):
   def getLyrics(lyrics):
      topLyrLab.configure(text=lyrics, wraplength=topLyrLab.winfo_width())

   lyrics_split = lyrics.split("\n")
   lyrics_split = [line for line in lyrics_split if line.strip() != '']
   lyrics_split = [line for line in lyrics_split if '[' not in line and ']' not in line]

   lines_fit = 5

   appx_line = len(lyrics_split)*converttoSec(prog_m, prog_s)//converttoSec(dur_m, dur_s)

   if appx_line < lines_fit - 5:
      getLyrics('\n'.join(lyrics_split[0:lines_fit]))
   elif appx_line > len(lyrics_split) - lines_fit:
      getLyrics('\n'.join(lyrics_split[len(lyrics_split) - lines_fit: len(lyrics_split)]))
   else:
      getLyrics('\n'.join(lyrics_split[appx_line - lines_fit//2 : appx_line + lines_fit//2 +1]))
   return None

def getSongDataAndLyrics(old_track, old_artist, usingSL, passlyrics):
   global lyrics
   try:
      state = sp.current_playback()
      if isCurrentlyPlaying(state):
         track, track_name, artist = getTrackInfo(state)
         title = track_name + " - " + artist
         if len(title) > 27:
            title = track_name[:18] + "... - " + artist[:7]
            if len(artist) > 7:
               title += "..."
         songLabel.configure(text = title)
         prog_m, prog_s, dur_m, dur_s = getSongProg(state)
         progLabel.configure(text=f"{prog_m}:{prog_s:02}/{dur_m}:{dur_s:02}")
         if isNewSong(old_track, old_artist, track_name, artist):
            lyrics = gotSyncedLyrics(track_name, artist)
            if lyrics is not None and lyrics != "" and lyrics != " ":
               topLyrLab.configure(text="Using Synced Lyrics...")
               lyrics = parseSLyrics(lyrics)
               print("SL")
               usingSL = True
            else:
               topLyrLab.configure(text="Using Genius Lyrics...")
               lyrics = getGeniusLyrics(track_name, artist)
               usingSL = False
               print("GENIUS LYRICS")

         if usingSL:
            changeLabelSL(prog_m, prog_s, lyrics)
         else:
            changeLabelGen(prog_m, prog_s, dur_m, dur_s, lyrics)
         app.after(100, getSongDataAndLyrics,track_name, artist, usingSL, passlyrics)
      else:
         topLyrLab.configure(text="Music Not Playing")
         songLabel.configure(text="No Artist/Title")
         progLabel.configure(text="X:XX/X:XX")
         app.after(10000, getSongDataAndLyrics,"", "", usingSL, passlyrics)
   except spotipy.SpotifyException as e:
      print(e)
      print(datetime.now())
      app.mainloop()
      setupSpotify()
      getSongDataAndLyrics("", "", usingSL, passlyrics)
def playPause():
    # Implement the logic to toggle between play and pause
    state = sp.current_playback()
    if state and 'is_playing' in state:
        if state['is_playing']:
            sp.pause_playback()
        else:
            sp.start_playback()

def nextTrack():
    sp.next_track()

def prevTrack():
    sp.previous_track()

def main():

   global sp
   global usingSL
   try:
      usingSL = True
      sp = setupSpotify()
      frameSetup()
      getTime()
      getSongDataAndLyrics("", "", None, None)
      app.mainloop()
   except Exception as e:
      print("error", e)
      main()


main()
