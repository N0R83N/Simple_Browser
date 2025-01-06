import tkinter as tk
    from tkinter import ttk
    from tkinter import colorchooser
    import webbrowser
    import http.cookiejar
    import urllib.request

    class CustomBrowser:
      def __init__(self, root):
        self.root = root
        self.root.title("Customizable Browser")
        self.root.geometry("800x600")

        # Cookie jar for basic cookie handling
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Add the first tab
        self.add_tab()

        # Create a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add settings menu
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        settings_menu.add_command(label="Change Background Color", command=self.change_background_color)
        settings_menu.add_command(label="New Tab", command=self.add_tab)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)

      def add_tab(self):
        """Add a new tab to the browser."""
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text="New Tab")

        # URL bar
        url_frame = tk.Frame(frame)
        url_frame.pack(fill="x")

        url_entry = tk.Entry(url_frame)
        url_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        go_button = tk.Button(url_frame, text="Go", command=lambda: self.open_url(url_entry.get(), frame))
        go_button.pack(side="right", padx=5, pady=5)

        # Web content area
        content_area = tk.Text(frame, wrap="word", bg="white", fg="black")
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
