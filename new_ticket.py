import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests  # <-- We need this
from datetime import datetime
from bs4 import BeautifulSoup # <-- We need this
import time
import threading
import queue
import os
import sys
import random

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

# --- REMOVED ALL 'core' IMPORTS ---
# from core.search_engine import search_trains


# --- Offline catalogs (stations/train names) ---
# --- We still keep this to help the user ---
STATION_CODE_SET = set()
TRAIN_NO_TO_NAME = {}

def fill_random_mobile(entry_field):
    random_number = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    entry_field.delete(0, tk.END)
    entry_field.insert(0, random_number)

def load_offline_catalogs():
# ... (existing code ...
    """Load station and train catalogs from assets/ if present."""
    global STATION_CODE_SET, TRAIN_NO_TO_NAME
    # --- FIX: Use the script_dir variable to find 'assets' ---
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
# ... (existing code ...
    if not (isinstance(code, str) and code.isalpha() and 2 <= len(code) <= 5 and code.isupper()):
        return False
    if STATION_CODE_SET:
        return code in STATION_CODE_SET
    return True


def resolve_train_name(train_no: str) -> str:
# ... (existing code ...
    try:
        return TRAIN_NO_TO_NAME.get(str(train_no).strip(), "")
    except Exception:
        return ""


# --- !! "AVENGER" AVAILABILITY FUNCTION (s.erail.in) !! ---
def get_train_availability(train_no, date, src, dst, cls, quota):
# ... (existing code ...
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
    
    # This is the form data the extension sends
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
        
        # The response is JSON
        data = response.json()
        
        # The response is a list of [date, status, probability]
        # e.g., ["31-10-2025", "RLWL 1/REFRESH", "90%"]
        if data and isinstance(data, list) and len(data[0]) > 1:
            # We just want the status string
            availability = data[0][1] # "RLWL 1/REFRESH"
            return [f"{formatted_date}: {availability}"]
        else:
            return ["No data found."]

    except Exception as e:
        print(f"Error fetching availability from s.erail.in: {e}")
        return []


# --- !! THIS IS YOUR WORKING "ETRAIN.INFO" SCRAPER !! ---
def get_trains_between(src, dst, date_str_yyyy_mm_dd):
# ... (existing code ...
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
    # --- !! SYNTAX ERROR FIX !! ---
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

        # --- 4. Parse the table (based on your output) ---
        # Your output: 12844 | ADI PURI SF EXP | UDN | 23:05 | BAM | 04:07 | 29:02H | ... | 2A 3A SL
        
        for row in rows[1:]: # Skip header
            try:
                cols = row.find_all('td')
                if len(cols) < 8: # Not a valid train row
                    continue
                
                # Use get_text for robustness
                number = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True)
                dep = cols[3].get_text(strip=True)
                arr = cols[5].get_text(strip=True)
                dur = cols[6].get_text(strip=True)
                
                # --- NEW: Parse classes into a clean list ---
                classes_text = cols[-1].get_text(" ", strip=True) # "2A 3A SL"
                classes_list = classes_text.split() # ["2A", "3A", "SL"]

                if number and name:
                    # --- !! NEW: Return a dictionary !! ---
                    trains_list.append({
                        "number": number,
                        "name": name,
                        "dep": dep,
                        "arr": arr,
                        "dur": dur,
                        "classes": classes_list # Return the list, not a string
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
# ... (existing code ...
    if not selected_date:
        selected_date = datetime.now().strftime("%Y-%m-%d")
    try:
        formatted_ui_date = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%m/%d/%y")
    except Exception:
        formatted_ui_date = datetime.now().strftime("%m/%d/%y")

    blank_ticket = {
        "source": "", "destination": "", "passengers": [],
        # --- !! FIX: Set defaults to True as requested !! ---
        "auto_upgrade": True,
        "confirm_berth": True,
        "ticket_name": "", "fare_limit": "",
        "irctc_id": "", "payment": "",
        "selected_train": "", "class": "SL", "quota": "GN", "train_no": "",
        "date": formatted_ui_date,
        "mobile": ""
    }
    open_new_ticket_autofill(blank_ticket)

# --- Function to Open Ticket Window (Polished & Fixed) ---
def open_new_ticket_autofill(ticket):
# ... (existing code ...
    win = tk.Toplevel()
    win.title(f"NEW-TICKET")
    win.geometry("800x600") # Adjusted height
    win.configure(bg="black")

    # Load IRCTC IDs
    try:
        with open("irctc_ids.json", "r") as f:
            irctc_data = json.load(f)
            irctc_users = [entry["user"] for entry in irctc_data]
    except:
        irctc_users = []
    # Load UPI IDs
    try:
        with open("payment_list.json", "r") as f:
            payment_data = json.load(f)
            upi_ids = [entry["upi"] for entry in payment_data]
    except:
        upi_ids = []

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
    class_combo_main = ttk.Combobox(win, values=["SL", "3A", "2A", "1A", "CC", "2S", "3E", "FC", "EC"], width=4) # Added all classes
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

    tk.Button(win, text="Random", bg="green", fg="black", command=lambda: print("Random clicked")).place(x=730, y=52)

    # --- Find Train Button (Main Window) ---
    def open_train_popup():
        train_popup = tk.Toplevel(win)
        train_popup.title("Train Between")
        # --- !! NEW: Compact Geometry !! ---
        train_popup.geometry("650x380") # Compact
        train_popup.configure(bg="black")
        
        # --- !! NEW: Remove OS Title Bar !! ---
        train_popup.overrideredirect(True)

        # --- !! NEW: Draggable Title Bar !! ---
        title_bar = tk.Frame(train_popup, bg="#39FF14", relief="raised", bd=0, height=25)
        title_bar.pack(fill="x")

        title_label = tk.Label(title_bar, text="Train Between", bg="#39FF14", fg="black", font=("Arial", 10, "bold"))
        title_label.pack(side="left", padx=10)

        # --- !! NEW: Single Close Button !! ---
        close_button = tk.Button(title_bar, text="X", bg="red", fg="white", font=("Arial", 10, "bold"),
                                 width=3, bd=0, command=train_popup.destroy)
        close_button.pack(side="right")

        # --- !! NEW: Make Window Draggable !! ---
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
        # --- !! END DRAGGABLE LOGIC !! ---

        # --- !! NEW: Compact Control Frame (using grid) !! ---
        controls_frame = tk.Frame(train_popup, bg="black")
        controls_frame.pack(fill="x", padx=10, pady=5)

        # Column 0
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
        date_entry.insert(0, ticket.get("date", datetime.now().strftime("%m/%d/%y")))
        
        # Column 2
        tk.Label(controls_frame, text="Quota:", fg="lime", bg="black").grid(row=0, column=2, sticky="w", padx=5)
        quota_var = tk.StringVar()
        quota_combo = ttk.Combobox(controls_frame, values=["GN", "TQ", "LD", "SS", "DF", "PH"], width=10, textvariable=quota_var)
        quota_combo.grid(row=0, column=3, pady=2)
        quota_combo.set(ticket.get("quota", "GN"))
    
        tk.Label(controls_frame, text="Class:", fg="lime", bg="black").grid(row=1, column=2, sticky="w", padx=5)
        class_combo = ttk.Combobox(controls_frame, values=["SL", "3A", "2A", "1A", "CC", "2S", "3E", "FC", "EC"], width=10)
        class_combo.grid(row=1, column=3, pady=2)
        class_combo.set("SL")

        # Column 4 (Buttons)
        tk.Button(controls_frame, text="Search Trains", command=lambda: search_trains_popup(), bg="green", fg="black", width=15).grid(row=0, column=4, padx=10, pady=2)
        tk.Button(controls_frame, text="Check Availability", command=lambda: check_availability_popup(), bg="blue", fg="white", width=15).grid(row=1, column=4, padx=10, pady=2)

        # --- !! NEW: "AVENGER" STYLE TRAIN FRAME !! ---
        list_canvas_frame = tk.Frame(train_popup, bg="black", bd=0, highlightthickness=0)
        list_canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5)) # Removed bottom padding
        
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
        # --- !! END OF NEW LIST FRAME !! ---


        # --- !! START THREADING LOGIC (Updated for Avenger UI) !! ---

        def on_class_select(train_data, class_code):
            """
            This is the new "Confirm" function.
            It's called when a user clicks a GREEN class button.
            """
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

        
        # Helper function 1: Runs the online search in a thread
        def thread_target_search_trains(src, dst, dte, res_queue):
            """
            Threaded wrapper for the ONLINE ETRAIN.INFO scrape.
            """
            try:
                # This is the call to YOUR scrape function
                results = get_trains_between(src, dst, dte)

                error = None
                if not results:
                    error = "No trains found for this route and date."
                
                res_queue.put((results, error))
            except Exception as e:
                res_queue.put(([], f"API search error: {e}"))


        # Helper function 2: Checks the queue for results
        def poll_search_queue(res_queue):
            """This function runs on the UI thread, checking the queue."""
            try:
                # Check if the thread has put anything in the queue
                trains, error = res_queue.get_nowait() 
                
                # --- YES! Results are in ---
                # --- !! NEW: Clear loading message from frame !! ---
                for widget in scrollable_train_list_frame.winfo_children():
                    widget.destroy()

                if error:
                    messagebox.showinfo("No results", error)
                elif trains:
                    # --- !! NEW: Build the "Avenger" UI !! ---
                    
                    # This is the master list of all classes in order
                    ALL_CLASSES = ["1A", "2A", "3A", "SL", "3E", "CC", "2S", "FC", "EC"]
                    
                    for train in trains:
                        # Create a row for this train
                        row_frame = tk.Frame(scrollable_train_list_frame, bg="#222") # Dark grey bg for row
                        row_frame.pack(fill="x", expand=True, pady=1)
                        
                        # 1. Train Name Label
                        train_label_str = f"{train['number']} - {train['name']}"
                        tk.Label(row_frame, text=train_label_str, fg="white", bg="#222", font=("Arial", 9, "bold"), anchor="w").pack(side="left", padx=5, pady=2)
                        
                        # 2. Frame for the class buttons
                        class_frame = tk.Frame(row_frame, bg="#222")
                        class_frame.pack(side="right", padx=5, pady=2)

                        # Get the list of classes this train *actually* has
                        available_classes_for_this_train = train.get("classes", []) # e.g., ["2A", "3A", "SL"]

                        # 3. Create the grid of buttons
                        for class_code in ALL_CLASSES:
                            if class_code in available_classes_for_this_train:
                                # GREEN BUTTON (Available)
                                btn = tk.Button(class_frame, text=class_code, bg="green", fg="white", font=("Arial", 8, "bold"), width=4,
                                                command=lambda t=train, c=class_code: on_class_select(t, c), bd=0, activebackground="green4")
                                btn.pack(side="left", padx=1)
                            else:
                                # RED BUTTON (Not Available)
                                btn = tk.Button(class_frame, text=class_code, bg="red", fg="#555", font=("Arial", 8), width=4,
                                                state="disabled", relief="sunken", bd=0)
                                btn.pack(side="left", padx=1)
                else:
                    messagebox.showinfo("No trains", "No trains found. Try other stations or dates.")
            
            except queue.Empty:
                # --- NO results yet ---
                train_popup.after(100, poll_search_queue, res_queue)
            
            except Exception as e:
                # Handle any other error during UI update
                print(f"Error in poll_search_queue: {e}")
                tk.Label(scrollable_train_list_frame, text=f"Error: {e}", fg="red", bg="black").pack()

        # --- Popup Helper Functions (MUST be defined INSIDE open_train_popup) ---
        def search_trains_popup():
            src = from_entry.get().strip().upper()
            dst = to_entry.get().strip().upper()
            dte = date_entry.get().strip()

            if not src or not dst or not dte:
                messagebox.showerror("Error", "From, To, and Date are required.")
                return

            try:
                # Convert MM/DD/YY to YYYY-MM-DD
                dte2 = datetime.strptime(dte.replace("-", "/").replace(".", "/"), "%m/%d/%y").strftime("%Y-%m-%d")
            except Exception:
                messagebox.showerror("Error", "Date must be MM/DD/YY")
                return

            # --- !! NEW: Clear frame and show loading !! ---
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

        # --- !! END THREADING LOGIC !! ---

        def check_availability_popup():
            # This function is now a bit redundant, but we keep it
            messagebox.showinfo("Info", "This button is for a future update.\nPlease click a green class button to select a train.")

        # --- !! REMOVED 'confirm_train_popup' as it's replaced by on_class_select !! ---

    # --- End of open_train_popup function ---

    # Button on MAIN window that calls the popup function
    tk.Button(win, text="Find Train", command=open_train_popup, bg="green", fg="black", font=("Arial",10,"bold")).place(x=600, y=18) # Adjusted x

    # --- Passenger Table ---
    tk.Label(win, text="Name", fg="lime", bg="black").place(x=20, y=100)
    tk.Label(win, text="Age", fg="lime", bg="black").place(x=120, y=100)
    tk.Label(win, text="Gender", fg="lime", bg="black").place(x=170, y=100)
    tk.Label(win, text="Berth Choice", fg="lime", bg="black").place(x=260, y=100)
    tk.Label(win, text="Food Choice", fg="lime", bg="black").place(x=400, y=100)
    passenger_entries = []
    row_y = 130
    
    for i in range(6):
        row = []
        row.append(tk.Entry(win, width=13, bg="navy", fg="white")); row[-1].place(x=20, y=row_y)
        row.append(tk.Entry(win, width=4, bg="navy", fg="white")); row[-1].place(x=120, y=row_y)
        row.append(ttk.Combobox(win, values=["Male", "Female", "Other"], width=7)); row[-1].place(x=170, y=row_y)
        row.append(ttk.Combobox(win, values=["No Preference", "Lower", "Middle", "Upper", "Side Lower", "Side Upper"], width=14)); row[-1].place(x=260, y=row_y)
        row[-1].set("No Preference")
        row.append(ttk.Combobox(win, values=["No Preference", "Veg", "Non-Veg"], width=14)); row[-1].place(x=400, y=row_y)
        row[-1].set("No Preference")
        passenger_entries.append(row)
        row_y += 32
        
    # Fill passengers if any
    for i, passenger in enumerate(ticket.get("passengers", [])):
        if i<6:
            passenger_entries[i][0].insert(0, passenger.get("name", ""))
            passenger_entries[i][1].insert(0, passenger.get("age", ""))
            passenger_entries[i][2].set(passenger.get("gender", "Male"))
            passenger_entries[i][3].set(passenger.get("berth", "No Preference"))
            passenger_entries[i][4].set(passenger.get("food", "No Preference"))

    # --- Checkboxes ---
    # --- !! FIX: Set default to 'ticket' value, which is now True by default !! ---
    auto_upgrade_var = tk.BooleanVar(value=ticket.get("auto_upgrade"))
    confirm_berth_var = tk.BooleanVar(value=ticket.get("confirm_berth"))
    
    tk.Checkbutton(win, text="Consider Auto upgradation", variable=auto_upgrade_var, fg="red", bg="black", selectcolor="black", activebackground="black", activeforeground="red").place(x=20, y=340)
    tk.Checkbutton(win, text="Book only if confirm Berth Allocated", variable=confirm_berth_var, fg="red", bg="black", selectcolor="black", activebackground="black", activeforeground="red").place(x=320, y=340)

    # --- Ticket summary/lower ---
    tk.Label(win, text="Ticket Name:", fg="lime", bg="black").place(x=20, y=390)
    ticket_name_entry = tk.Entry(win, width=20, bg="navy", fg="white")
    ticket_name_entry.place(x=130, y=390)
    ticket_name_entry.insert(0, ticket.get("ticket_name", ""))

    tk.Label(win, text="PT Fare Limit:", fg="lime", bg="black").place(x=320, y=390)
    fare_limit_entry = tk.Entry(win, width=18, bg="navy", fg="white")
    fare_limit_entry.place(x=420, y=390)
    fare_limit_entry.insert(0, ticket.get("fare_limit", ""))

    tk.Label(win, text="IRCTC ID:", fg="lime", bg="black").place(x=20, y=430)
    irctc_combo = ttk.Combobox(win, values=irctc_users, width=18)
    irctc_combo.place(x=130, y=430)
    irctc_combo.set(ticket.get("irctc_id", ""))

    tk.Label(win, text="Payment:", fg="lime", bg="black").place(x=320, y=430)
    payment_combo = ttk.Combobox(win, values=upi_ids, width=18)
    payment_combo.place(x=420, y=430)
    payment_combo.set(ticket.get("payment", ""))

    # --- Save Function ---
    def save_ticket():
        ticket.update({
            "source": src_entry.get(),
            "destination": dst_entry.get(),
            "train_no": trainno_entry.get(),
            "class": class_combo_main.get(),
            "quota": quota_combo_main.get(),
            "date": date_entry_main.get(),
            "mobile": mob_entry.get(),
            "passengers": [],
            "auto_upgrade": auto_upgrade_var.get(),
            "confirm_berth": confirm_berth_var.get(),
            "ticket_name": ticket_name_entry.get(),
            "fare_limit": fare_limit_entry.get(),
            "irctc_id": irctc_combo.get(),
            "payment": payment_combo.get(),
            "selected_train": ticket.get("selected_train", ""),
        })
        
        for row in passenger_entries:
            name = row[0].get()
            age = row[1].get()
            if name and age: # Only save passengers with at least a name and age
                passenger = {
                    "name": name,
                    "age": age,
                    "gender": row[2].get(),
                    "berth": row[3].get(),
                    "food": row[4].get(),
                }
                ticket["passengers"].append(passenger)
        
        try:
            with open("ticket_list.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
            
        # Check if ticket already exists (e.g., by name) to avoid duplicates
        ticket_names = [t.get("ticket_name") for t in data]
        if ticket["ticket_name"] and ticket["ticket_name"] in ticket_names:
            print("Updating existing ticket")
            for i, t in enumerate(data):
                if t.get("ticket_name") == ticket["ticket_name"]:
                    data[i] = ticket
                    break
        else:
            print("Adding new ticket")
            data.append(ticket)
            
        try:
            with open("ticket_list.json", "w") as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Saved", "✅ Ticket saved successfully!")
            win.destroy() # Close window after saving
            # You might want to refresh the main list here
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save ticket: {e}")

    tk.Button(win, text="Save Ticket", command=save_ticket, bg="lime", fg="black", font=("Arial", 12, "bold")).place(x=320, y=495)


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

