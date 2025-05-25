import tkinter as tk
from tkinter import ttk, PhotoImage # Added PhotoImage
from tkinter import colorchooser
import webbrowser
import http.cookiejar
import urllib.request

class CustomBrowser:
      # Placeholder Base64 encoded icons
      ICON_GO_B64 = "R0lGODlhEAAQAPMAAP///wAAAMlcLq49O7xSO/////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAA8ALAAAAAAQABAAQAQzUMhJq70Yl9xQWHn9pGoD0gRFLHBL62FqEzR2q2bX4L8aL0MvRzO02bQ0QLIQEEDkAAA7"
      ICON_NEW_TAB_B64 = "R0lGODlhEAAQAPMAAP///wAAAMlcLq49O7xSO/////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAA8ALAAAAAAQABAAQAQzEMhJq70Yl9xQWHn9pGoD0gRFLHBL62FqEzR2q2bX4L8aL0MvRzO02bQ0QLIQEEDkAAA7"

      def __init__(self, root):
        self.root = root
        self.root.title("Customizable Browser")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0") # Set root background

        # Apply ttk styling
        style = ttk.Style(self.root)
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", background="#cccccc", foreground="#333333")
        style.configure("TButton", background="#cccccc", foreground="#333333", borderwidth=1)
        style.map("TButton", background=[('active', '#b0b0b0')])
        # For TEntry, fieldbackground is the editable area, background is the border area.
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#333333", background="#f0f0f0", borderwidth=1)

        # Create PhotoImage objects for icons
        try:
            self.go_icon = PhotoImage(data=CustomBrowser.ICON_GO_B64)
            self.new_tab_icon = PhotoImage(data=CustomBrowser.ICON_NEW_TAB_B64)
        except tk.TclError:
            # Placeholder icons might be invalid, use None if so
            self.go_icon = None 
            self.new_tab_icon = None
            print("Warning: Could not load icons from base64 data. Using text buttons/menu items.")

        # Cookie jar for basic cookie handling
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Add the first tab
        self.add_tab()

        # Create a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add settings menu
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label="Change Background Color", command=self.change_background_color)
        # Add "New Tab" with icon
        if self.new_tab_icon:
            settings_menu.add_command(label="New Tab", image=self.new_tab_icon, compound="left", command=self.add_tab)
        else:
            settings_menu.add_command(label="New Tab", command=self.add_tab) # Fallback if icon failed
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)

      def add_tab(self):
        """Add a new tab to the browser."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="New Tab")

        # URL bar
        url_frame = ttk.Frame(frame)
        url_frame.pack(fill="x", padx=5, pady=5)

        url_entry = ttk.Entry(url_frame)
        url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Update "Go" button with icon
        if self.go_icon:
            go_button = ttk.Button(url_frame, text="Go", image=self.go_icon, compound="left", command=lambda: self.open_url(url_entry.get(), frame))
        else:
            go_button = ttk.Button(url_frame, text="Go", command=lambda: self.open_url(url_entry.get(), frame)) # Fallback
        go_button.pack(side="right", padx=5, pady=5)

        # Web content area
        content_area = tk.Text(frame, wrap="word", bg="#f0f0f0", fg="#333333") # Updated colors
        content_area.pack(fill="both", expand=True, padx=5, pady=5)

      def open_url(self, url, frame):
        """Open a URL and display the content."""
        if not url.startswith("http://") and not url.startswith("https://"):
          url = "http://" + url

        try:
          response = self.opener.open(url)
          content = response.read().decode("utf-8")

          # Find the content area in the current tab
          for widget in frame.winfo_children():
            if isinstance(widget, tk.Text):
              widget.delete(1.0, tk.END)
              widget.insert(tk.END, content)
        except Exception as e:
          for widget in frame.winfo_children():
            if isinstance(widget, tk.Text):
              widget.delete(1.0, tk.END)
              widget.insert(tk.END, f"Error: {e}")

      def change_background_color(self):
        """Change the background color of the browser."""
        color = colorchooser.askcolor()[1]
        if color:
          for tab in self.notebook.winfo_children():
            for widget in tab.winfo_children():
              if isinstance(widget, tk.Text):
                widget.config(bg=color)

if __name__ == "__main__":
  root = tk.Tk()
  browser = CustomBrowser(root)
  root.mainloop()
