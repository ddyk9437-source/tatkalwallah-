import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time
import threading
import queue
import os
import sys
import uuid # <-- Need this for new ticket IDs

# --- !! START IMPORT FIX !! ---
# This forces Python to look for 'core' in the same folder as this file
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
except NameError:
    # This handles cases where __file__ is not defined (like in some IDEs)
    script_dir = os.getcwd()
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
# --- !! END IMPORT FIX !! ---


# --- Offline catalogs (stations/train names) ---
STATION_CODE_SET = set()
TRAIN_NO_TO_NAME = {}

def load_offline_catalogs():
    """Load station and train catalogs from assets/ if present."""
    global STATION_CODE_SET, TRAIN_NO_TO_NAME
    assets_dir = os.path.join(script_dir, "assets")

    # Stations list
    stations_candidates = [
        os.path.join(assets_dir, "railwayStationsList.json"),
        os.path.join(assets_dir, "Railway Stations"),
    ]
    for path in stations_candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    codes = [s.get("code") for s in data if isinstance(s, dict) and s.get("code")]
                    STATION_CODE_SET.update([c.strip().upper() for c in codes if isinstance(c, str)])
                elif isinstance(data, dict):
                    STATION_CODE_SET.update([k.strip().upper() for k in data.keys()])
        except Exception as e:
            print(f"[Offline Stations] Failed to load {path}: {e}")

    # Train numbers and names
    trains_candidates = [
        os.path.join(assets_dir, "Indian Railway Train Numbers & Names.json"),
    ]
    for path in trains_candidates:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for row in data:
                        num = None
                        name = None
                        if isinstance(row, dict):
                            num = row.get("number") or row.get("train_no") or row.get("trainNum")
                            name = row.get("name") or row.get("train_name") or row.get("trainName")
                        if num and isinstance(num, (str, int)) and name:
                            TRAIN_NO_TO_NAME[str(num).strip()] = name.strip()
                elif isinstance(data, dict):
                    for k, v in data.items():
                        TRAIN_NO_TO_NAME[str(k).strip()] = str(v).strip()
        except Exception as e:
            print(f"[Offline Trains] Failed to load {path}: {e}")

load_offline_catalogs()


def is_valid_station_code(code):
    if not (isinstance(code, str) and 2 <= len(code) <= 5 and code.isupper()):
        return False
    if STATION_CODE_SET:
        return code in STATION_CODE_SET
    return True


def resolve_train_name(train_no: str) -> str:
    try:
        return TRAIN_NO_TO_NAME.get(str(train_no).strip(), "")
    except Exception:
        return ""


# --- !! "AVENGER" AVAILABILITY FUNCTION (s.erail.in) !! ---
def get_train_availability(train_no, date, src, dst, cls, quota):
    """
    This function now uses the s.erail.in/getvalue API
    that you discovered.
    """
    print(f"Checking availability via s.erail.in for {train_no}...")
    try:
        # Convert MM/DD/YY to DD-MM-YYYY
        date_obj = datetime.strptime(date.replace("-", "/").replace(".", "/"), "%m/%d/%y")
        formatted_date = date_obj.strftime("%d-%m-%Y")
    except Exception as e:
        print(f"Invalid date format: {e}")
        return []

    url = "https://s.erail.in/getvalue"
    
    payload = {
        'trainNo': train_no,
        'from': src,
        'to': dst,
        'date': formatted_date,
        'class': cls,
        'quota': quota,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Referer': 'https://erail.in/', # Disguise as coming from erail.in
        'Origin': 'https://erail.in',
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # e.g., ["31-10-2025", "RLWL 1/REFRESH", "90%"]
        if data and isinstance(data, list) and len(data[0]) > 1:
            availability = data[0][1] # "RLWL 1/REFRESH"
            return [f"{formatted_date}: {availability}"]
        else:
            return ["No data found."]

    except Exception as e:
        print(f"Error fetching availability from s.erail.in: {e}")
        return []


# --- !! THIS IS YOUR WORKING "ETRAIN.INFO" SCRAPER !! ---
def get_trains_between(src, dst, date_str_yyyy_mm_dd):
    """
    This function now uses YOUR working scraper logic from etrain_parse.py
    --- NEW: It now returns a list of DICTIONARIES for the GUI ---
    """
    print(f"Searching trains (YOUR etrain.info scrape) on: {src} to {dst}")
    
    # --- 1. Convert date format (YYYY-MM-DD -> DD-MMM-YYYY) ---
    try:
        date_obj = datetime.strptime(date_str_yyyy_mm_dd, "%Y-%m-%d")
        url_date = date_obj.strftime("%d-%b-%Y").upper() # e.g., 01-NOV-2025
    except Exception as e:
        print(f"Date formatting error: {e}")
        return []

    # --- 2. Build the URL ---
    url = f"https://etrain.info/trains/{src}-to-{dst}?date={url_date}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Referer': 'https://etrain.info/',
    }

    try:
        print(f"  Scraping URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- 3. Use *YOUR* exact table-finding logic ---
        train_table = soup.find('table', class_='myTable data nocps nolrborder bx1_brm')
        if not train_table:
            print("  Fallback: trying general 'myTable data' class...")
            train_table = soup.find('table', {'class': lambda x: x and 'myTable' in x and 'data' in x})

        if not train_table:
            print("  No trains found on page. (No 'myTable data' found).")
            return []
        
        trains_list = []
        rows = train_table.find_all('tr')
        if not rows:
              print("  Table found, but no rows.")
              return []

        # --- 4. Parse the table ---
        for row in rows[1:]: # Skip header
            try:
                cols = row.find_all('td')
                if len(cols) < 8: # Not a valid train row
                    continue
                
                number = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True)
                dep = cols[3].get_text(strip=True)
                arr = cols[5].get_text(strip=True)
                dur = cols[6].get_text(strip=True)
                
                classes_text = cols[-1].get_text(" ", strip=True) # "2A 3A SL"
                classes_list = classes_text.split() # ["2A", "3A", "SL"]

                if number and name:
                    trains_list.append({
                        "number": number,
                        "name": name,
                        "dep": dep,
                        "arr": arr,
                        "dur": dur,
                        "classes": classes_list
                    })
            except Exception as e:
                print(f"Error parsing one row: {e}")

        print(f"Train rows found ({src}->{dst}):", len(trains_list))
        return trains_list

    except Exception as e:
        print(f"ERROR during network request (etrain.info): {e}")
        return []
# --- !! END OF NEW ETRAIN.INFO METHOD !! ---


# --- Function to Open New Ticket Window (Blank) ---
def open_new_ticket(selected_date=None):
    if not selected_date:
        selected_date = datetime.now().strftime("%Y-%m-%d")
    try:
        formatted_ui_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%m/%d/%y")
    except Exception:
        formatted_ui_date = datetime.now().strftime("%m/%d/%y")

    # --- POLISH: Add a unique ID for new tickets ---
    blank_ticket = {
        "id": f"ticket_{uuid.uuid4().hex[:8]}", # New unique ID
        "source": "", "destination": "", "passengers": [],
        "auto_upgrade": True,
        "confirm_berth": True,
        "ticket_name": "", "fare_limit": "",
        "irctc_id": "", "payment": "",
        "class": "SL", "quota": "GN", "train_no": "",
        "date": formatted_ui_date,
        "mobile": "",
        "slot": "Slot-1", # Default slot
        "web": 1,        # Default web
        "app": 0         # Default app
    }
    open_new_ticket_autofill(blank_ticket)

# --- Function to Open Ticket Window (Polished & Fixed) ---
def open_new_ticket_autofill(ticket):
    
    # --- POLISH: Make window more compact ---
    win = tk.Toplevel()
    win_title = f"Edit Ticket: {ticket.get('ticket_name', '...North-Gondwana...')}" if ticket.get('ticket_name') else "Create New Ticket"
    win.title(win_title)
    win.geometry("800x500") # <-- Made 100px shorter
    win.configure(bg="black")

    # --- Load dynamic dropdown data ---
    try:
        with open("irctc_ids.json", "r") as f:
            irctc_data = json.load(f)
            irctc_users = [entry["user"] for entry in irctc_data if "user" in entry]
    except Exception as e:
        print(f"Warning: Could not load irctc_ids.json: {e}")
        irctc_users = []
    try:
        with open("payment_list.json", "r") as f:
            payment_data = json.load(f)
            upi_ids = [entry["upi_id"] for entry in payment_data if "upi_id" in entry]
    except Exception as e:
        print(f"Warning: Could not load payment_list.json: {e}")
        upi_ids = []

    # --- Define all UI elements ---
    
    # --- Row 1: Source and Destination ---
    tk.Label(win, text="Source :", fg="lime", bg="black").place(x=20, y=20)
    src_entry = tk.Entry(win, bg="navy", fg="white", width=18)
    src_entry.place(x=100, y=20)
    src_entry.insert(0, ticket.get("source", ""))

    tk.Label(win, text="Destination:", fg="lime", bg="black").place(x=320, y=20)
    dst_entry = tk.Entry(win, bg="navy", fg="white", width=18)
    dst_entry.place(x=420, y=20)
    dst_entry.insert(0, ticket.get("destination", ""))

    # --- Train/Class/Quota/Date/Mobile ---
    tk.Label(win, text="Train:", fg="lime", bg="black").place(x=20, y=55)
    trainno_entry = tk.Entry(win, bg="navy", fg="white", width=10)
    trainno_entry.place(x=75, y=55)
    trainno_entry.insert(0, ticket.get("train_no", ""))

    tk.Label(win, text="Class:", fg="lime", bg="black").place(x=160, y=55)
    class_combo_main = ttk.Combobox(win, values=["SL", "3A", "2A", "1A", "CC", "2S", "3E", "FC", "EC"], width=4)
    class_combo_main.place(x=210, y=55)
    class_combo_main.set(ticket.get("class","SL"))

    tk.Label(win, text="Quota:", fg="lime", bg="black").place(x=270, y=55)
    quota_combo_main = ttk.Combobox(win, values=["GN", "TQ", "LD", "SS", "DF", "PH"], width=4)
    quota_combo_main.place(x=320, y=55)
    quota_combo_main.set(ticket.get("quota", "GN"))

    tk.Label(win, text="Date:", fg="lime", bg="black").place(x=400, y=55)
    date_entry_main = tk.Entry(win, bg="white", fg="black", width=12)
    date_entry_main.place(x=440, y=55)
    date_entry_main.insert(0, ticket.get("date", datetime.now().strftime("%m/%d/%y")))

    tk.Label(win, text="Mob No.:", fg="lime", bg="black").place(x=580, y=55)
    mob_entry = tk.Entry(win, bg="navy", fg="white", width=12)
    mob_entry.place(x=650, y=55)
    mob_entry.insert(0, ticket.get("mobile", ""))

    tk.Button(win, text="Find Train", command=lambda: open_train_popup(), bg="green", fg="black", font=("Arial",10,"bold")).place(x=600, y=18)

    # --- Passenger Frame (COMPACT) ---
    passenger_frame = tk.Frame(win, bg="black")
    passenger_frame.place(x=20, y=90, width=760, height=210)

    tk.Label(passenger_frame, text="Name", fg="lime", bg="black").place(x=0, y=5)
    p_name_entry = tk.Entry(passenger_frame, width=15, bg="navy", fg="white")
    p_name_entry.place(x=0, y=30)
    
    tk.Label(passenger_frame, text="Age", fg="lime", bg="black").place(x=100, y=5)
    p_age_entry = tk.Entry(passenger_frame, width=4, bg="navy", fg="white")
    p_age_entry.place(x=100, y=30)
    
    tk.Label(passenger_frame, text="Gender", fg="lime", bg="black").place(x=140, y=5)
    p_gender_combo = ttk.Combobox(passenger_frame, values=["Male", "Female", "Other"], width=7)
    p_gender_combo.place(x=140, y=30)
    p_gender_combo.set("Male")
    
    tk.Label(passenger_frame, text="Berth Choice", fg="lime", bg="black").place(x=220, y=5)
    p_berth_combo = ttk.Combobox(passenger_frame, values=["No Preference", "Lower", "Middle", "Upper", "Side Lower", "Side Upper"], width=14)
    p_berth_combo.place(x=220, y=30)
    p_berth_combo.set("No Preference")
    
    tk.Label(passenger_frame, text="Food Choice", fg="lime", bg="black").place(x=350, y=5)
    p_food_combo = ttk.Combobox(passenger_frame, values=["No Preference", "Veg", "Non-Veg"], width=14)
    p_food_combo.place(x=350, y=30)
    p_food_combo.set("No Preference")

    # --- Passenger Listbox ---
    passenger_listbox = tk.Listbox(passenger_frame, bg="navy", fg="white", height=6, width=60)
    passenger_listbox.place(x=0, y=65)
    
    # --- Passenger Buttons ---
    def add_passenger():
        name = p_name_entry.get()
        age = p_age_entry.get()
        if not name or not age:
            messagebox.showwarning("Missing Info", "Please enter at least Name and Age.", parent=win)
            return
        
        gender = p_gender_combo.get()
        berth = p_berth_combo.get()
        food = p_food_combo.get()
        
        # Store data as a dict string in the listbox
        p_data = {"name": name, "age": age, "gender": gender, "berth": berth, "food": food}
        display_text = f"{name} ({age}, {gender}) - {berth}"
        
        # Add to listbox, storing both text and data
        passenger_listbox.insert(tk.END, display_text)
        # Store the raw data in a parallel list (or use a custom listbox)
        if not hasattr(passenger_listbox, 'passenger_data'):
            passenger_listbox.passenger_data = []
        passenger_listbox.passenger_data.append(p_data)
        
        # Clear fields
        p_name_entry.delete(0, tk.END)
        p_age_entry.delete(0, tk.END)
        p_gender_combo.set("Male")
        p_berth_combo.set("No Preference")

    def remove_passenger():
        selected_indices = passenger_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a passenger to remove.", parent=win)
            return
        
        selected_index = selected_indices[0]
        passenger_listbox.delete(selected_index)
        # Remove from parallel data list
        if hasattr(passenger_listbox, 'passenger_data'):
            passenger_listbox.passenger_data.pop(selected_index)

    tk.Button(passenger_frame, text="Add Passenger", bg="green", fg="black", command=add_passenger).place(x=500, y=80)
    tk.Button(passenger_frame, text="Remove Selected", bg="red", fg="white", command=remove_passenger).place(x=500, y=120)

    # --- Load existing passengers into listbox ---
    passenger_listbox.passenger_data = []
    for p in ticket.get("passengers", []):
        display_text = f"{p.get('name')} ({p.get('age')}, {p.get('gender')}) - {p.get('berth')}"
        passenger_listbox.insert(tk.END, display_text)
        passenger_listbox.passenger_data.append(p)
    
    # --- Checkboxes ---
    auto_upgrade_var = tk.BooleanVar(value=ticket.get("auto_upgrade"))
    confirm_berth_var = tk.BooleanVar(value=ticket.get("confirm_berth"))
    
    tk.Checkbutton(win, text="Consider Auto upgradation", variable=auto_upgrade_var, fg="red", bg="black", selectcolor="black", activebackground="black", activeforeground="red").place(x=20, y=310)
    tk.Checkbutton(win, text="Book only if confirm Berth Allocated", variable=confirm_berth_var, fg="red", bg="black", selectcolor="black", activebackground="black", activeforeground="red").place(x=320, y=310)

    # --- Ticket summary/lower ---
    tk.Label(win, text="Ticket Name:", fg="lime", bg="black").place(x=20, y=350)
    ticket_name_entry = tk.Entry(win, width=20, bg="navy", fg="white")
    ticket_name_entry.place(x=130, y=350)
    ticket_name_entry.insert(0, ticket.get("ticket_name", ""))

    tk.Label(win, text="PT Fare Limit:", fg="lime", bg="black").place(x=320, y=350)
    fare_limit_entry = tk.Entry(win, width=18, bg="navy", fg="white")
    fare_limit_entry.place(x=420, y=350)
    fare_limit_entry.insert(0, ticket.get("fare_limit", ""))

    tk.Label(win, text="IRCTC ID:", fg="lime", bg="black").place(x=20, y=390)
    irctc_combo = ttk.Combobox(win, values=irctc_users, width=18, state="readonly")
    irctc_combo.place(x=130, y=390)
    irctc_combo.set(ticket.get("irctc_id", ""))

    tk.Label(win, text="Payment:", fg="lime", bg="black").place(x=320, y=390)
    payment_combo = ttk.Combobox(win, values=upi_ids, width=18, state="readonly")
    payment_combo.place(x=420, y=390)
    payment_combo.set(ticket.get("payment", ""))

    # --- POLISH: Add Slot, Web, App controls ---
    tk.Label(win, text="Slot:", fg="lime", bg="black").place(x=580, y=350)
    slot_combo = ttk.Combobox(win, values=["Slot-1", "Slot-2", "Slot-3", "Slot-4"], width=8, state="readonly")
    slot_combo.place(x=620, y=350)
    slot_combo.set(ticket.get("slot", "Slot-1"))

    web_var = tk.IntVar(value=ticket.get("web", 1))
    tk.Checkbutton(win, text="Web", variable=web_var, fg="lime", bg="black", selectcolor="black", activebackground="black", activeforeground="lime").place(x=580, y=385)
    
    app_var = tk.IntVar(value=ticket.get("app", 0))
    tk.Checkbutton(win, text="App", variable=app_var, fg="lime", bg="black", selectcolor="black", activebackground="black", activeforeground="lime").place(x=650, y=385)


    # --- Save Function ---
    def save_ticket():
        
        # --- POLISH: Get passengers from the listbox data ---
        passengers_to_save = []
        if hasattr(passenger_listbox, 'passenger_data'):
            passengers_to_save = passenger_listbox.passenger_data
            
        if not passengers_to_save:
            messagebox.showwarning("No Passengers", "Please add at least one passenger.", parent=win)
            return
            
        new_ticket_name = ticket_name_entry.get()
        if not new_ticket_name:
            messagebox.showwarning("No Ticket Name", "Ticket Name is required.", parent=win)
            return
            
        # --- Update the original ticket dictionary ---
        ticket.update({
            "id": ticket.get("id"), # Keep the original ID
            "source": src_entry.get(),
            "destination": dst_entry.get(),
            "train_no": trainno_entry.get(),
            "class": class_combo_main.get(),
            "quota": quota_combo_main.get(),
            "date": date_entry_main.get(),
            "mobile": mob_entry.get(),
            "passengers": passengers_to_save, # <-- Save from listbox
            "auto_upgrade": auto_upgrade_var.get(),
            "confirm_berth": confirm_berth_var.get(),
            "ticket_name": new_ticket_name,
            "fare_limit": fare_limit_entry.get(),
            "irctc_id": irctc_combo.get(),
            "payment": payment_combo.get(),
            "slot": slot_combo.get(),
            "web": web_var.get(),
            "app": app_var.get()
        })
        
        try:
            with open("ticket_list.json", "r") as f:
                data = json.load(f)
                if not isinstance(data, list): data = []
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
            
        # --- POLISH: Find and update ticket by ID ---
        found = False
        for i, t in enumerate(data):
            if t.get("id") == ticket.get("id"):
                print(f"Updating existing ticket (ID: {ticket.get('id')})")
                data[i] = ticket # Update ticket in place
                found = True
                break
                
        if not found:
            print(f"Adding new ticket (ID: {ticket.get('id')})")
            data.append(ticket)
            
        try:
            with open("ticket_list.json", "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Saved", "✅ Ticket saved successfully!", parent=win)
            win.destroy() # Close window after saving
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save ticket: {e}", parent=win)

    tk.Button(win, text="Save Ticket", command=save_ticket, bg="lime", fg="black", font=("Arial", 12, "bold")).place(x=320, y=440)


    # --- Find Train Popup Function (defined inside) ---
    def open_train_popup():
        train_popup = tk.Toplevel(win)
        train_popup.title("Train Between")
        train_popup.geometry("650x380")
        train_popup.configure(bg="black")
        train_popup.overrideredirect(True)

        # --- Draggable Title Bar ---
        title_bar = tk.Frame(train_popup, bg="#39FF14", relief="raised", bd=0, height=25)
        title_bar.pack(fill="x")
        title_label = tk.Label(title_bar, text="Train Between", bg="#39FF14", fg="black", font=("Arial", 10, "bold"))
        title_label.pack(side="left", padx=10)
        close_button = tk.Button(title_bar, text="X", bg="red", fg="white", font=("Arial", 10, "bold"),
                                 width=3, bd=0, command=train_popup.destroy)
        close_button.pack(side="right")

        def start_move(event):
            train_popup.x = event.x
            train_popup.y = event.y
        def do_move(event):
            deltax = event.x - train_popup.x
            deltay = event.y - train_popup.y
            x = train_popup.winfo_x() + deltax
            y = train_popup.winfo_y() + deltay
            train_popup.geometry(f"+{x}+{y}")
        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", do_move)

        # --- Compact Control Frame (using grid) ---
        controls_frame = tk.Frame(train_popup, bg="black")
        controls_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(controls_frame, text="From:", fg="lime", bg="black").grid(row=0, column=0, sticky="w", padx=5)
        from_entry = tk.Entry(controls_frame, bg="navy", fg="white", width=15)
        from_entry.grid(row=0, column=1, pady=2)
        from_entry.insert(0, src_entry.get())
    
        tk.Label(controls_frame, text="To:", fg="lime", bg="black").grid(row=1, column=0, sticky="w", padx=5)
        to_entry = tk.Entry(controls_frame, bg="navy", fg="white", width=15)
        to_entry.grid(row=1, column=1, pady=2)
        to_entry.insert(0, dst_entry.get())

        tk.Label(controls_frame, text="Date:", fg="lime", bg="black").grid(row=2, column=0, sticky="w", padx=5)
        date_entry = tk.Entry(controls_frame, bg="white", fg="black", width=12)
        date_entry.grid(row=2, column=1, pady=2, sticky="w")
        date_entry.insert(0, date_entry_main.get()) # Get date from main window
        
        tk.Label(controls_frame, text="Quota:", fg="lime", bg="black").grid(row=0, column=2, sticky="w", padx=5)
        quota_var = tk.StringVar()
        quota_combo = ttk.Combobox(controls_frame, values=["GN", "TQ", "LD", "SS", "DF", "PH"], width=10, textvariable=quota_var, state="readonly")
        quota_combo.grid(row=0, column=3, pady=2)
        quota_combo.set(quota_combo_main.get()) # Get quota from main window
    
        tk.Label(controls_frame, text="Class:", fg="lime", bg="black").grid(row=1, column=2, sticky="w", padx=5)
        class_combo = ttk.Combobox(controls_frame, values=["SL", "3A", "2A", "1A", "CC", "2S", "3E", "FC", "EC"], width=10, state="readonly")
        class_combo.grid(row=1, column=3, pady=2)
        class_combo.set("SL")

        tk.Button(controls_frame, text="Search Trains", command=lambda: search_trains_popup(), bg="green", fg="black", width=15).grid(row=0, column=4, padx=10, pady=2)
        tk.Button(controls_frame, text="Check Availability", command=lambda: check_availability_popup(), bg="blue", fg="white", width=15).grid(row=1, column=4, padx=10, pady=2)

        # --- "AVENGER" STYLE TRAIN FRAME ---
        list_canvas_frame = tk.Frame(train_popup, bg="black", bd=0, highlightthickness=0)
        list_canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        list_canvas = tk.Canvas(list_canvas_frame, bg="black", highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(list_canvas_frame, orient="vertical", command=list_canvas.yview)
        scrollable_train_list_frame = tk.Frame(list_canvas, bg="black")
        scrollable_train_list_frame.bind(
            "<Configure>",
            lambda e: list_canvas.configure(
                scrollregion=list_canvas.bbox("all")
            )
        )
        list_canvas.create_window((0, 0), window=scrollable_train_list_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=list_scrollbar.set)
        list_canvas.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")
        # --- END OF LIST FRAME ---

        def on_class_select(train_data, class_code):
            """Called when a user clicks a GREEN class button."""
            print(f"User selected Train: {train_data['number']} Class: {class_code}")
            
            # Update main window fields
            src_entry.delete(0, tk.END); src_entry.insert(0, from_entry.get())
            dst_entry.delete(0, tk.END); dst_entry.insert(0, to_entry.get())
            trainno_entry.delete(0, tk.END); trainno_entry.insert(0, train_data['number'])
            
            class_combo_main.set(class_code) # <-- Set the selected class
            quota_combo_main.set(quota_combo.get())
            date_entry_main.delete(0, tk.END)
            date_entry_main.insert(0, date_entry.get())
            
            train_popup.destroy()
        
        def thread_target_search_trains(src, dst, dte, res_queue):
            """Threaded wrapper for the ONLINE ETRAIN.INFO scrape."""
            try:
                results = get_trains_between(src, dst, dte)
                error = None
                if not results:
                    error = "No trains found for this route and date."
                res_queue.put((results, error))
            except Exception as e:
                res_queue.put(([], f"API search error: {e}"))

        def poll_search_queue(res_queue):
            """This function runs on the UI thread, checking the queue."""
            try:
                trains, error = res_queue.get_nowait() 
                
                # Clear loading message
                for widget in scrollable_train_list_frame.winfo_children():
                    widget.destroy()

                if error:
                    messagebox.showinfo("No results", error, parent=train_popup)
                elif trains:
                    ALL_CLASSES = ["1A", "2A", "3A", "SL", "3E", "CC", "2S", "FC", "EC"]
                    
                    for train in trains:
                        row_frame = tk.Frame(scrollable_train_list_frame, bg="#222")
                        row_frame.pack(fill="x", expand=True, pady=1)
                        
                        train_label_str = f"{train['number']} - {train['name']}"
                        tk.Label(row_frame, text=train_label_str, fg="white", bg="#222", font=("Arial", 9, "bold"), anchor="w").pack(side="left", padx=5, pady=2)
                        
                        class_frame = tk.Frame(row_frame, bg="#222")
                        class_frame.pack(side="right", padx=5, pady=2)

                        available_classes_for_this_train = train.get("classes", [])

                        for class_code in ALL_CLASSES:
                            if class_code in available_classes_for_this_train:
                                btn = tk.Button(class_frame, text=class_code, bg="green", fg="white", font=("Arial", 8, "bold"), width=4,
                                                command=lambda t=train, c=class_code: on_class_select(t, c), bd=0, activebackground="green4")
                                btn.pack(side="left", padx=1)
                            else:
                                btn = tk.Button(class_frame, text=class_code, bg="red", fg="#555", font=("Arial", 8), width=4,
                                                state="disabled", relief="sunken", bd=0)
                                btn.pack(side="left", padx=1)
                else:
                    messagebox.showinfo("No trains", "No trains found. Try other stations or dates.", parent=train_popup)
            
            except queue.Empty:
                train_popup.after(100, poll_search_queue, res_queue)
            except Exception as e:
                print(f"Error in poll_search_queue: {e}")
                tk.Label(scrollable_train_list_frame, text=f"Error: {e}", fg="red", bg="black").pack()

        def search_trains_popup():
            src = from_entry.get().strip().upper()
            dst = to_entry.get().strip().upper()
            dte = date_entry.get().strip()

            if not src or not dst or not dte:
                messagebox.showerror("Error", "From, To, and Date are required.", parent=train_popup)
                return

            try:
                # Convert MM/DD/YY to YYYY-MM-DD
                dte2 = datetime.strptime(dte.replace("-", "/").replace(".", "/"), "%m/%d/%y").strftime("%Y-%m-%d")
            except Exception:
                messagebox.showerror("Error", "Date must be MM/DD/YY", parent=train_popup)
                return

            for widget in scrollable_train_list_frame.winfo_children():
                widget.destroy()
            tk.Label(scrollable_train_list_frame, text="Searching... Please wait.", fg="lime", bg="black").pack()
            train_popup.update_idletasks()

            result_queue = queue.Queue()
            threading.Thread(
                target=thread_target_search_trains,
                args=(src, dst, dte2, result_queue),
                daemon=True
            ).start()

            poll_search_queue(result_queue)

        def check_availability_popup():
            messagebox.showinfo("Info", "This button is for a future update.\nPlease click a green class button to select a train.", parent=train_popup)

        # --- Make popup modal ---
        train_popup.transient(win)
        train_popup.grab_set()

    # --- Make main window modal ---
    win.transient(win.master)
    win.grab_set()


# --- Main application setup (to make the file runnable) ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main Control Panel")
    root.geometry("300x200")
    
    # Add a style for the main ttk button
    style = ttk.Style(root)
    style.configure("TButton", font=("Arial", 10))

    # Button to open the new ticket window
    new_ticket_btn = ttk.Button(root, text="Open New Ticket", command=open_new_ticket)
    new_ticket_btn.pack(expand=True, padx=20, pady=20)
    
    # Label to show this is the main window
    tk.Label(root, text="This is the main window.\nClick the button to open the ticket editor.").pack(pady=10)

    root.mainloop()

