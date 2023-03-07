import os
import tkinter as tk
from tkinter import ttk
import ttkthemes
from tkinter import filedialog
import pygame
import eyed3

def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # reverse sort next time
    tv.heading(col, command=lambda: \
               treeview_sort_column(tv, col, not reverse))

class App(ttk.Frame):
    def __init__(self, title='Foton Audio Player'):
        pygame.init()
        with open('._foton_audio_player_settings') as file:
            txt = file.read()
        self.music_dirs = txt.split('\n')
        self.tk_window = ttkthemes.ThemedTk()
        super().__init__(self.tk_window)
        self.pack(fill='both', expand=True)
        self.tk_window.set_theme('black')
        self.tk_window.title(title)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        self.init_play_tab()
        self.init_library_tab()
        self.tk_window.mainloop()
    def init_play_tab(self, event=None):
        self.play_tab = ttk.Frame(self.notebook)
        self.play_tab.pack(fill='both', expand=True)
        self.notebook.add(self.play_tab, text='Музыка')
        self.play_lab1 = ttk.Label(self.play_tab, text='Название музыки')
        self.play_lab1.pack()
        self.play_frame1 = ttk.Frame(self.play_tab)
        self.play_frame1.pack(fill='x', expand=True)
        ttk.Button(self.play_frame1, text="Пауза", width=16, command=self.play_tab_pause).pack(side='left')
        ttk.Button(self.play_frame1, text="Заново", command=self.play_tab_play, width=16).pack(side='right')
        ttk.Button(self.play_frame1, text="Возобновить", command=self.play_tab_unpause, width=16).pack()

    def play_tab_pause(self, event=None):
        pygame.mixer.music.pause()
    def play_tab_unpause(self, event=None):
        pygame.mixer.music.unpause()
    def play_tab_play(self, event=None):
        pygame.mixer.music.play(0)
    def init_library_tab(self, event=None):
        self.lib_tab = ttk.Frame(self.notebook)
        self.lib_tab.pack(fill='both', expand=True)
        self.notebook.add(self.lib_tab, text='Библиотека')
        columns = ("#1", "#2", "#3", "#4")
        self.tree_lib1 = ttk.Treeview(self.lib_tab, show="headings", columns=columns)
        self.tree_lib1.heading("#1", text="Название")
        self.tree_lib1.heading("#2", text="Альбом")
        self.tree_lib1.heading("#3", text="Группа")
        self.tree_lib1.heading("#4", text="Файл")
        self.treelib1ysb = ttk.Scrollbar(self.lib_tab, orient=tk.VERTICAL, command=self.tree_lib1.yview)
        self.tree_lib1.configure(yscroll=self.treelib1ysb.set)
        self.tree_lib1.pack(side='left', fill='both', expand=True)
        self.treelib1ysb.pack(side='right',fill='y')
        for direct in self.music_dirs:
            print(direct)
            for file in os.listdir(direct):
                if os.path.isfile(direct+'\\'+file):
                    print(file)
                    if file.endswith(".mp3"):
                        af = eyed3.load(direct+'\\'+file)
                        tag = af.tag
                        print("\n".join(dir(tag)))
                        self.tree_lib1.insert("", tk.END, values=(tag.title, tag.album, tag.artist,direct+'\\'+file), )
        treeview_sort_column(self.tree_lib1, 0, False)
        treeview_sort_column(self.tree_lib1, 1, False)
        treeview_sort_column(self.tree_lib1, 2, False)
        treeview_sort_column(self.tree_lib1, 3, False)
        self.tree_lib1.bind("<Double-1>", self.lib_play_music)
    def playsounds(self, filenames):
        pygame.mixer.music.load(filenames[0])
        pygame.mixer.music.play()
        for i in range(len(filenames)-1):
            pygame.mixer.music.queue(filenames[i+1])

    def lib_play_music(self, event=None):
        fns = []
        for selection in self.tree_lib1.selection():
            item = self.tree_lib1.item(selection)
            _, _2, _3, fn = item["values"][0:4]
            fns.append(fn)
        self.playsounds(fns)
        text = ''
        for fn in fns:
            af = eyed3.load(fn)
            tag = af.tag
            print("\n".join(dir(tag)))
            text+=f"{tag.title} - {tag.album} - {tag.artist}\n"
        self.play_lab1.config(text=text)

if __name__ == "__main__":
    if not os.path.exists("._foton_audio_player_settings"):
        w = tk.Tk()
        fns = []
        tk.Button(w, text='Добавить папку. Если больше музыки нет - закройте это окно', command=lambda e=None: fns.append(filedialog.askdirectory()) ).pack()
        w.resizable(False, False)
        w.mainloop()
        with open("._foton_audio_player_settings", 'w+') as file:
            file.write('\n'.join(fns))
    App()