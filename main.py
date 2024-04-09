# MYAP - Minimalistic Youtube Audio Player
# Supports not only youtube
import yt_dlp
import os
import pygame
import customtkinter
import tomli
import tomli_w
import time
import requests
import time
import platform
from pypresence import Presence
from mutagen.mp3 import MP3
from tkinter import *
from threading import Thread
from pathlib import Path
from datetime import datetime
from time import sleep
version = "v1.3.1"
song_start_epoch = 0
song_end_epoch = 0
music_pos_seconds = 0
music_length = 0
paused = False
inprogress = False
repeat_track = False
run_presence = False
format = "mp3"
title = "Nothing"
author = "None"
regex_title = ""
cover_link = "https://user-images.githubusercontent.com/64737924/234092116-d079857b-37ab-4837-85c2-d3f27b6ea96b.png"
playlist_queue = []
queue_pos = 0
whole_config = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
is_rich_presence = whole_config["enable_rich_presence"]
files_stale_after = whole_config["delete_files_after"]
all_files = tomli.loads(Path("files.toml").read_text(encoding="utf-8"))["files"]
hide_console = whole_config["show_console"]
audio_loudness = whole_config["audio_loudness"]
check_for_updates = whole_config["check_for_updates"]
ffmpeg_location = whole_config["ffmpeg_location"]

if platform.system() == "Windows":
    import win32.lib.win32con as win32con
    import win32gui
    if not hide_console:
        the_program_to_hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

def presence_loop():
    global title
    global author
    global song_end_epoch
    global song_start_epoch
    while run_presence:
        if inprogress:
            if not paused:
                RPC.update(details=title, state=author, large_image=cover_link, large_text=title, start=int(song_start_epoch),end=int(song_end_epoch))
            else:
                RPC.update(details=title, state=author, large_image=cover_link, large_text=title)
        else:
            RPC.update(details="Listening to", state=title, large_image=cover_link, large_text="MYAP")
        sleep(1)

if is_rich_presence:
    try:
        RPC = Presence("1060563956806205491",pipe=0)
        RPC.connect()
        run_presence = True
        p_l = Thread(target=presence_loop)
        p_l.start()
    except:
        print("[MYAP] Discord not found")

print("[MYAP] "+str(all_files))

files_to_remove = []
for file in range(len(all_files)):
    try:
        last_access_time = os.path.getatime("downloaded/"+all_files[file])
        today = time.localtime()
        last_access_time = time.localtime(last_access_time)
        today = time.strftime('%Y/%m/%d %H:%M:%S', today)
        last_access_time = time.strftime('%Y/%m/%d %H:%M:%S', last_access_time)
        today = datetime.strptime(today, "%Y/%m/%d %H:%M:%S")
        last_access_time = datetime.strptime(last_access_time, "%Y/%m/%d %H:%M:%S")
        print("[MYAP] "+str(last_access_time))
        print("[MYAP] "+str(today))
        difference = (today-last_access_time).days
        print("[MYAP] Difference " + str(difference))
        if difference >= files_stale_after:
            os.remove("downloaded/"+all_files[file])
            files_to_remove.append(all_files[file])
    except FileNotFoundError:
        print("[MYAP] File " + all_files[file] + " not found. Removing from the list")
        all_files.remove(all_files[file-file])
for file in range(len(files_to_remove)):
    all_files.remove(all_files[file-file])
files_to_remove = []
with open("files.toml", mode="wb") as fp:
    print("[MYAP] "+str(dict(files = all_files)))
    tomli_w.dump(dict(files = all_files), fp)

def get_formated_time(time_in_seconds):
    minutes = time_in_seconds / 60
    seconds = time_in_seconds % 60
    if seconds < 10:
        formated = str(int(minutes)) + ":0" + str(int(seconds))
    else:
        formated = str(int(minutes)) + ":" + str(int(seconds))
    return formated

def check_music():
    global music_pos_seconds
    global inprogress
    global title
    global playlist_queue
    global queue_pos
    global cover_link
    global song_start_epoch
    global song_end_epoch
    for event in pygame.event.get():
        if event.type == MUSIC_END:
            print("[MYAP] Playback stopped")
            slider.set(0)
            music_pos_seconds = 0
            inprogress = False
            if repeat_track:
                print("[MYAP] Repeating")
                play_button.configure(text="||")
                if len(playlist_queue) > 0 and queue_pos == len(playlist_queue):
                    queue_pos = 0
                    m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                    m_p.start()
                elif len(playlist_queue) > 0:
                    if len(playlist_queue) > 0:
                        queue_pos += 1
                    if len(playlist_queue) > 0 and not queue_pos >= len(playlist_queue):
                        m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                        m_p.start()
                    if queue_pos >= len(playlist_queue):
                        queue_pos = 0
                        m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                        m_p.start()
                else:
                    p_a = Thread(target=play)
                    p_a.start()
                    song_start_epoch = time.time()
                    song_end_epoch = song_start_epoch + music_length
            else:
                if len(playlist_queue) > 0:
                    queue_pos += 1
                if len(playlist_queue) > 0 and not queue_pos >= len(playlist_queue):
                    m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                    m_p.start()
                else:
                    playlist_queue = []
                    queue_pos = 0
                    pygame.mixer.music.unload()
                    root.title("Playing: Nothing - MYAP")
                    time_total.configure(text=get_formated_time(0))
                    time_into.configure(text=get_formated_time(0))
                    slider.configure(from_=0, to=1, number_of_steps=1)
                    play_button.configure(text=">")
                    title = "Nothing"
                    cover_link = "https://user-images.githubusercontent.com/64737924/234092116-d079857b-37ab-4837-85c2-d3f27b6ea96b.png"
    root.after(100,check_music)

def slider_seek(value):
    global song_end_epoch
    global song_start_epoch
    global music_pos_seconds
    global music_length
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.play(start=value)
        music_pos_seconds = value
        time_into.configure(text=get_formated_time(music_pos_seconds))
        slider.set(value)
        song_start_epoch = time.time()
        song_end_epoch = song_start_epoch + (music_length - music_pos_seconds)

def slider_volume(value):
    global audio_loudness
    pygame.mixer.music.set_volume(value)
    audio_loudness = value

def p_updater():
    global inprogress
    global music_pos_seconds
    while pygame.mixer.music.get_busy() and inprogress:
        time_into.configure(text=get_formated_time((pygame.mixer.music.get_pos()/1000)+music_pos_seconds))
        slider.set((pygame.mixer.music.get_pos()/1000)+music_pos_seconds)
        sleep(1)

def play():
    global inprogress
    inprogress = True
    root.title("Playing: " + title + " - MYAP")
    pygame.mixer.music.load('./downloaded/'+regex_title)
    pygame.mixer.music.play()
    slider.set(0)
    p_u = Thread(target=p_updater)
    p_u.start()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

downloading = False
def progress(d):
    global downloading
    global progress_bar
    global slider
    if not downloading:
        progress_bar = customtkinter.CTkProgressBar(master=root)
        progress_bar.place(relx=0.7,rely=0.35,anchor=CENTER)
        slider.place_forget()
        downloading = True
    if d["status"] == "finished":
        downloading = False
        progress_bar.place_forget()
        slider.place(relx=0.7,rely=0.35,anchor=CENTER)
    if d["status"] == "downloading":
        p = d["_percent_str"]
        p = p.replace("%","")
        p = p.replace("\x1b[0;94m","")
        p = p.replace("\x1b[0m","")
        progress_bar.set(float(p)/100)

def pre_play(link):
    global title
    global video_id
    global music_pos_seconds
    global all_files
    global playlist_queue
    global queue_pos
    global cover_link
    global regex_title
    global author
    global song_start_epoch
    global song_end_epoch
    global music_length
    fnfe = False
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'ignoreerrors': True,
        'extract_flat': True,
        'restrictfilenames': True,
        'progress_hooks': [progress],
        'noplaylist': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio','preferredcodec': format,},
            {'key': 'SponsorBlock'},
            {'key': 'ModifyChapters', 'remove_sponsor_segments': ['sponsor', 'selfpromo', 'interaction']}
        ],
    }
    if ffmpeg_location != "":
        ydl_opts['ffmpeg_location'] = ffmpeg_location
    if link == " ":
        dialog = customtkinter.CTkInputDialog(text="Paste in url", title="MYAP")
        dialog.iconbitmap("icon.ico")
        input = dialog.get_input()
    else:
        input = link
    if input != "" or input != None:
        try:
            if link == " ":
                input.index("https://")
            else:
                print("[MYAP] Skipping")
        except ValueError:
            print("[MYAP] Provided string is not a valid url")
        except AttributeError:
            print("[MYAP] Dialog window has been closed")
        else:
            try:
                input.index("playlist?")
            except ValueError:
                root.title("Fetching audio - MYAP")
                video_id = ""
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(input, download=False)
                    try:
                        title = ydl.sanitize_info(info)["title"]
                        author = ydl.sanitize_info(info)["uploader"]
                        regex_title = ydl.prepare_filename(info)
                        regex_title = regex_title.replace(".m4a",".mp3")
                        video_id = ydl.sanitize_info(info)["id"]
                    except TypeError:
                        print("[MYAP] There was an error with " + regex_title + ". The site may not be supported")
                        title = "Nothing"
                        root.title("Playing: Nothing - MYAP")
                    else:
                        try:
                            input.index("youtu")
                        except ValueError:
                            cover_link = "https://raw.githubusercontent.com/PouekDEV/MYAP/main/icon.png"
                        else:
                            cover_link = "https://i.ytimg.com/vi/"+video_id+"/hq720.jpg"
                        if not os.path.exists("downloaded/"+regex_title):
                            root.title("Downloading: " + title + " - MYAP")
                            ydl.download(input)
                            try:
                                os.replace(regex_title,"downloaded/"+regex_title)
                            except FileNotFoundError:
                                fnfe = True
                                for file in os.listdir("./"):
                                    if file.endswith(".mp3"):
                                        os.remove(file)
                                print("[MYAP] There was an error with " + regex_title + ". File probably has some unusual signs")
                                title = "Nothing"
                                cover_link = "https://user-images.githubusercontent.com/64737924/234092116-d079857b-37ab-4837-85c2-d3f27b6ea96b.png"
                                root.title("Playing: Nothing - MYAP")
                                if len(playlist_queue) > 0:
                                    queue_pos += 1
                                    m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                                    m_p.start()
                            else:
                                all_files.append(regex_title)
                                with open("files.toml", mode="wb") as fp:
                                    print(str(dict(files = all_files)))
                                    tomli_w.dump(dict(files = all_files), fp)
                        else:
                            print("[MYAP] File exists")
                        if not fnfe:
                            mf = MP3("downloaded/"+regex_title)
                            music_length = mf.info.length
                            song_start_epoch = time.time()
                            song_end_epoch = song_start_epoch + mf.info.length
                            slider.configure(from_=0,to=mf.info.length,number_of_steps=mf.info.length*10)
                            play_button.configure(text="||")
                            time_total.configure(text=get_formated_time(mf.info.length))
                            p_a = Thread(target=play)
                            p_a.start()
                            print("[MYAP] Done processing url & audio file(s)")
            else:
                ydl_opts = {
                    'ignoreerrors': True,
                    'extract_flat': True,
                    'skip_download': True,
                }
                root.title("Downloading playlist data - MYAP")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(input, download=False)
                for i in range(len(ydl.sanitize_info(info)["entries"])):
                    try:
                        print("[MYAP] Adding this id to playlist: "+str(ydl.sanitize_info(info)["entries"][i]["id"]))
                    except TypeError:
                        print("[MYAP] TypeError. Probably this video is private")
                    else:
                        playlist_queue.append(str(ydl.sanitize_info(info)["entries"][i]["id"]))
                print("[MYAP] Playlist queue: "+str(playlist_queue))
                m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                m_p.start()
    else:
        print("[MYAP] Provided string is not a valid url")

def stop_p():
    global paused
    global inprogress
    global music_pos_seconds
    global title
    global playlist_queue
    global queue_pos
    global cover_link
    if repeat_track:
        set_repeat()
    if len(playlist_queue) > 0:
        playlist_queue = []
        queue_pos = 0
    paused = False
    inprogress = False
    title = "Nothing"
    cover_link = "https://user-images.githubusercontent.com/64737924/234092116-d079857b-37ab-4837-85c2-d3f27b6ea96b.png"
    music_pos_seconds = 0
    pygame.mixer.music.stop()

def set_repeat():
    global repeat_track
    if not repeat_track:
        repeat_track = True
        repeat_button.configure(text="⥁")
    else:
        repeat_track = False
        repeat_button.configure(text="→")

def play_b():
    global paused
    global inprogress
    global song_start_epoch
    global song_end_epoch
    global music_length
    global music_pos_seconds
    if inprogress:
        if not paused:
            paused = True
            play_button.configure(text=">")
            pygame.mixer.music.pause()
        else:
            paused = False
            play_button.configure(text="||")
            song_start_epoch = time.time()
            song_end_epoch = (song_start_epoch + (music_length - music_pos_seconds))-2
            pygame.mixer.music.unpause()
            p_u = Thread(target=p_updater)
            p_u.start()
    else:
        m_p = Thread(target=pre_play,args=" ")
        m_p.start()

pygame.init()
MUSIC_END = pygame.USEREVENT+1
pygame.mixer.music.set_endevent(MUSIC_END)
customtkinter.set_default_color_theme(whole_config["theme"])
customtkinter.set_appearance_mode(whole_config["appearance"]) 
root = customtkinter.CTk()
root.geometry("500x100")
root.title("Playing: Nothing - MYAP")
# Buttons
play_button = customtkinter.CTkButton(master=root,text=">",font=("Courier", 44),command=play_b, width=60,height=60)
play_button.place(relx=0.07,rely=0.5,anchor=CENTER)
stop_button = customtkinter.CTkButton(master=root,text="□",font=("Courier", 44),command=stop_p, width=60,height=60)
stop_button.place(relx=0.2,rely=0.5,anchor=CENTER)
repeat_button = customtkinter.CTkButton(master=root,text="→",font=("Courier", 44),command=set_repeat, width=60,height=60)
repeat_button.place(relx=0.33,rely=0.5,anchor=CENTER)
# Time labels and progress slider
time_into = customtkinter.CTkLabel(master=root, text="0:00")
time_into.place(relx=0.45,rely=0.35,anchor=CENTER)
time_total = customtkinter.CTkLabel(master=root, text="0:00")
time_total.place(relx=0.94,rely=0.35,anchor=CENTER)
slider = customtkinter.CTkSlider(master=root,from_=0, to=1, number_of_steps=1, command=slider_seek)
slider.place(relx=0.7,rely=0.35,anchor=CENTER)
slider.set(0)
# Audio
speaker_emoji = customtkinter.CTkLabel(master=root, text="🔊",font=("Courier", 20))
speaker_emoji.place(relx=0.45,rely=0.6,anchor=CENTER)
slider_v = customtkinter.CTkSlider(master=root,from_=0, to=1, number_of_steps=1000, command=slider_volume)
slider_v.place(relx=0.7,rely=0.6,anchor=CENTER)
slider_v.set(audio_loudness)
pygame.mixer.music.set_volume(audio_loudness)
check_music()

def new_version():
    os.system("start https://github.com/PouekDEV/MYAP/releases/latest")
    window.destroy()

if check_for_updates:
    response = requests.get("https://api.github.com/repos/PouekDEV/MYAP/releases/latest")
    if response.json()["name"] != version:
        print("[MYAP] A new version is available")
        window = customtkinter.CTkToplevel()
        window.title("A new version is available!")
        window.resizable(0,0)
        window.iconbitmap("icon.ico")
        window.geometry("300x100")
        info = customtkinter.CTkLabel(master=window, text="A new version is available!")
        info.place(relx=0.5, rely=0.2, anchor=CENTER)
        v_name = customtkinter.CTkLabel(master=window, text=response.json()["name"])
        v_name.place(relx=0.5, rely=0.5, anchor=CENTER)
        github = customtkinter.CTkButton(master=window,text="Download",command=new_version, width=60,height=20)
        github.place(relx=0.5, rely=0.8,anchor=CENTER)
    else:
        print("[MYAP] MYAP is up to date")

def close_program():
    global run_presence
    global whole_config
    whole_config["audio_loudness"] = audio_loudness
    with open("config.toml", mode="wb") as fp:
        tomli_w.dump(whole_config, fp)
    print("[MYAP] Quitting")
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.quit()
    if is_rich_presence:
        RPC.clear()
        RPC.close()
        run_presence = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_program)
root.resizable(0,0)
root.iconbitmap("icon.ico")
print("[MYAP] Initializing")
root.mainloop()