import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from core.proxy_checker import check_proxy

# Define the path for the proxy file
PROXY_FILE = "proxies.json"

def load_proxies():
    """Loads the list of proxies from the JSON file. Returns a list of proxy dicts."""
    if not os.path.exists(PROXY_FILE):
        print(f"[INFO] {PROXY_FILE} not found. Creating new file.")
        return []

    try:
        if os.path.getsize(PROXY_FILE) == 0:
            print(f"[INFO] {PROXY_FILE} is empty. Returning empty list.")
            return []

        with open(PROXY_FILE, "r") as f:
            proxies = json.load(f)
            if isinstance(proxies, list):
                return proxies
            else:
                print(f"[WARN] {PROXY_FILE} is not a list. Resetting.")
                return []
    except Exception as e:
        print(f"[ERROR] Failed to load {PROXY_FILE}: {e}")
        return []

def save_proxies(proxies):
    """Saves the list of proxies to the JSON file."""
    try:
        with open(PROXY_FILE, "w") as f:
            json.dump(proxies, f, indent=4)
        print(f"[INFO] Saved {len(proxies)} proxies to {PROXY_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save {PROXY_FILE}: {e}")

def open_proxy_settings():
# ... (existing code) ...
    """Opens the 'Proxy IP Setting' window."""
    
    # --- Create the Toplevel Window ---
    win = tk.Toplevel()
    win.title("Proxy IP Setting")
    win.geometry("450x450")
    win.configure(bg="#ffeadb") # Light orange background
    win.resizable(False, False)

    # --- Draggable Window Logic ---
    win.overrideredirect(True) # Remove OS title bar
# ... (existing code) ...
    
    title_bar = tk.Frame(win, bg="#DAA520", relief="raised", bd=0, height=25) # Golden/brown title bar
    title_bar.pack(fill="x")

    title_label = tk.Label(title_bar, text="Proxy IP Setting", bg="#DAA520", fg="black", font=("Arial", 10, "bold"))
    title_label.pack(side="left", padx=10)

    close_button = tk.Button(title_bar, text="X", bg="red", fg="white", font=("Arial", 10, "bold"),
                             width=3, bd=0, command=win.destroy)
    close_button.pack(side="right")

    def start_move(event):
# ... (existing code) ...
        win.x = event.x
        win.y = event.y

    def do_move(event):
# ... (existing code) ...
        deltax = event.x - win.x
        deltay = event.y - win.y
        x = win.winfo_x() + deltax
        y = win.winfo_y() + deltay
        win.geometry(f"+{x}+{y}")

    title_bar.bind("<Button-1>", start_move)
    title_bar.bind("<B1-Motion>", do_move)
    title_label.bind("<Button-1>", start_move)
    title_label.bind("<B1-Motion>", do_move)
    
    # --- Main content frame ---
    content = tk.Frame(win, bg="#ffeadb")
# ... (existing code) ...
    content.pack(fill="both", expand=True, padx=10, pady=10)

    # --- 1. "ADD PRIVATE IP" section ---
    add_frame = tk.LabelFrame(content, text=" ADD PRIVATE IP ", bg="#ffeadb", font=("Arial", 9, "bold"))
# ... (existing code) ...
    add_frame.pack(fill="x", pady=5)

    tk.Label(add_frame, text="IP", bg="#ffeadb").grid(row=0, column=0, padx=5, pady=5)
    ip_entry = tk.Entry(add_frame)
    ip_entry.grid(row=1, column=0, padx=5, pady=5)

    tk.Label(add_frame, text="Port", bg="#ffeadb").grid(row=0, column=1, padx=5, pady=5)
    port_entry = tk.Entry(add_frame, width=10)
    port_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(add_frame, text="Username", bg="#ffeadb").grid(row=0, column=2, padx=5, pady=5)
    user_entry = tk.Entry(add_frame)
    user_entry.grid(row=1, column=2, padx=5, pady=5)

    tk.Label(add_frame, text="Password", bg="#ffeadb").grid(row=0, column=3, padx=5, pady=5)
    pass_entry = tk.Entry(add_frame, show="*")
    pass_entry.grid(row=1, column=3, padx=5, pady=5)

    check_irctc_var = tk.BooleanVar()
    tk.Checkbutton(add_frame, text="Check IRCTC", variable=check_irctc_var, bg="#ffeadb").grid(row=2, column=0, pady=5)

    save_btn = tk.Button(add_frame, text="Save", bg="orange", fg="black", font=("Arial", 9, "bold"))
    save_btn.grid(row=1, column=4, rowspan=2, padx=10, pady=5, ipady=5)
    
    # --- 2. "Proxy IP" management section ---
    manage_frame = tk.LabelFrame(content, text=" Proxy IP ", bg="#ffeadb", font=("Arial", 9, "bold"))
# ... (existing code) ...
    manage_frame.pack(fill="x", pady=10)

    proxy_list = load_proxies()
    proxy_var = tk.StringVar()
    proxy_dropdown = ttk.Combobox(manage_frame, textvariable=proxy_var, values=proxy_list, width=40)
    proxy_dropdown.pack(pady=10, padx=10)
    if proxy_list:
        proxy_dropdown.set(proxy_list[0])

    btn_frame = tk.Frame(manage_frame, bg="#ffeadb")
    btn_frame.pack(pady=5)
    
    check_btn = tk.Button(btn_frame, text="Check", bg="orange", fg="black", font=("Arial", 9, "bold"), width=10)
    check_btn.pack(side="left", padx=10)
    
    delete_btn = tk.Button(btn_frame, text="Delete", bg="orange", fg="black", font=("Arial", 9, "bold"), width=10)
    delete_btn.pack(side="left", padx=10)

    # --- 3. Instructions ---
    tk.Label(content, text="Yaha Par Ap Proxy ko IP:PORT:USERNAME:PASS format\nme enter kare aur ok kare to wo ip auto upar wale column me add ho jayega",
# ... (existing code) ...
             bg="#ffeadb", font=("Arial", 8, "bold")).pack(pady=5)
    
    tk.Label(content, text="Ok, Karne par proxy Upar column me add hogi waha se save kar",
# ... (existing code) ...
             bg="orange", fg="black", font=("Arial", 9, "bold"), relief="solid", bd=1).pack(fill="x", pady=10, ipady=5)

    # --- Function Logic ---
    
    def refresh_proxy_list():
# ... (existing code) ...
        """Reloads the proxy list from file and updates the dropdown."""
        proxies = load_proxies()
        proxy_dropdown['values'] = proxies
        if proxies:
            proxy_dropdown.set(proxies[0])
        else:
            proxy_dropdown.set("")

    def add_proxy_logic():
# ... (existing code) ...
        """Saves the proxy from the entry fields."""
        ip = ip_entry.get()
        port = port_entry.get()
        user = user_entry.get()
        pwd = pass_entry.get()

        if not (ip and port):
            messagebox.showerror("Error", "IP and Port are required.", parent=win)
            return

        # Format: IP:PORT or IP:PORT:USER:PASS
        if user and pwd:
            proxy_str = f"{ip}:{port}:{user}:{pwd}"
        else:
            proxy_str = f"{ip}:{port}"

        proxies = load_proxies()
        if proxy_str in proxies:
            messagebox.showinfo("Info", "Proxy already exists.", parent=win)
            return
            
        proxies.append(proxy_str)
        save_proxies(proxies)
        messagebox.showinfo("Success", "Proxy saved!", parent=win)
        
        # Clear fields
        ip_entry.delete(0, "end")
        port_entry.delete(0, "end")
        user_entry.delete(0, "end")
        pass_entry.delete(0, "end")
        
        refresh_proxy_list()

    def delete_proxy_logic():
# ... (existing code) ...
        """Deletes the selected proxy."""
        selected_proxy = proxy_var.get()
        if not selected_proxy:
            messagebox.showerror("Error", "No proxy selected to delete.", parent=win)
            return
            
        proxies = load_proxies()
        if selected_proxy in proxies:
            proxies.remove(selected_proxy)
            save_proxies(proxies)
            messagebox.showinfo("Success", "Proxy deleted.", parent=win)
            refresh_proxy_list()
        else:
            messagebox.showerror("Error", "Proxy not found in list.", parent=win)

    def check_proxy_logic():
        """Checks the selected proxy from dropdown using IRCTC test."""
        selected_proxy = proxy_var.get()
        if not selected_proxy:
            messagebox.showerror("Error", "No proxy selected to check.", parent=win)
            return

        # Parse string back to components
        parts = selected_proxy.split(":")
        if len(parts) == 4:
         ip, port, user, pwd = parts
        elif len(parts) == 2:
            ip, port = parts
            user = pwd = None
        else:
            messagebox.showerror("Error", "Invalid proxy format.", parent=win)
            return

        result = check_proxy(ip, port, user, pwd)
        if result:
            messagebox.showinfo("Proxy Check", f"✅ {ip}:{port} is working with IRCTC", parent=win)
        else:
            messagebox.showerror("Proxy Check", f"❌ {ip}:{port} is blocked or failed", parent=win)

    def check_proxy_logic():
        selected_proxy = proxy_var.get()
        if not selected_proxy:
            messagebox.showerror("Error", "No proxy selected to check.", parent=win)
            return

        parts = selected_proxy.split(":")
        if len(parts) == 4:
            ip, port, user, pwd = parts
        elif len(parts) == 2:
            ip, port = parts
            user = pwd = None
        else:
            messagebox.showerror("Error", "Invalid proxy format.", parent=win)
            return

        result = check_proxy(ip, port, user, pwd)
        if result:
            messagebox.showinfo("Proxy Check", f"✅ {ip}:{port} is working with IRCTC", parent=win)
        else:
            messagebox.showerror("Proxy Check", f"❌ {ip}:{port} is blocked or failed", parent=win)
    # --- Bind buttons to functions ---
    save_btn.config(command=add_proxy_logic)
    delete_btn.config(command=delete_proxy_logic)
    check_btn.config(command=check_proxy_logic)
    
    # --- Make window modal ---
    win.transient(win.master)
    win.grab_set()

# This allows you to test this file directly
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    # Create dummy structured proxies.json if missing
    if not os.path.exists(PROXY_FILE):
        dummy_proxies = [
            {"ip": "127.0.0.1", "port": "8080", "username": "", "password": ""},
            {"ip": "192.168.1.1", "port": "9000", "username": "user", "password": "pass"}
        ]
        save_proxies(dummy_proxies)

    open_proxy_settings()
    root.mainloop()

