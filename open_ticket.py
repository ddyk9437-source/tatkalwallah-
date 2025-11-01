import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
# --- FIX: This import is the crucial link to the cockpit window
from irctc_launcher import open_ticket_launcher 
# --- FIX: This import is for the "Edit" button
from new_ticket import open_new_ticket_autofill

TICKET_FILE = "ticket_list.json"

def load_tickets():
    """Loads tickets from the JSON file."""
    if not os.path.exists(TICKET_FILE):
        return []
    try:
        with open(TICKET_FILE, "r") as f:
            data = json.load(f)
            # Ensure data is a list and items have IDs
            valid_data = []
            if isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        # --- POLISH: Ensure every ticket has a unique ID ---
                        if "id" not in item or not item["id"]:
                            # --- FIX: Use ticket_name or generate new ID ---
                            item["id"] = item.get("ticket_name", f"ticket_{i+1}_{os.urandom(4).hex()}")
                        valid_data.append(item)
                if len(valid_data) != len(data):
                    # If we had to add IDs, resave the file
                    save_tickets(valid_data) 
                return valid_data
            else:
                return [] # File is not a list
    except Exception as e:
        print(f"Error loading {TICKET_FILE}: {e}")
        messagebox.showerror("Load Error", f"Failed to load {TICKET_FILE}.\nFile might be corrupted.\n{e}")
        return []

def save_tickets(tickets):
    """Saves the list of tickets to the JSON file."""
    try:
        with open(TICKET_FILE, "w") as f:
            json.dump(tickets, f, indent=4)
    except Exception as e:
        print(f"Error saving {TICKET_FILE}: {e}")
        messagebox.showerror("Save Error", f"Failed to save {TICKET_FILE}.\n{e}")

def open_saved_ticket():
    """
    Opens the 'Tesla-style' ticket list window.
    """
    win = tk.Toplevel()
    win.title("Open Ticket")
    win.geometry("850x400") 
    win.configure(bg="#1e1e1e") 
    
    # --- Custom Title Bar (for dragging and closing) ---
    win.overrideredirect(True)
    title_bar = tk.Frame(win, bg="orange", relief="raised", bd=0, height=25)
    title_bar.pack(fill="x")
    
    title_label = tk.Label(title_bar, text="Select Ticket", bg="orange", fg="black", font=("Arial", 10, "bold"))
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

    # --- Header ---
    header_frame = tk.Frame(win, bg="#1e1e1e")
    header_frame.pack(fill="x", padx=10, pady=5)
    total_label = tk.Label(header_frame, text="Total Ticket   00", bg="orange", fg="black", font=("Arial", 10, "bold"), padx=10)
    total_label.pack(side="left")

    # --- Treeview (Ticket List) ---
    style = ttk.Style(win) 
    
    style.configure("Treeview", 
                    rowheight=25, 
                    font=("Arial", 9), 
                    fieldbackground="#2a2a2a", 
                    background="#2a2a2a", 
                    foreground="white")
    style.configure("Treeview.Heading", 
                    font=("Arial", 10, "bold"), 
                    background="orange", 
                    foreground="black",
                    relief="flat")
    style.map("Treeview", 
              background=[('selected', 'lime')], 
              foreground=[('selected', 'black')])

    tree_frame = tk.Frame(win, bg="#1e1e1e")
    tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # --- Define ALL columns, including action buttons ---
    cols_data = ("#", "Name", "From", "To", "Date", "QT", "CLS", "Train", "SLOT", "Web", "App")
    cols_actions = ("Open", "Login", "Edit", "Delete")
    cols_all = cols_data + cols_actions
    
    tree = ttk.Treeview(tree_frame, columns=cols_all, show="headings", style="Treeview")
    
    col_widths = {
        "#": 30, "Name": 100, "From": 60, "To": 60, "Date": 80, "QT": 40, 
        "CLS": 40, "Train": 70, "SLOT": 60, "Web": 40, "App": 40,
        "Open": 50, "Login": 50, "Edit": 50, "Delete": 50
    }
    
    for col in cols_all:
        tree.column(col, width=col_widths.get(col, 60), anchor="center")
        tree.heading(col, text=col)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    
    # --- Bottom Buttons ---
    bottom_frame = tk.Frame(win, bg="#1e1e1e")
    bottom_frame.pack(fill="x", padx=10, pady=10)
    
    btn_style = {"bg": "orange", "fg": "black", "font": ("Arial", 10, "bold"), "width": 12, "bd": 1, "relief": "solid"}
    delete_all_btn = tk.Button(bottom_frame, text="Delete All", **btn_style)
    delete_all_btn.pack(side="left", padx=20)
    
    open_all_btn = tk.Button(bottom_frame, text="Open All Ticket", **btn_style)
    open_all_btn.pack(side="left", padx=20)

    # --- Functions ---
    
    def refresh_ticket_list():
        """Clears and reloads the tree with data from ticket_list.json."""
        for i in tree.get_children():
            tree.delete(i)
            
        tickets = load_tickets()
        for i, ticket in enumerate(tickets, 1):
            # ---
            # --- !! THIS IS THE MAIN FIX !! ---
            # --- We are now using the correct keys from new_ticket.py ---
            # ---
            values = (
                f"{i:02d}", # Row number
                ticket.get("ticket_name", "N/A"), # FIX: Was "name"
                ticket.get("source", "N/A"),      # FIX: Was "from_station"
                ticket.get("destination", "N/A"), # FIX: Was "to_station"
                ticket.get("date", "N/A"),        # FIX: Was "journey_date"
                ticket.get("quota", "N/A"),       # (Correct)
                ticket.get("class", "N/A"),       # FIX: Was "class_code"
                ticket.get("train_no", "N/A"),    # (Correct)
                ticket.get("slot", "N/A"),        # FIX: Add .get()
                ticket.get("web", 0),             # FIX: Add .get()
                ticket.get("app", 0),             # FIX: Add .get()
                "Open",
                "Login",
                "Edit",
                "Delete"
            )
            
            # --- FIX: Use the 'id' field from the ticket as the iid ---
            tree.insert("", "end", iid=ticket.get("id"), values=values) 
        
        total_label.config(text=f"Total Ticket   {len(tickets):02d}")

    def on_tree_click(event):
        """Handles clicks inside the treeview to simulate buttons."""
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        col_id = tree.identify_column(event.x)
        try:
            col_index = int(col_id.replace("#", "")) - 1
        except ValueError:
            return 
            
        if col_index < 0 or col_index >= len(cols_all):
            return
            
        col_name = cols_all[col_index]
        
        selected_iid = tree.focus()
        if not selected_iid:
            return

        # Get all ticket data for the selected row
        all_tickets = load_tickets()
        # --- FIX: Find ticket by 'id' which is stored in iid ---
        ticket_data = next((t for t in all_tickets if t.get("id") == selected_iid), None)
        
        if not ticket_data:
            messagebox.showerror("Error", "Could not find ticket data.", parent=win)
            return

        # --- Handle Button Clicks ---
        if col_name == "Open":
            print(f"Opening cockpit for: {ticket_data.get('ticket_name')}")
            open_ticket_launcher(
                parent=win,
                ticket_data=ticket_data 
            )
            
        elif col_name == "Login":
            print(f"Login logic for {ticket_data.get('irctc_id')} goes here.")
            messagebox.showinfo("Login", f"Login logic for {ticket_data.get('irctc_id')} coming soon.", parent=win)
            
        elif col_name == "Edit":
            print(f"Editing: {ticket_data.get('ticket_name')}")
            # --- 
            # --- !! FIX: "Edit" button now works !! ---
            # ---
            # Pass the full ticket dictionary to the autofill function
            open_new_ticket_autofill(ticket_data)
            # --- After the edit window closes, refresh this list ---
            win.after(100, refresh_ticket_list) # Refresh after a short delay
            
        elif col_name == "Delete":
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{ticket_data.get('ticket_name')}'?", parent=win):
                all_tickets.remove(ticket_data)
                save_tickets(all_tickets)
                refresh_ticket_list()
                print(f"Deleted: {ticket_data.get('ticket_name')}")
        
    def style_action_cells(event):
        """Changes cursor to hand when hovering over action buttons."""
        region = tree.identify_region(event.x, event.y)
        if region == "cell":
            col_id = tree.identify_column(event.x)
            try:
                col_index = int(col_id.replace("#", "")) - 1
                if col_index >= 0 and cols_all[col_index] in cols_actions:
                    tree.config(cursor="hand2")
                else:
                    tree.config(cursor="")
            except ValueError:
                tree.config(cursor="")
        else:
            tree.config(cursor="")

    def on_delete_all():
        """Deletes all tickets from the file."""
        if messagebox.askyesno("Confirm Delete All", "Are you sure you want to delete ALL tickets?\nThis cannot be undone.", parent=win, icon='warning'):
            save_tickets([]) # Save an empty list
            refresh_ticket_list()
            print("Deleted all tickets.")
            
    def on_open_all():
        """Opens all tickets in separate cockpits."""
        if messagebox.askyesno("Confirm Open All", "Are you sure you want to open all tickets?", parent=win):
            all_tickets = load_tickets()
            if not all_tickets:
                messagebox.showinfo("Empty", "No tickets to open.", parent=win)
                return
                
            for ticket_data in all_tickets:
                print(f"Opening cockpit for: {ticket_data.get('ticket_name')}")
                open_ticket_launcher(
                    parent=win,
                    ticket_data=ticket_data
                )

    # --- Bind Events ---
    tree.bind("<Button-1>", on_tree_click)
    tree.bind("<Motion>", style_action_cells) # Add hover effect
    delete_all_btn.config(command=on_delete_all)
    open_all_btn.config(command=on_open_all)
    
    # --- Initial Load ---
    refresh_ticket_list()

    # --- Make window modal ---
    win.transient(win.master)
    win.grab_set()

# --- This allows you to test this file directly ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main Root")
    root.geometry("200x200")
    
    # --- FIX: Dummy data now uses the CORRECT keys ---
    if not os.path.exists(TICKET_FILE):
        dummy_tickets = [
            {
                "id": "t1_abc", 
                "ticket_name": "BAM_ST_JITU", 
                "source": "BAM", 
                "destination": "ST", 
                "date": "02-11-2025", 
                "quota": "PT", 
                "class": "SL", 
                "train_no": "20819",
                "slot": "Slot-1",
                "web": 1,
                "app": 0,
                "irctc_id": "jitu123",
                "payment": "jitu@upi",
                "passengers": [{"name": "Jitu", "age": "25", "gender": "Male", "berth": "Lower", "food": "Veg"}]
            },
            {
                "id": "t2_def", 
                "ticket_name": "NDLS_BCT_RAJ", 
                "source": "NDLS", 
                "destination": "BCT", 
                "date": "10-12-2025", 
                "quota": "GN", 
                "class": "1A", 
                "train_no": "12952",
                "slot": "Slot-2",
                "web": 0,
                "app": 1,
                "irctc_id": "rajdhani_user",
                "payment": "raj@upi",
                "passengers": [{"name": "Raj", "age": "40", "gender": "Male", "berth": "Upper", "food": "Non-Veg"}]
            }
        ]
        save_tickets(dummy_tickets)

    tk.Button(root, text="Test Open Ticket List", command=open_saved_ticket).pack(pady=50)
    root.mainloop()

