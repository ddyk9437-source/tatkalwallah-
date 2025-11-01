import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading

# --- Import the browser automation logic ---
# We check if the script is in 'bmw' folder or not.
try:
    from bmw.irctc_actions import launch_irctc_web
except ImportError:
    # Fallback if running from the root directory
    try:
        from irctc_actions import launch_irctc_web
    except ImportError:
        print("CRITICAL: Could not import 'launch_irctc_web' from 'bmw/irctc_actions.py'")
        # Define a dummy function to avoid crashes
        def launch_irctc_web(*args, **kwargs):
            messagebox.showerror("Import Error", "Could not find 'launch_irctc_web' function.\nPlease check 'bmw/irctc_actions.py'.")

# --- File paths ---
IRCTC_ID_FILE = "irctc_ids.json"
PAYMENT_FILE = "payment_list.json"
PROXY_FILE = "proxies.json"

# --- Helper functions to load data ---
def load_json_file(filename, default_value=[]):
    """Safely loads a JSON file."""
    if not os.path.exists(filename):
        return default_value
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            # --- FIX: Handle files that are not lists ---
            if not isinstance(data, list):
                if os.path.basename(filename) == PROXY_FILE and isinstance(data, dict): # Handle old proxy format?
                    return list(data.keys()) # Or just return empty
                print(f"Warning: {filename} did not contain a list.")
                return default_value
            return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_value

def open_ticket_launcher(parent, ticket_data):
    """
    Opens the small cockpit window for a specific ticket.
    'parent' is the 'Open Ticket' list window.
    'ticket_data' is the full dictionary for the selected ticket.
    """
    
    win = tk.Toplevel(parent)
    # --- FIX: Use 'ticket_name' from the data pipeline ---
    win.title(ticket_data.get("ticket_name", "Launcher"))
    win.geometry("320x250")
    
    # --- Draggable Window Logic ---
    win.overrideredirect(True)
    win.configure(bg="#f0f0f0", relief="solid", bd=2)

    # --- Custom Title Bar ---
    title_bar = tk.Frame(win, bg="#d9d9d9", relief="raised", bd=0, height=25)
    title_bar.pack(fill="x")

    # --- FIX: Use 'ticket_name' ---
    title_label = tk.Label(title_bar, text=ticket_data.get("ticket_name"), bg="#d9d9d9", fg="black", font=("Arial", 9, "bold"))
    title_label.pack(side="left", padx=10)

    close_button = tk.Button(title_bar, text="X", bg="red", fg="white", font=("Arial", 10, "bold"),
                             width=3, bd=0, command=win.destroy)
    close_button.pack(side="right")

    def start_move(event): win.x, win.y = event.x, event.y
    def do_move(event):
        win.geometry(f"+{win.winfo_x() + event.x - win.x}+{win.winfo_y() + event.y - win.y}")

    title_bar.bind("<Button-1>", start_move)
    title_bar.bind("<B1-Motion>", do_move)
    title_label.bind("<Button-1>", start_move)
    title_label.bind("<B1-Motion>", do_move)
    
    # --- Main content ---
    content = tk.Frame(win, bg="#ffffff", padx=5, pady=5)
    content.pack(fill="both", expand=True)

    # --- Red Status Bar ---
    # --- FIX: Pull fare_limit from data ---
    fare_limit = ticket_data.get('fare_limit', 'N/A')
    status_bar = tk.Label(content, text=f"Ready - {{Bkg Fare Lim: {fare_limit}}} Login Lim:", bg="#dc3545", fg="white", font=("Arial", 9, "bold"), anchor="w")
    status_bar.pack(fill="x")
    
    # --- Ticket Info Frame ---
    info_frame = tk.Frame(content, bg="white")
    info_frame.pack(fill="x", pady=5)
    
    # --- FIX: Use correct data keys ---
    tk.Label(info_frame, text=f"{ticket_data.get('source')}_{ticket_data.get('destination')}", bg="white", fg="blue", font=("Arial", 10, "underline")).pack(side="left", padx=5)
    tk.Label(info_frame, text=ticket_data.get('train_no', 'N/A'), bg="white", font=("Arial", 10)).pack(side="left", padx=5)
    tk.Label(info_frame, text=f"{ticket_data.get('class', 'SL')}:{ticket_data.get('quota', 'PT')}", bg="white", font=("Arial", 10)).pack(side="left", padx=5)

    # ---
    # --- !! THIS IS THE CRASH FIX !! ---
    # ---
    date_str = ticket_data.get('date', 'N/A') # <-- Use 'date' key
    display_date = "N/A"
    try:
        # We assume date is MM/DD/YY or DD-MM-YYYY
        # Let's try to parse it to be safe
        date_obj = datetime.strptime(date_str.replace("/", "-"), "%m-%d-%y")
        display_date = date_obj.strftime("%m-%d") # "11-02"
    except ValueError:
        try:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            display_date = date_obj.strftime("%d-%m") # "02-11"
        except ValueError:
            # Fallback for "N/A" or other formats
            if '-' in date_str:
                parts = date_str.split('-')
                display_date = f"{parts[0]}-{parts[1]}"
            else:
                display_date = date_str
        
    tk.Label(info_frame, text=display_date, bg="white", font=("Arial", 10)).pack(side="left", padx=5)
    # --- !! END OF CRASH FIX !! ---

    # --- Load dynamic data ---
    irctc_ids = load_json_file(IRCTC_ID_FILE)
    payment_methods = load_json_file(PAYMENT_FILE)
    proxies = load_json_file(PROXY_FILE, default_value=["None"]) # Add "None" as default
    
    # --- FIX: Load the correct keys from JSON files ---
    irctc_id_names = [uid.get("user") for uid in irctc_ids if uid.get("user")]
    payment_names = [p.get("upi_id") for p in payment_methods if p.get("upi_id")] # Use 'upi_id'
    
    # Proxies are just strings, ensure "None" is an option
    proxy_names = ["None"] + [p for p in proxies if isinstance(p, str) and p != "None"]

    # --- Controls Frame 1 ---
    controls_frame1 = tk.Frame(content, bg="white")
    controls_frame1.pack(fill="x", pady=5)
    
    tk.Button(controls_frame1, text="Pair", bg="#e0e0e0", fg="blue", relief="solid", bd=1, width=5).pack(side="left", padx=2)
    
    pair_var = tk.StringVar()
    pair_dropdown = ttk.Combobox(controls_frame1, textvariable=pair_var, values=irctc_id_names, width=10, state="readonly")
    pair_dropdown.pack(side="left", padx=2)
    # --- FIX: Set dropdown to the ticket's saved ID ---
    if ticket_data.get("irctc_id") in irctc_id_names:
        pair_var.set(ticket_data.get("irctc_id"))
    elif irctc_id_names:
        pair_var.set(irctc_id_names[0])

    slot_var = tk.StringVar(value=ticket_data.get("slot", "T-1"))
    ttk.Combobox(controls_frame1, textvariable=slot_var, values=["T-1", "T-2", "Slot-1", "Slot-2"], width=5, state="readonly").pack(side="left", padx=2)

    tk.Checkbutton(controls_frame1, text="St", bg="white").pack(side="left", padx=2)

    # --- Controls Frame 2 (Payment) ---
    controls_frame2 = tk.Frame(content, bg="white")
    controls_frame2.pack(fill="x", pady=5)

    tk.Label(controls_frame2, text="Payment", bg="white", font=("Arial", 9)).pack(side="left", padx=2)
    payment_var = tk.StringVar()
    payment_dropdown = ttk.Combobox(controls_frame2, textvariable=payment_var, values=payment_names, width=20, state="readonly")
    payment_dropdown.pack(side="left", padx=2, fill="x", expand=True)
    # --- FIX: Set dropdown to the ticket's saved payment ---
    if ticket_data.get("payment") in payment_names:
        payment_var.set(ticket_data.get("payment"))
    elif payment_names:
        payment_var.set(payment_names[0])


    # --- Controls Frame 3 (Proxy) ---
    controls_frame3 = tk.Frame(content, bg="white")
    controls_frame3.pack(fill="x", pady=5)
    
    tk.Label(controls_frame3, text="Proxy", bg="white", font=("Arial", 9)).pack(side="left", padx=2)
    proxy_var = tk.StringVar(value=proxy_names[0])
    proxy_dropdown = ttk.Combobox(controls_frame3, textvariable=proxy_var, values=proxy_names, width=20, state="readonly")
    proxy_dropdown.pack(side="left", padx=2, fill="x", expand=True)

    # --- Button Bar ---
    button_bar = tk.Frame(content, bg="white")
    button_bar.pack(fill="x", pady=10)
    
    btn_style = {"fg": "white", "font": ("Arial", 9, "bold"), "width": 6, "relief": "raised", "bd": 2}
    
    tk.Button(button_bar, text="SUP", bg="#5a6268", **btn_style).pack(side="left", fill="x", expand=True, padx=2)
    tk.Button(button_bar, text="RAILON", bg="#28a745", **btn_style).pack(side="left", fill="x", expand=True, padx=2)
    tk.Button(button_bar, text="APP", bg="#ffc107", fg="black", **btn_style).pack(side="left", fill="x", expand=True, padx=2)
    web_btn = tk.Button(button_bar, text="WEB", bg="#007bff", **btn_style)
    web_btn.pack(side="left", fill="x", expand=True, padx=2)

    # --- Button Click Logic ---
    
    def on_launch_web():
        """Handles the 'WEB' button click."""
        selected_id_name = pair_var.get()
        selected_proxy_str = proxy_var.get()
        
        # Find the full IRCTC ID object
        selected_id_details = next((uid for uid in load_json_file(IRCTC_ID_FILE) if uid.get("user") == selected_id_name), None)
        if not selected_id_details:
            messagebox.showerror("Error", f"Could not find details for ID: {selected_id_name}", parent=win)
            return

        # Parse proxy string
        proxy_details = None
        if selected_proxy_str != "None":
            try:
                parts = selected_proxy_str.split(":")
                proxy_details = {"ip": parts[0], "port": parts[1]}
                if len(parts) == 4:
                    proxy_details["username"] = parts[2]
                    proxy_details["password"] = parts[3]
            except Exception as e:
                print(f"Could not parse proxy string: {e}")

        # Disable button to prevent double-click
        web_btn.config(text="Launching...", state="disabled", bg="#0056b3")
        win.update()
        
        # --- Run Selenium in a separate thread to avoid freezing the UI ---
        threading.Thread(
            target=launch_irctc_web, 
            args=(ticket_data, selected_id_details, proxy_details),
            daemon=True
        ).start()
        
        # Close this cockpit window after launching
        win.after(1000, win.destroy)

    web_btn.config(command=on_launch_w)
    
    # --- Make window modal ---
    win.transient(parent)
    win.grab_set()
    win.focus_force()

# --- This allows you to test this file directly ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main Test Window")
    root.geometry("400x400")
    
    # Dummy data for testing
    test_ticket = {
        "id": "t1", 
        "ticket_name": "BAM_ST_JITU", # <-- FIX: Use 'ticket_name'
        "source": "BAM",          # <-- FIX: Use 'source'
        "destination": "ST",      # <-- FIX: Use 'destination'
        "date": "02-11-2025",     # <-- FIX: Use 'date' (Full date)
        "quota": "PT", 
        "class": "SL",            # <-- FIX: Use 'class'
        "train_no": "20819",
        "slot": "Slot-1",
        "web": 1,
        "app": 0,
        "irctc_id": "test_user",  # <-- Add matching ID
        "payment": "Test_UPI@okhdfc" # <-- Add matching payment
    }
    # Create dummy files if missing
    if not os.path.exists(IRCTC_ID_FILE):
        with open(IRCTC_ID_FILE, "w") as f:
            json.dump([{"user": "test_user", "password": "test_pass"}], f)
    if not os.path.exists(PAYMENT_FILE):
        with open(PAYMENT_FILE, "w") as f:
            json.dump([{"upi_id": "Test_UPI@okhdfc"}], f) # <-- FIX: Use 'upi_id'
            
    def on_open_test():
        open_ticket_launcher(parent=root, ticket_data=test_ticket)

    tk.Button(root, text="Test Open Launcher", command=on_open_test).pack(pady=50)
    
    root.mainloop()

