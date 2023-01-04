# MYAP - Minimalistic Youtube Audio Player
# Supports not only youtube
# https://www.youtube.com/watch?v=mUPlzggNRoE
# TODO:
# - Add better way of adding or retrieving audio timestamp
# - Add json file that keeps track of audio files last used dates and then after a certain amount of time deletes them
# - Add support for YouTube playlists
from time import sleep
import yt_dlp
import shutil
import os
import pygame
from mutagen.mp3 import MP3
from tkinter import *
from threading import Thread
import customtkinter

music_pos_seconds = 0
paused = False
inprogress = False
repeat_track = False
format = "mp3"

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
    for event in pygame.event.get():
        if event.type == MUSIC_END:
            print("[MYAP] Playback stopped")
            slider.set(0)
            music_pos_seconds = 0
            inprogress = False
            if repeat_track:
                print("[MYAP] Repeating in 3 seconds")
                sleep(3)
                play_button.configure(text="||")
                p_a = Thread(target=play)
                p_a.start()
            else:
                pygame.mixer.music.unload()
                root.title("Playing: Nothing - MYAP")
                time_total.configure(text=get_formated_time(0))
                time_into.configure(text=get_formated_time(0))
                slider.configure(from_=0, to=1, number_of_steps=1)
                play_button.configure(text=">")
    root.after(100,check_music)

def slider_seek(value):
    global music_pos_seconds
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.play(start=value)
        music_pos_seconds = value
        time_into.configure(text=get_formated_time(music_pos_seconds))
        slider.set(value)

def p_updater():
    global inprogress
    global music_pos_seconds
    if music_pos_seconds > 0:
        music_pos_seconds -= 1
    while pygame.mixer.music.get_busy() and inprogress:
        music_pos_seconds += 1
        time_into.configure(text=get_formated_time(music_pos_seconds))
        slider.set(music_pos_seconds)
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

def pre_play():
    global title
    global video_id
    global music_pos_seconds
    dialog = customtkinter.CTkInputDialog(text="Paste in url", title="MYAP")
    input = dialog.get_input()
    if input != "" or input != None:
        try:
            input.index("https://")
        except ValueError:
            print("[MYAP] Provided string is not a valid url")
        else:
            try:
                input.index("playlist?")
            except ValueError:
                root.title("Fetching audio - MYAP")
                URLS = input
                title = ""
                video_id = ""
                ydl_opts = {
                    'format': 'm4a/bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format,
                    }]
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(URLS, download=False)
                    title = ydl.sanitize_info(info)["title"]
                    video_id = ydl.sanitize_info(info)["id"]
                    if not os.path.exists("downloaded/"+title+" ["+ video_id +"]."+format):
                        root.title("Downloading: " + title + " - MYAP")
                        error_code = ydl.download(URLS)
                        shutil.move(title+" ["+ video_id +"]."+format,"downloaded/"+title+" ["+ video_id +"]."+format)
                    else:
                        print("[MYAP] File exists")
                mf = MP3("downloaded/"+title+" ["+ video_id +"]."+format)
                slider.configure(from_=0,to=mf.info.length,number_of_steps=mf.info.length*10)
                play_button.configure(text="||")
                time_total.configure(text=get_formated_time(mf.info.length))
                p_a = Thread(target=play)
                p_a.start()
                print("[MYAP] Done processing url & audio file(s)")
            else:
                print("[MYAP] Unsupported url. Playlist detected")
                root.title("Playing: Nothing - MYAP")
    else:
        print("[MYAP] Provided string is not a valid url")

def stop_p():
    global paused
    global inprogress
    global music_pos_seconds
    if repeat_track:
        set_repeat()
    paused = False
    inprogress = False
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
        m_p = Thread(target=pre_play)
        m_p.start()

pygame.init()
MUSIC_END = pygame.USEREVENT+1
pygame.mixer.music.set_endevent(MUSIC_END)
customtkinter.set_default_color_theme("green")
root = customtkinter.CTk()
root.geometry("500x100")
root.title("Playing: Nothing - MYAP")
play_button = customtkinter.CTkButton(master=root,text=">",font=("Courier", 44),command=play_b, width=60,height=60)
play_button.place(relx=0.07,rely=0.5,anchor=CENTER)
stop_button = customtkinter.CTkButton(master=root,text="□",font=("Courier", 44),command=stop_p, width=60,height=60)
stop_button.place(relx=0.2,rely=0.5,anchor=CENTER)
repeat_button = customtkinter.CTkButton(master=root,text="→",font=("Courier", 44),command=set_repeat, width=60,height=60)
repeat_button.place(relx=0.33,rely=0.5,anchor=CENTER)
time_into = customtkinter.CTkLabel(master=root, text="0:00")
time_into.place(relx=0.45,rely=0.5,anchor=CENTER)
time_total = customtkinter.CTkLabel(master=root, text="0:00")
time_total.place(relx=0.94,rely=0.5,anchor=CENTER)
slider = customtkinter.CTkSlider(master=root,from_=0, to=1, number_of_steps=1, command=slider_seek)
slider.place(relx=0.7,rely=0.5,anchor=CENTER)
slider.set(0)
check_music()

def close_program():
    print("[MYAP] Quitting")
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.quit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_program)
root.resizable(0,0)
root.iconbitmap("icon.ico")
print("[MYAP] Initializing")
root.mainloop()