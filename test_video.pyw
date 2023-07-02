import os
import tkinter
import tkinter as tk
from tkinter import filedialog
import cv2
import PIL.Image, PIL.ImageTk
import time
import pygame
import moviepy.editor as mp
from moviepy.editor import VideoFileClip
import threading

from contextlib import redirect_stdout, redirect_stderr
import io

CONSOLE_OUTPUT = io.StringIO()


def converttomp3(mp4file, mp3file):
    video = VideoFileClip(mp4file)
    # получаем аудиодорожку
    audio = video.audio
    # сохраняем аудио файл
    audio.write_audiofile(mp3file)
    # уничтожаем объекты
    # что бы не было ошибок
    audio.close()
    video.close()
class App:
    def __init__(self, window, window_title, video_source=0):
        self.window = tkinter.Tk()
        pygame.init()
        self.window.title(video_source)
        self.video_source = video_source
        self.need_myloop=True

        l = tk.Label(self.window, text='wait')
        l.pack()
        t = threading.Thread(target=self.myloop)
        t.start()
        # open video source (by default this will try to open the computer webcam)
        while self.need_myloop:
            self.window.update()
            self.window.update_idletasks()
            x = CONSOLE_OUTPUT.getvalue().split('\r')[-1].split('%')[0].split(' ')[-1]
            l.config(text="Предобработка видео: "+x+'%')
        self.vid = MyVideoCapture(self.video_source)
        pygame.mixer.music.load('audio.mp3')
        pygame.mixer.music.set_volume(1)
        # Create a canvas that can fit the above video source size
        self.canvas=tkinter.Label(window)
        #self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.pack(fill='both', expand='True')
        self.canvas.bind('<Button-1>', self.pause_bind)


        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = int(1/self.vid.vid.get(cv2.CAP_PROP_FPS)*1000)
        self.last_d = 0
        self.i=0
        self.start = time.perf_counter()
        self.need_myloop = False
        self.pause=False
        t.join()
        l.destroy()
        self.update()
        pygame.mixer.music.play()
        self.window.geometry(f"{int(self.vid.width)}x{int(self.vid.height)}")
        self.window.resizable(False, False)
        self.pause=True
        pygame.mixer.music.pause()
        self.window.mainloop()
        pygame.quit()

    def pause_bind(self, event=None):
        if self.pause:
            pygame.mixer.music.unpause()
            #self.window.overrideredirect(True)
        else:
            pygame.mixer.music.pause()
            #self.window.overrideredirect(False)
        self.pause = not self.pause
    def myloop(self, event=None):
        with redirect_stdout(CONSOLE_OUTPUT),redirect_stderr(CONSOLE_OUTPUT):
            converttomp3(self.video_source, 'audio.mp3')
        self.need_myloop=False

    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            cv2.imwrite("frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    def update(self):
        # Get a frame from the video source
        if not self.pause:
            self.new_sec = self.vid.vid.get(cv2.CAP_PROP_POS_MSEC)
            pos = pygame.mixer.music.get_pos()
            ret, frame = self.vid.get_frame()


            if ret:
                self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
                self.canvas.config(image=self.photo)
               #self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

            d2= self.new_sec - pos
            self.delay = max(1, int((d2+self.last_d)/2))
            self.last_d = d2
        self.window.after(self.delay, self.update)


class MyVideoCapture:
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)

        # Get video source width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            return (ret, None)

     # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

# Create a window and pass it to the Application object
App(None, "Foton Video Player", filedialog.askopenfilename())
