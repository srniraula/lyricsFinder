import tkinter as tk
from tkinter import messagebox, scrolledtext
import lyricsgenius
from pynput import keyboard
import threading
import sys

# --- Configuration ---
# Replace with your actual Genius Client Access Token
GENIUS_ACCESS_TOKEN = "5tlYy1tVTleLKXCBA7x-y5C3JsPHaWumY8JOT0qNbYXex-f4jpxoRfSEQr6nevTc" 
HOTKEY_COMBINATION = '<ctrl>+<shift>+l' # Hotkey to trigger the popup

# --- Dark Theme Colors ---
BG_COLOR = "#2B2B2B"  # Dark background
FG_COLOR = "#E0E0E0"  # Light grey text
ENTRY_BG = "#3C3C3C"  # Slightly lighter dark for entry
ENTRY_FG = "#FFFFFF"  # White text for entry
BUTTON_BG = "#4A4A4A" # Darker button
BUTTON_FG = "#FFFFFF" # White text for button
HIGHLIGHT_COLOR = "#0078D7" # A blue highlight for focus

# --- Font Settings ---
INITIAL_FONT_SIZE = 10
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 24
FONT_FAMILY = "Helvetica" # You can change this to "Liberation Mono", "Noto Sans Mono", etc.

# --- Initialize Genius API ---
try:
    genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN, verbose=False)
    genius.skip_non_songs = True
    genius.excluded_terms = ["(Remix)", "(Live)"]
except Exception as e:
    print(f"Error initializing Genius API: {e}", file=sys.stderr)
    genius = None # Set to None to prevent further errors if token is bad

# --- Popup Window Class ---
class LyricsPopup:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Lyrics Finder")
        self.root.geometry("600x700") # Slightly taller to accommodate new entry
        self.root.attributes("-topmost", True)

        self.root.resizable(True, True) 
        self.root.minsize(400, 450)

        self.root.withdraw() # Hide the window initially

        self.root.configure(bg=BG_COLOR)

        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

        self.song_var = tk.StringVar() # Changed from search_var to song_var
        self.artist_var = tk.StringVar() # New StringVar for artist
        self.current_font_size = INITIAL_FONT_SIZE

        # Song name entry and label
        tk.Label(self.root, text="Song Name:", bg=BG_COLOR, fg=FG_COLOR, font=(FONT_FAMILY, 11, "bold")).pack(pady=5)
        self.song_entry = tk.Entry( # Changed from self.entry to self.song_entry
            self.root, 
            textvariable=self.song_var, 
            width=50, 
            bg=ENTRY_BG, 
            fg=ENTRY_FG, 
            insertbackground=FG_COLOR, 
            highlightbackground=HIGHLIGHT_COLOR, 
            highlightthickness=1, 
            font=(FONT_FAMILY, 12)
        )
        self.song_entry.pack(pady=5, padx=10, fill=tk.X)
        self.song_entry.bind("<Return>", self.fetch_lyrics)

        # Artist name entry and label (NEW)
        tk.Label(self.root, text="Artist Name (Optional):", bg=BG_COLOR, fg=FG_COLOR, font=(FONT_FAMILY, 11, "bold")).pack(pady=5)
        self.artist_entry = tk.Entry( # New entry for artist
            self.root, 
            textvariable=self.artist_var, 
            width=50, 
            bg=ENTRY_BG, 
            fg=ENTRY_FG, 
            insertbackground=FG_COLOR, 
            highlightbackground=HIGHLIGHT_COLOR, 
            highlightthickness=1, 
            font=(FONT_FAMILY, 12)
        )
        self.artist_entry.pack(pady=5, padx=10, fill=tk.X)
        self.artist_entry.bind("<Return>", self.fetch_lyrics)

        # Search button
        tk.Button(
            self.root, 
            text="Search", 
            command=self.fetch_lyrics, 
            bg=BUTTON_BG, 
            fg=BUTTON_FG, 
            relief=tk.FLAT, 
            activebackground=HIGHLIGHT_COLOR, 
            activeforeground=BUTTON_FG,
            font=(FONT_FAMILY, 11, "bold")
        ).pack(pady=5)

        # Lyrics display area
        self.lyrics_area = scrolledtext.ScrolledText(
            self.root, 
            wrap=tk.WORD, 
            width=60, 
            height=20, 
            font=(FONT_FAMILY, self.current_font_size), 
            bg=ENTRY_BG, 
            fg=FG_COLOR, 
            insertbackground=FG_COLOR,
            selectbackground=HIGHLIGHT_COLOR, 
            selectforeground=ENTRY_FG, 
            relief=tk.FLAT,
            highlightbackground=HIGHLIGHT_COLOR,
            highlightthickness=1
        )
        self.lyrics_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True) 
        self.lyrics_area.config(state=tk.DISABLED) 

        # Close button
        tk.Button(
            self.root, 
            text="Close", 
            command=self.hide_popup,
            bg=BUTTON_BG, 
            fg=BUTTON_FG, 
            relief=tk.FLAT, 
            activebackground=HIGHLIGHT_COLOR,
            activeforeground=BUTTON_FG,
            font=(FONT_FAMILY, 11, "bold")
        ).pack(pady=5)

        self.is_open = False 
        self.root.protocol("WM_DELETE_WINDOW", self.hide_popup)

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.root.geometry(f'+{x}+{y}')

    def show_popup(self):
        self.root.deiconify()
        self.root.lift()
        # This line makes the window stay on top.
        self.root.attributes("-topmost", True) 
        # Remove or comment out the next line to keep it always on top:
        # self.root.attributes("-topmost", False) # <-- REMOVE OR COMMENT THIS LINE
        self.song_entry.focus_set() 
        self.is_open = True
        self.song_var.set("")
        self.artist_var.set("")
        self.lyrics_area.config(state=tk.NORMAL)
        self.lyrics_area.delete('1.0', tk.END)
        self.lyrics_area.config(state=tk.DISABLED)


    def hide_popup(self):
        self.root.withdraw()
        self.is_open = False

    def fetch_lyrics(self, event=None):
        song_name = self.song_var.get().strip()
        artist_name = self.artist_var.get().strip() # Get artist name

        if not song_name:
            messagebox.showwarning("Input Error", "Please enter a song name.", parent=self.root)
            return

        if not genius:
            self.lyrics_area.config(state=tk.NORMAL)
            self.lyrics_area.delete('1.0', tk.END)
            self.lyrics_area.insert(tk.END, "Genius API not initialized. Please check your token and restart the application.")
            self.lyrics_area.config(state=tk.DISABLED)
            return

        self.lyrics_area.config(state=tk.NORMAL)
        self.lyrics_area.delete('1.0', tk.END)
        self.lyrics_area.insert(tk.END, "Searching for lyrics... Please wait.")
        self.lyrics_area.config(state=tk.DISABLED)

        # Pass both song_name and artist_name to the threaded function
        threading.Thread(target=self._fetch_lyrics_threaded, args=(song_name, artist_name)).start()

    def _fetch_lyrics_threaded(self, song_name, artist_name):
        try:
            # Use the 'artist' parameter in search_song for more specific results
            song = genius.search_song(title=song_name, artist=artist_name, get_full_info=False) 

            self.lyrics_area.config(state=tk.NORMAL)
            self.lyrics_area.delete('1.0', tk.END)
            if song and song.lyrics:
                self.lyrics_area.insert(tk.END, song.lyrics)
            else:
                self.lyrics_area.insert(tk.END, f"Lyrics not found for '{song_name}' by '{artist_name if artist_name else 'any artist'}'. Try a different spelling or include/remove artist name.")
            self.lyrics_area.config(state=tk.DISABLED)
        except Exception as e:
            self.lyrics_area.config(state=tk.NORMAL)
            self.lyrics_area.delete('1.0', tk.END)
            self.lyrics_area.insert(tk.END, f"An error occurred while fetching lyrics: {e}")
            self.lyrics_area.config(state=tk.DISABLED)

    def adjust_font_size(self, delta):
        """Adjusts the font size of the lyrics area."""
        new_size = self.current_font_size + delta
        if MIN_FONT_SIZE <= new_size <= MAX_FONT_SIZE:
            self.current_font_size = new_size
            self.lyrics_area.config(font=(FONT_FAMILY, self.current_font_size))
            # print(f"Font size adjusted to: {self.current_font_size}") # For debugging

# --- Hotkey Listener and Application Logic ---
app_root = None 
popup_instance = None
hotkey_listener = None
zoom_listener = None 

def create_and_run_popup():
    global popup_instance, app_root
    if popup_instance is None: 
        if app_root is None:
            app_root = tk.Tk()
            app_root.withdraw()
            app_root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
        popup_instance = LyricsPopup()

    app_root.after(0, popup_instance.show_popup) 

def on_hotkey_activated():
    if app_root:
        app_root.after(0, create_and_run_popup)

def on_zoom_in_activated():
    global popup_instance
    if popup_instance and popup_instance.is_open:
        app_root.after(0, lambda: popup_instance.adjust_font_size(1))

def on_zoom_out_activated():
    global popup_instance
    if popup_instance and popup_instance.is_open:
        app_root.after(0, lambda: popup_instance.adjust_font_size(-1))

def setup_hotkey_listener():
    global hotkey_listener, zoom_listener
    print(f"Listening for hotkey: {HOTKEY_COMBINATION}. Press Ctrl++ / Ctrl+- for zoom. Press Ctrl+C in terminal to exit.")

    hotkey_listener = keyboard.GlobalHotKeys({
        HOTKEY_COMBINATION: on_hotkey_activated
    })
    hotkey_listener.start()

    zoom_listener = keyboard.GlobalHotKeys({
        '<ctrl>+=': on_zoom_in_activated, # Ctrl + Plus (on US keyboard, '+' is usually Shift+=)
        '<ctrl>+<shift>+=': on_zoom_in_activated, # Alternative for Ctrl + Shift + Plus if '=' does not work
        '<ctrl>+-': on_zoom_out_activated,  # Ctrl + Minus
    })
    zoom_listener.start() 

    if app_root:
        app_root.mainloop() 
    else:
        try:
            hotkey_listener.join()
            zoom_listener.join() 
        except KeyboardInterrupt:
            print("\nExiting hotkey listeners...")
            hotkey_listener.stop()
            zoom_listener.stop()

if __name__ == "__main__":
    app_root = tk.Tk()
    app_root.withdraw()
    app_root.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

    setup_hotkey_listener()