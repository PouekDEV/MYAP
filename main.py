# MYAP - Minimalistic Youtube Audio Player
# Supports not only youtube
#TODO: The thing with the playlists and bad files y'know
import yt_dlp
import os
import pygame
import customtkinter
import tomli
import tomli_w
import time
import win32gui
import win32.lib.win32con as win32con
from pypresence import Presence
from mutagen.mp3 import MP3
from tkinter import *
from threading import Thread
from pathlib import Path
from time import sleep
from datetime import datetime

music_pos_seconds = 0
paused = False
inprogress = False
repeat_track = False
run_presence = False
format = "mp3"
title = "Nothing"
cover_link = "https://user-images.githubusercontent.com/64737924/210854929-b4f80382-71a6-4b03-9d41-c88b31b75bb3.png"
playlist_queue = []
queue_pos = 0
whole_config = tomli.loads(Path("config.toml").read_text(encoding="utf-8"))
is_rich_presence = whole_config["enable_rich_presence"]
files_stale_after = whole_config["delete_files_after"]
all_files = tomli.loads(Path("files.toml").read_text(encoding="utf-8"))["files"]
hide_console = whole_config["show_console"]
audio_loudness = whole_config["audio_loudness"]

if not hide_console:
    the_program_to_hide = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

def presence_loop():
    global title
    while run_presence:
        RPC.update(details="Listening to", state=title, large_image=cover_link)
        sleep(15)

if is_rich_presence:
    RPC = Presence("1060563956806205491",pipe=0)
    RPC.connect()
    run_presence = True
    p_l = Thread(target=presence_loop)
    p_l.start()

print("[MYAP] "+str(all_files))

for file in range(len(all_files)):
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
    if difference > files_stale_after:
        os.remove("downloaded/"+all_files[file])
        all_files.remove(file)
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
                    cover_link = "https://user-images.githubusercontent.com/64737924/210854929-b4f80382-71a6-4b03-9d41-c88b31b75bb3.png"
    root.after(100,check_music)

def slider_seek(value):
    global music_pos_seconds
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.play(start=value)
        music_pos_seconds = value
        time_into.configure(text=get_formated_time(music_pos_seconds))
        slider.set(value)

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
    pygame.mixer.music.load('./downloaded/'+title+' ['+ video_id +'].'+format)
    pygame.mixer.music.play()
    slider.set(0)
    p_u = Thread(target=p_updater)
    p_u.start()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def pre_play(link):
    global title
    global video_id
    global music_pos_seconds
    global all_files
    global playlist_queue
    global queue_pos
    global cover_link
    fnfe = False
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'ignoreerrors': True,
        'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format,
            }]
    }
    if link == " ":
        dialog = customtkinter.CTkInputDialog(text="Paste in url", title="MYAP")
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
                    title = ydl.sanitize_info(info)["title"]
                    video_id = ydl.sanitize_info(info)["id"]
                    cover_link = "https://i.ytimg.com/vi/"+video_id+"/hq720.jpg"
                    if not os.path.exists("downloaded/"+title+" ["+ video_id +"]."+format):
                        root.title("Downloading: " + title + " - MYAP")
                        error_code = ydl.download(input)
                        try:
                            os.replace(title+" ["+ video_id +"]."+format,"downloaded/"+title+" ["+ video_id +"]."+format)
                        except FileNotFoundError:
                            fnfe = True
                            for file in os.listdir("./"):
                                if file.endswith(".mp3"):
                                    os.remove(file)
                            print("[MYAP] There was an error with " + title + ". File probably has some unusual signs")
                            title = "Nothing"
                            cover_link = "https://user-images.githubusercontent.com/64737924/210854929-b4f80382-71a6-4b03-9d41-c88b31b75bb3.png"
                            root.title("Playing: Nothing - MYAP")
                            if len(playlist_queue) > 0:
                                queue_pos += 1
                                m_p = Thread(target=pre_play,args=(playlist_queue[queue_pos],))
                                m_p.start()
                        else:
                            all_files.append(title+" ["+ video_id +"]."+format)
                            with open("files.toml", mode="wb") as fp:
                                print(str(dict(files = all_files)))
                                tomli_w.dump(dict(files = all_files), fp)
                    else:
                        print("[MYAP] File exists")
                if not fnfe:
                    mf = MP3("downloaded/"+title+" ["+ video_id +"]."+format)
                    slider.configure(from_=0,to=mf.info.length,number_of_steps=mf.info.length*10)
                    play_button.configure(text="||")
                    time_total.configure(text=get_formated_time(mf.info.length))
                    p_a = Thread(target=play)
                    p_a.start()
                    print("[MYAP] Done processing url & audio file(s)")
            else:
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
    cover_link = "https://user-images.githubusercontent.com/64737924/210854929-b4f80382-71a6-4b03-9d41-c88b31b75bb3.png"
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
    if inprogress:
        if not paused:
            paused = True
            play_button.configure(text=">")
            pygame.mixer.music.pause()
        else:
            paused = False
            play_button.configure(text="||")
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