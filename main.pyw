import os, sys
import pickle
import tkinter as tk
from tkinter import ttk

import PIL.ImageTk
import PIL.Image
import ttkthemes
from tkinter import filedialog
import pygame
import eyed3
import mutagen
from mutagen.mp3 import MP3
from pystray import MenuItem as item
import pystray
from PIL import Image
import tkinter as tk

SYSTEM_OS = sys.platform
print(SYSTEM_OS)
if SYSTEM_OS == 'win32':
    FS_SEP = '\\'
else:
    FS_SEP = '/'

PT_PLTS_PAGE = 0
PT_VIEW_PAGE = 1
PLS_INFO_FN = '._foton_audio_player_playlists_info'


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
        self.set_lib_fn = set_lib_fn
        with open(set_lib_fn) as file:
            txt = file.read()
        self.music_dirs = txt.split('\n')
        print(self.music_dirs)
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
        self.init_playlist_tab()
        self.init_settings_tab()
        self.style = ttkthemes.ThemedStyle()
        self.style.configure("H.TLabel", font=("JetBrains Mono", 17))
        self.last_text_play_lab1 = ''
        pygame.mixer.music.set_endevent(self.MUSIC_END_EVENT)
        self.subloop()
        self.music_queue = []
        self.tk_window.protocol('WM_DELETE_WINDOW', self.withdraw_window)
        self.tk_window.mainloop()

    def quit_window(self, icon, item):
        icon.stop()
        self.tk_window.destroy()

    def show_window(self, icon, item):
        icon.stop()
        self.tk_window.after(0, self.tk_window.deiconify)

    def withdraw_window(self):
        self.tk_window.withdraw()
        image = Image.open("image.ico")
        menu = (item('Выйти', self.quit_window), item('Открыть', self.show_window))
        icon = pystray.Icon("FotonPlayer(A)", image, "Foton", menu)
        icon.run()

    def init_play_tab(self, event=None):
        self.play_tab = ttk.Frame(self.notebook)
        self.play_tab.pack(fill='both', expand=True)
        self.notebook.add(self.play_tab, text='Музыка')
        self.play_lab1 = ttk.Label(self.play_tab, text='Название музыки', style="H.TLabel")
        self.play_lab1.pack()
        self.play_tab_text_of_sing = tk.Text(self.play_tab, background='#454544', foreground='white', borderwidth=0,
                                             font=('JetBrains mono', 9))
        self.play_tab_text_of_sing.pack(expand=1, fill='both')
        self.pt_l1_var = tk.Variable(value=[])
        self.play_tab_listbox1 = tk.Listbox(self.play_tab, background='#454544', foreground='white', borderwidth=0,
                                            font=('JetBrains mono', 13), listvariable=self.pt_l1_var)
        self.play_tab_listbox1.pack(fill='both', expand=True)
        self.play_frame1 = ttk.Frame(self.play_tab)
        self.play_frame1.pack(fill='x', expand=True)
        ttk.Button(self.play_frame1, text="Пауза", width=16, command=self.play_tab_pause).pack(side='left')
        ttk.Button(self.play_frame1, text="Следующий ->", width=16, command=self.play_tab_go_next).pack(side='left')
        ttk.Button(self.play_frame1, text='Удалить из очереди', command=self.play_tab_del_from_queue).pack(side='right')
        ttk.Button(self.play_frame1, text="Заново", command=self.play_tab_play, width=16).pack(side='right')
        ttk.Button(self.play_frame1, text='Очистить очередь', command=self.clear_play_queue).pack(side='right')
        ttk.Button(self.play_frame1, text="Возобновить", command=self.play_tab_unpause, width=16).pack()

        self.play_scroll_volume = ttk.Scrollbar(self.play_tab, orient='horizontal',
                                                command=self.set_volume_by_scrollbar)
        self.play_scroll_volume.pack(fill='x')
        self.play_scroll_volume.set(0.99, 1)

    def play_tab_del_from_queue(self, event=None):
        if len(self.music_queue) > 1:
            print(self.music_queue)
            ind = self.play_tab_listbox1.curselection()[0]
            if ind > 0:
                self.music_queue.pop(ind)
                self.play_tab_listbox1.delete(ind)
            else:
                self.play_tab_go_next()

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
        self.update_library()
        treeview_sort_column(self.tree_lib1, 0, False)
        treeview_sort_column(self.tree_lib1, 1, False)
        treeview_sort_column(self.tree_lib1, 2, False)
        treeview_sort_column(self.tree_lib1, 3, False)
        treeview_sort_column(self.tree_lib1, 4, False)
        self.tree_lib1.bind("<Double-1>", self.lib_play_music)

    def update_library(self, event=None):
        for row in self.tree_lib1.get_children():
            self.tree_lib1.delete(row)
        file_to_songs = open('file_with_songs.txt', 'w+', encoding='utf-8')

        for direct in self.music_dirs:
            for file in os.listdir(direct):
                if os.path.isfile(direct + FS_SEP + file):
                    if file.endswith(".mp3"):
                        af = eyed3.load(direct + FS_SEP + file)
                        tag = af.tag
                        self.tree_lib1.insert("", tk.END,
                                              values=(tag.title, tag.album, tag.artist,
                                                      str(int(MP3(direct + FS_SEP + file).info.length)),
                                                      direct + FS_SEP + file), )
                        file_to_songs.write(
                            f"{tag.title}@v@{tag.album}@v@{tag.artist}@v@{str(int(MP3(direct + FS_SEP + file).info.length))}\n")
        file_to_songs.close()

    def playsounds(self, filenames):
        print(filenames[0])
        try:
            txt = eyed3.load(filenames[0]).tag.lyrics[0].text
            self.play_tab_text_of_sing.delete('1.0', 'end')
            self.play_tab_text_of_sing.insert('end', txt)
        except:
            pass

        pygame.mixer.music.load(filenames[0])
        pygame.mixer.music.play()
        for i in range(len(filenames) - 1):
            pygame.mixer.music.queue(filenames[i + 1])

    def init_playlist_tab(self):
        self.playlist_tab_page = PT_VIEW_PAGE
        self.playlist_tab = ttk.Frame(self.notebook)
        self.playlist_tab.pack(expand=True, fill='both')
        self.notebook.add(self.playlist_tab, text="Плейлист")
        # ============== Playlists page ======================
        self.playlist_tab_playlists_page = ttk.Frame(self.playlist_tab)
        self.playlist_tab_playlists_page.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.playlist_tab_playlists_page_playlists_frame = ttk.Frame(self.playlist_tab_playlists_page)
        self.playlist_tab_playlists_page_playlists_frame.pack(expand=True, fill='both')
        columns = ("#1", "#2", "#3", '#4')
        self.playlist_treeview_playlists = ttk.Treeview(self.playlist_tab_playlists_page_playlists_frame,
                                                        show="headings", columns=columns)
        self.playlist_treeview_playlists.heading("#1", text="")
        self.playlist_treeview_playlists.heading("#2", text="Название")
        self.playlist_treeview_playlists.heading("#3", text="Число треков")
        self.playlist_treeview_playlists.heading("#4", text='ID')
        self.playlist_treeview_playlists_ysb = ttk.Scrollbar(self.playlist_tab_playlists_page_playlists_frame,
                                                             orient=tk.VERTICAL,
                                                             command=self.playlist_treeview_playlists.yview)
        self.playlist_treeview_playlists.configure(yscroll=self.playlist_treeview_playlists_ysb.set)
        self.playlist_treeview_playlists.pack(side='left', fill='both', expand=True)
        self.playlist_treeview_playlists_ysb.pack(side='right', fill='y')
        treeview_sort_column(self.playlist_treeview_playlists, 0, False)
        treeview_sort_column(self.playlist_treeview_playlists, 1, False)
        treeview_sort_column(self.playlist_treeview_playlists, 2, False)
        self.playlist_tab_playlists_page_manage_frame = ttk.Frame(self.playlist_tab_playlists_page)
        self.playlist_tab_playlists_page_manage_frame.pack(fill='x')
        self.playlist_tab_playlists_page_manage_frame_add_button = ttk.Button(
            self.playlist_tab_playlists_page_manage_frame, text='Добавить плейлист', command=self.add_playlist)
        self.playlist_tab_playlists_page_manage_frame_add_button.pack(side='left', fill='both', expand=1)
        self.playlist_tab_playlists_page_manage_frame_delete_button = ttk.Button(
            self.playlist_tab_playlists_page_manage_frame, text='Удалить плейлист')
        self.playlist_tab_playlists_page_manage_frame_delete_button.pack(side='right', fill='both', expand=1)
        self.playlist_treeview_playlists.bind("<Double-1>", self.playlist_tab_switch_page)
        self.playlist_tab_playlists_page.place_forget()
        # ============ view (playlist) page ==================
        self.playlist_tab_view_page = ttk.Frame(self.playlist_tab)
        self.playlist_tab_view_page.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.playlist_tab_view_page_songs_frame = ttk.Frame(self.playlist_tab_view_page)
        self.playlist_tab_view_page_songs_frame.pack(expand=True, fill='both')
        columns = ("#1", "#2", "#3", '#4', '#5')
        self.playlist_treeview_view = ttk.Treeview(self.playlist_tab_view_page_songs_frame,
                                                   show="headings", columns=columns)
        self.playlist_treeview_view.heading("#1", text="")
        self.playlist_treeview_view.heading("#2", text="Название")
        self.playlist_treeview_view.heading("#3", text="Альбом")
        self.playlist_treeview_view.heading("#4", text="Исполнитель")
        self.playlist_treeview_view.heading("#5", text="Файл    ")
        self.playlist_treeview_view_ysb = ttk.Scrollbar(self.playlist_tab_view_page_songs_frame,
                                                        orient=tk.VERTICAL,
                                                        command=self.playlist_treeview_view.yview)
        self.playlist_treeview_view.configure(yscroll=self.playlist_treeview_view_ysb.set)
        self.playlist_treeview_view.pack(side='left', fill='both', expand=True)
        self.playlist_treeview_view_ysb.pack(side='right', fill='y')
        treeview_sort_column(self.playlist_treeview_view, 0, False)
        treeview_sort_column(self.playlist_treeview_view, 1, False)
        treeview_sort_column(self.playlist_treeview_view, 2, False)
        self.playlist_tab_view_page_manage_frame = ttk.Frame(self.playlist_tab_view_page)
        self.playlist_tab_view_page_manage_frame.pack(fill='x')
        self.playlist_tab_view_page_manage_frame_add_button = ttk.Button(
            self.playlist_tab_view_page_manage_frame, text='Добавить песню')
        self.playlist_tab_view_page_manage_frame_add_button.pack(side='left', fill='both', expand=1)
        self.playlist_tab_view_page_manage_frame_delete_button = ttk.Button(
            self.playlist_tab_view_page_manage_frame, text='Удалить песню')
        self.playlist_tab_view_page_manage_frame_delete_button.pack(side='right', fill='both', expand=1)
        self.playlist_tab_switch_page()

    def playlist_tab_switch_page(self, event=None):
        if self.playlist_tab_page == PT_PLTS_PAGE:
            self.playlist_tab_page = PT_VIEW_PAGE
            self.playlist_tab_playlists_page.place_forget()
            self.playlist_tab_view_page.place(relx=0, rely=0, relwidth=1, relheight=1)
        else:
            self.playlist_tab_page = PT_PLTS_PAGE
            self.playlist_tab_view_page.place_forget()
            self.playlist_tab_playlists_page.place(relx=0, rely=0, relwidth=1, relheight=1)

    def pls_tab_reload_playlists(self, event=None):
        # id : ['name', bool_img, [fn_music1, fn_music2, ..]]
        for row in self.playlist_treeview_playlists.get_children():
            self.playlist_treeview_playlists.delete(row)
        try:
            with open(PLS_INFO_FN, 'rb') as f:
                data = pickle.load(f)
            if type(dict()) != type(data):
                raise TypeError()
            for key in data.keys():
                if type(list()) != type(data[key]):
                    raise TypeError()



        except:
            with open(PLS_INFO_FN, 'wb+') as f:
                pickle.dump(dict(), f)

    def add_playlist(self):
        self.top = tk.Toplevel(self.tk_window)
        self.top_frame = ttk.Frame(self.top)
        self.top_frame.pack(fill='both', expand=True)
        self.image_filename_for_playlist_new = ''
        self.top_img_lbl = ttk.Label(self.top_frame, text='*Изображение*')
        self.top_img_lbl.pack(fill='both', expand=True)
        ttk.Button(self.top_frame, text='Выбрать изображение...', command=self.top_choice_image_for_playlist).pack(
            fill='both', expand=True)
        self.top_entry = ttk.Entry(self.top_frame)
        self.top_entry.pack(fill='both', expand=True)
        ttk.Label(self.top_frame, text='Название').pack(fill='both', expand=True)
        ttk.Button(self.top_frame, text='Добавить').pack(fill='both', expand=True)

    def top_choice_image_for_playlist(self):
        self.image_filename_for_playlist_new = filedialog.askopenfilename()
        print(self.image_filename_for_playlist_new)
        if not self.image_filename_for_playlist_new:
            self.image_filename_for_playlist_new = ''
        else:
            try:
                self.img = PIL.ImageTk.PhotoImage(
                    PIL.Image.open(self.image_filename_for_playlist_new).resize((200, 200), Image.Resampling.LANCZOS))
                self.top_img_lbl.config(image=self.img, compound='image')
            except Exception as err:
                print(err)
                self.image_filename_for_playlist_new = ''
        self.top.wm_transient(self.tk_window)

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
                    self.play_lab1.config(
                        text=f"{self.music_queue[0][0]} - {self.music_queue[0][1]} - {self.music_queue[0][2]}")
                    self.play_music_display_queue()
        self.tk_window.after(100, self.subloop)

    def init_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text='Настройки')
        self.set_tab_frame1 = ttk.Frame(self.settings_tab)
        ttk.Label(self.set_tab_frame1, text='Тема').pack(side='left', padx=10, pady=10)
        self.combo_theme_set = ttk.Combobox(self.set_tab_frame1)
        self.combo_theme_set['values'] = self.all_themes
        self.combo_theme_set.pack(side='left', padx=10, pady=10)
        self.combo_theme_set.set(self.tk_window.current_theme)
        self.combo_theme_set.bind("<<ComboboxSelected>>", self.combo_theme_set_bind_function)
        ttk.Button(self.set_tab_frame1, text='-', command=self.delete_music_lib).pack(side='right', padx=10, pady=10)
        ttk.Button(self.set_tab_frame1, text='+', command=self.add_music_lib).pack(side='right', padx=10, pady=10)
        ttk.Label(self.set_tab_frame1, text='Библиотека:').pack(side='right', padx=10, pady=10)
        self.set_tab_frame1.pack(fill='x')

        self.settings_tab_tree_with_library = ttk.Treeview(self.settings_tab)
        self.settings_tab_tree_with_library = ttk.Treeview(self.settings_tab)
        self.treeset2ysb = ttk.Scrollbar(self.settings_tab, orient=tk.VERTICAL,
                                         command=self.settings_tab_tree_with_library.yview)
        self.settings_tab_tree_with_library.configure(yscroll=self.treeset2ysb.set)
        self.settings_tab_tree_with_library.pack(side='left', fill='both', expand=True)
        self.treeset2ysb.pack(side='right', fill='y')
        self.set_music_dirs_update()

    def set_music_dirs_update(self, event=None):
        for row in self.settings_tab_tree_with_library.get_children():
            self.settings_tab_tree_with_library.delete(row)
        for music_dir in self.music_dirs:
            print(music_dir)
            self.settings_tab_tree_with_library.insert("", tk.END,
                                                       text=music_dir)

    def add_music_lib(self, event=None):
        s = filedialog.askdirectory()
        if True:
            self.music_dirs.append(s)
            print(s)
            with open(self.set_lib_fn, 'w+') as file:
                file.write('\n'.join(self.music_dirs))
            self.update_library()
        self.set_music_dirs_update()

    def delete_music_lib(self, event=None):
        fns = []
        for selection in self.settings_tab_tree_with_library.selection():
            item = self.settings_tab_tree_with_library.item(selection)
            fn = item['text']
            fns.append(fn)
        self.music_dirs.remove(fns[0])
        with open(self.set_lib_fn, 'w+') as file:
            file.write('\n'.join(self.music_dirs))
        self.set_music_dirs_update()

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
    App(set_theme_fn=SET_THEME_FN, set_lib_fn=SET_LIB_FN)
