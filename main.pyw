import os
import tkinter as tk
from tkinter import ttk
import ttkthemes
from tkinter import filedialog
import pygame
import eyed3
import mutagen
from mutagen.mp3 import MP3


def treeview_sort_column(tv, col, reverse):
    l = [(int(tv.set(k, col)) if col == 3 else tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)

    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # reverse sort next time
    tv.heading(col, command=lambda: \
        treeview_sort_column(tv, col, not reverse))


class App(ttk.Frame):
    def __init__(self, title='Foton Audio Player', set_lib_fn=None, set_theme_fn=None):
        self.MUSIC_END_EVENT = pygame.USEREVENT + 1
        pygame.init()
        self.set_theme_fn = set_theme_fn
        with open(set_lib_fn) as file:
            txt = file.read()
        self.music_dirs = txt.split('\n')
        self.tk_window = ttkthemes.ThemedTk()
        super().__init__(self.tk_window)
        self.pack(fill='both', expand=True)
        with open(set_theme_fn) as file:
            self.tk_window.set_theme(file.read())
        self.all_themes = self.tk_window.themes
        print(self.all_themes)
        try:
            self.all_themes.remove('breeze')
        except:
            pass
        self.tk_window.title(title)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        self.init_play_tab()
        self.init_library_tab()
        self.init_settings_tab()
        self.style = ttkthemes.ThemedStyle()
        self.style.configure("H.TLabel", font=("JetBrains Mono", 17))
        self.last_text_play_lab1 = ''
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        self.subloop()
        self.music_queue = []
        self.tk_window.mainloop()

    def init_play_tab(self, event=None):
        self.play_tab = ttk.Frame(self.notebook)
        self.play_tab.pack(fill='both', expand=True)
        self.notebook.add(self.play_tab, text='Музыка')
        self.play_lab1 = ttk.Label(self.play_tab, text='Название музыки', style="H.TLabel")
        self.play_lab1.pack()
        self.pt_l1_var = tk.Variable(value=[])
        self.play_tab_listbox1 = tk.Listbox(self.play_tab, background='#454544', foreground='white', borderwidth=0, font=('JetBrains mono', 13), listvariable=self.pt_l1_var)
        self.play_tab_listbox1.pack(fill='both', expand=True)
        self.play_frame1 = ttk.Frame(self.play_tab)
        self.play_frame1.pack(fill='x', expand=True)
        ttk.Button(self.play_frame1, text="Пауза", width=16, command=self.play_tab_pause).pack(side='left')
        ttk.Button(self.play_frame1, text="Следующий ->", width=16, command=self.play_tab_go_next).pack(side='left')
        ttk.Button(self.play_frame1, text="Заново", command=self.play_tab_play, width=16).pack(side='right')
        ttk.Button(self.play_frame1, text='Очистить очередь', command=self.clear_play_queue).pack(side='right')
        ttk.Button(self.play_frame1, text="Возобновить", command=self.play_tab_unpause, width=16).pack()

        self.play_scroll_volume = ttk.Scrollbar(self.play_tab, orient='horizontal', command=self.set_volume_by_scrollbar)
        self.play_scroll_volume.pack(fill='x')
        self.play_scroll_volume.set(0.99, 1)

    def play_tab_go_next(self, event=None):
        self.last_text_play_lab1 = self.play_lab1['text']
        self.play_lab1.config(text="Ничего пока не играет")
        if len(self.music_queue) > 1:
            self.music_queue.pop(0)
            self.playsounds(self.music_queue[0][-1])
            self.play_lab1.config(
                text=f"{self.music_queue[0][0]} - {self.music_queue[0][1]} - {self.music_queue[0][2]}")
            self.play_music_display_queue()
        else:
            self.play_tab_play()

    def set_volume_by_scrollbar(self, _, moveto, **kwargs):
        pygame.mixer.music.set_volume(min(1, max(0, float(moveto))))
        self.play_scroll_volume.set(float(moveto), float(moveto) + .01)

    def clear_play_queue(self, event=None):
        self.music_queue = []
        pygame.mixer.music.unload()
        self.play_music_display_queue()
        self.play_lab1.config(text=' Ничего пока не играет ')

    def play_tab_pause(self, event=None):
        pygame.mixer.music.pause()

    def play_tab_unpause(self, event=None):
        pygame.mixer.music.unpause()

    def play_tab_play(self, event=None):
        pygame.mixer.music.play()
        if self.play_lab1['text'] == 'Ничего пока не играет':
            self.play_lab1.config(text=self.last_text_play_lab1)

    def init_library_tab(self, event=None):
        self.lib_tab = ttk.Frame(self.notebook)
        self.lib_tab.pack(fill='both', expand=True)
        self.notebook.add(self.lib_tab, text='Библиотека')
        columns = ("#1", "#2", "#3", "#4", "#5")
        self.tree_lib1 = ttk.Treeview(self.lib_tab, show="headings", columns=columns)
        self.tree_lib1.heading("#1", text="Название")
        self.tree_lib1.heading("#2", text="Альбом")
        self.tree_lib1.heading("#3", text="Группа")
        self.tree_lib1.heading("#4", text="Время, сек")
        self.tree_lib1.heading("#5", text="Файл")
        self.treelib1ysb = ttk.Scrollbar(self.lib_tab, orient=tk.VERTICAL, command=self.tree_lib1.yview)
        self.tree_lib1.configure(yscroll=self.treelib1ysb.set)
        self.tree_lib1.pack(side='left', fill='both', expand=True)
        self.treelib1ysb.pack(side='right', fill='y')
        for direct in self.music_dirs:
            for file in os.listdir(direct):
                if os.path.isfile(direct + '\\' + file):
                    if file.endswith(".mp3"):
                        af = eyed3.load(direct + '\\' + file)
                        tag = af.tag
                        self.tree_lib1.insert("", tk.END,
                                              values=(tag.title, tag.album, tag.artist,
                                                      str(int(MP3(direct + '\\' + file).info.length)),
                                                      direct + '\\' + file), )
        treeview_sort_column(self.tree_lib1, 0, False)
        treeview_sort_column(self.tree_lib1, 1, False)
        treeview_sort_column(self.tree_lib1, 2, False)
        treeview_sort_column(self.tree_lib1, 3, False)
        treeview_sort_column(self.tree_lib1, 4, False)
        self.tree_lib1.bind("<Double-1>", self.lib_play_music)

    def playsounds(self, filenames):
        print(filenames[0])
        pygame.mixer.music.load(filenames[0])
        pygame.mixer.music.play()
        for i in range(len(filenames) - 1):
            pygame.mixer.music.queue(filenames[i + 1])

    def add_music_to_queue(self, metainfo):
        self.music_queue.append(metainfo)

    def play_music_display_queue(self, event=None):
        values = []
        for song in self.music_queue:
            values.append(f'{song[0]} - {song[1]} - {song[2]}')
        self.pt_l1_var.set(values)

    def lib_play_music(self, event=None):
        fns = []
        for selection in self.tree_lib1.selection():
            item = self.tree_lib1.item(selection)
            _, _2, _3, _4, fn = item["values"][0:5]
            fns.append(fn)
        print(self.music_queue)
        if len(self.music_queue) == 0:
            self.playsounds(fns)
            self.play_lab1.config(text=f"{_} - {_2} - {_3}")
        self.add_music_to_queue([_, _2, _3, _4, fns])
        self.play_music_display_queue()

    def subloop(self, event=None):
        for event in pygame.event.get():
            if event.type == self.MUSIC_END_EVENT:
                self.last_text_play_lab1 = self.play_lab1['text']
                self.play_lab1.config(text="Ничего пока не играет")
                if len(self.music_queue) > 1:
                    self.music_queue.pop(0)
                    self.playsounds(self.music_queue[0][-1])
                    self.play_lab1.config(text=f"{self.music_queue[0][0]} - {self.music_queue[0][1]} - {self.music_queue[0][2]}")
                    self.play_music_display_queue()
        self.tk_window.after(100, self.subloop)

    def init_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text='Настройки')
        self.combo_theme_set = ttk.Combobox(self.settings_tab)
        self.combo_theme_set['values'] = self.all_themes
        self.combo_theme_set.grid(row=0, column=1)
        self.combo_theme_set.set(self.tk_window.current_theme)
        self.combo_theme_set.bind("<<ComboboxSelected>>", self.combo_theme_set_bind_function)
        ttk.Label(self.settings_tab, text='Тема').grid(row=0, column=0)

    def combo_theme_set_bind_function(self, event=None):
        self.tk_window.set_theme(self.combo_theme_set.get())
        with open(self.set_theme_fn, 'w+') as file:
            file.write(self.combo_theme_set.get())



if __name__ == "__main__":
    SET_THEME_FN = '._foton_audio_player_settings_theme'
    SET_LIB_FN = '._foton_audio_player_settings_library'
    if not os.path.exists(SET_LIB_FN):
        w = tk.Tk()
        fns = []
        tk.Button(w, text='Добавить папку. Если больше музыки нет - закройте это окно',
                  command=lambda e=None: fns.append(filedialog.askdirectory())).pack()
        w.resizable(False, False)
        w.mainloop()
        with open(SET_LIB_FN, 'w+') as file:
            file.write('\n'.join(fns))
    if not os.path.exists(SET_THEME_FN):
        with open(SET_THEME_FN, 'w+') as file:
            file.write('black')
    App(set_theme_fn=SET_THEME_FN, set_lib_fn = SET_LIB_FN)
