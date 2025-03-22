import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import keyboard
import random
from collections import defaultdict

class HotkeyTrainer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hotkey Trainer")
        
        # State variables
        self.prompts = []  # List of prompt dictionaries
        self.visible_prompts = 3  # Default number of visible prompts
        self.show_hotkeys = True
        self.weights = defaultdict(lambda: 1.0)  # Weights for each prompt
        self.sequence_groups = []  # List of prompt sequences
        self.current_sequence = None
        self.consecutive_correct = defaultdict(int)  # Track consecutive correct answers
        self.current_config_file = None  # Track the currently loaded config file
        self.last_pressed_hotkey = ""  # Track the last pressed hotkey
        self.current_keys = set()  # Track currently pressed keys
        self.displayed_prompts = []  # Track currently displayed prompts
        self.wrong_attempt = False  # Track if last attempt was wrong
        
        # Key mapping for normalization
        self.modifier_map = {
            'left ctrl': 'ctrl', 'right ctrl': 'ctrl', 'control_l': 'ctrl', 'control_r': 'ctrl', 'control': 'ctrl',
            'left alt': 'alt', 'right alt': 'alt', 'alt_l': 'alt', 'alt_r': 'alt', 'alt': 'alt',
            'left shift': 'shift', 'right shift': 'shift', 'shift_l': 'shift', 'shift_r': 'shift', 'shift': 'shift',
            'left windows': 'win', 'right windows': 'win', 'windows': 'win', 'win_l': 'win', 'win_r': 'win',
            'super_l': 'win', 'super_r': 'win', 'super': 'win',  # Linux/Mac naming
            'meta_l': 'win', 'meta_r': 'win', 'meta': 'win',     # Alternative naming
            'altgr': 'alt',  # Map AltGr to Alt
        }
        
        self._setup_ui()
        self._load_keyboard_listener()
    
    def _setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Last pressed hotkey display
        hotkey_frame = ttk.Frame(self.main_frame)
        hotkey_frame.grid(row=0, column=0, pady=5)
        ttk.Label(hotkey_frame, text="Last Pressed Hotkey:").pack(side=tk.LEFT)
        self.hotkey_display = ttk.Label(hotkey_frame, text="")
        self.hotkey_display.pack(side=tk.LEFT, padx=5)
        
        # Prompts display area
        self.prompts_frame = ttk.Frame(self.main_frame)
        self.prompts_frame.grid(row=1, column=0, pady=10)
        
        # Controls
        controls_frame = ttk.Frame(self.main_frame)
        controls_frame.grid(row=2, column=0, pady=10)
        
        ttk.Button(controls_frame, text="Settings", command=self._open_settings).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(controls_frame, text="Show Hotkeys", 
                       variable=tk.BooleanVar(value=self.show_hotkeys),
                       command=self._toggle_hotkeys).pack(side=tk.LEFT, padx=5)
    
    def _open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x800")
        settings_window.transient(self.root)  # Make dialog modal
        settings_window.grab_set()  # Make dialog modal
        
        # Prompt configuration
        prompt_frame = ttk.LabelFrame(settings_window, text="Prompts", padding="10")
        prompt_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Add prompt button
        ttk.Button(prompt_frame, text="Add Prompt", 
                  command=lambda: self._add_prompt_dialog(settings_window)).pack()
        
        # Sequence groups
        sequence_frame = ttk.LabelFrame(settings_window, text="Sequence Groups", padding="10")
        sequence_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(sequence_frame, text="Enter sequence groups (format: group1: prompt1,prompt2;group2: prompt3,prompt4)").pack()
        self.sequence_entry = ttk.Entry(sequence_frame, width=50)
        self.sequence_entry.pack(pady=5)
        ttk.Button(sequence_frame, text="Add Sequence", command=self._add_sequence).pack()
        
        # Visible prompts setting
        visible_frame = ttk.LabelFrame(settings_window, text="Display Settings", padding="10")
        visible_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(visible_frame, text="Number of Visible Prompts:").pack(side=tk.LEFT)
        visible_var = tk.StringVar(value=str(self.visible_prompts))
        visible_spinbox = ttk.Spinbox(visible_frame, from_=1, to=10, width=5,
                                    textvariable=visible_var,
                                    command=lambda: self._update_visible_prompts(visible_var.get()))
        visible_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Config display
        config_frame = ttk.LabelFrame(settings_window, text="Current Configuration", padding="10")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create a canvas with scrollbar for the config list
        canvas = tk.Canvas(config_frame)
        scrollbar = ttk.Scrollbar(config_frame, orient="vertical", command=canvas.yview)
        self.config_list_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=self.config_list_frame, anchor="nw")
        
        self._update_config_display()
        
        # File operations
        file_frame = ttk.Frame(settings_window, padding="10")
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(file_frame, text="Save As", 
                  command=self._save_config_as).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Save", 
                  command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Load Configuration", 
                  command=self._load_config).pack(side=tk.LEFT, padx=5)
        
        def on_settings_close():
            settings_window.destroy()
            # Force update of main window display
            self.displayed_prompts = []  # Reset displayed prompts
            self._update_display()
        
        settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)
    
    def _update_config_display(self):
        # Clear existing items
        for widget in self.config_list_frame.winfo_children():
            widget.destroy()
        
        # Display prompts
        ttk.Label(self.config_list_frame, text="Prompts:", font=("", 10, "bold")).pack(anchor="w")
        for prompt in self.prompts:
            frame = ttk.Frame(self.config_list_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{prompt['name']} - {prompt['hotkey']} (weight: {prompt['weight']})").pack(side=tk.LEFT)
            ttk.Button(frame, text="×", width=3,
                      command=lambda p=prompt: self._delete_prompt(p)).pack(side=tk.RIGHT)
        
        # Display sequence groups
        if self.sequence_groups:
            ttk.Label(self.config_list_frame, text="\nSequence Groups:", font=("", 10, "bold")).pack(anchor="w")
            for i, group in enumerate(self.sequence_groups):
                frame = ttk.Frame(self.config_list_frame)
                frame.pack(fill=tk.X, pady=2)
                ttk.Label(frame, text=f"Group {i+1}: {','.join(group)}").pack(side=tk.LEFT)
                ttk.Button(frame, text="×", width=3,
                          command=lambda idx=i: self._delete_sequence(idx)).pack(side=tk.RIGHT)
    
    def _delete_prompt(self, prompt):
        self.prompts.remove(prompt)
        self._update_config_display()
        self._update_display()
    
    def _delete_sequence(self, index):
        del self.sequence_groups[index]
        self._update_config_display()
    
    def _add_sequence(self):
        sequence_text = self.sequence_entry.get()
        try:
            # Parse the sequence text
            groups = sequence_text.split(';')
            for group in groups:
                if not group.strip():
                    continue
                name, prompts = group.split(':')
                prompt_list = [p.strip() for p in prompts.split(',')]
                self.sequence_groups.append(prompt_list)
            self.sequence_entry.delete(0, tk.END)
            self._update_config_display()
        except:
            messagebox.showerror("Error", "Invalid sequence format. Please use the format: group1: prompt1,prompt2;group2: prompt3,prompt4")
    
    def _add_prompt_dialog(self, parent):
        dialog = tk.Toplevel(parent)
        dialog.title("Add Prompt")
        dialog.transient(parent)  # Make dialog modal
        dialog.grab_set()  # Make dialog modal
        
        # Temporarily disable global keyboard hook
        keyboard.unhook_all()
        
        ttk.Label(dialog, text="Prompt Name:").pack(pady=5)
        name_entry = ttk.Entry(dialog)
        name_entry.pack(pady=5)
        
        # Create a frame for hotkey input
        hotkey_frame = ttk.LabelFrame(dialog, text="Hotkey Input", padding="10")
        hotkey_frame.pack(pady=10, padx=10, fill=tk.X)
        
        hotkey_entry = ttk.Entry(hotkey_frame, state='readonly')
        hotkey_entry.pack(pady=5, fill=tk.X)
        
        hotkey_status = ttk.Label(hotkey_frame, text="Click here and press your hotkey combination...")
        hotkey_status.pack(pady=5)
        
        ttk.Label(dialog, text="Weight:").pack(pady=5)
        weight_entry = ttk.Entry(dialog)
        weight_entry.insert(0, "1.0")
        weight_entry.pack(pady=5)
        
        dialog_keys = set()
        current_hotkey = [""]  # Use a list to store the current hotkey
        is_capturing_hotkey = False
        
        def start_hotkey_capture():
            nonlocal is_capturing_hotkey
            is_capturing_hotkey = True
            dialog_keys.clear()
            current_hotkey[0] = ""
            hotkey_entry.config(state='normal')
            hotkey_entry.delete(0, tk.END)
            hotkey_entry.config(state='readonly')
            hotkey_status.config(text="Press your hotkey combination... (Click again to stop)")
            hotkey_frame.config(relief="sunken")
        
        def stop_hotkey_capture():
            nonlocal is_capturing_hotkey
            is_capturing_hotkey = False
            hotkey_status.config(text="Click here to capture a hotkey combination")
            hotkey_frame.config(relief="raised")
        
        def on_hotkey_frame_click(event):
            if is_capturing_hotkey:
                stop_hotkey_capture()
            else:
                start_hotkey_capture()
        
        def on_dialog_key(event):
            if not is_capturing_hotkey:
                return
            
            # Convert event.keysym to a more readable format and normalize it
            key_name = self._normalize_key(event.keysym.lower())
            
            if event.type == tk.EventType.KeyPress:
                if key_name not in dialog_keys:
                    dialog_keys.add(key_name)
                    current_hotkey[0] = self._normalize_hotkey(dialog_keys)
                    hotkey_entry.config(state='normal')
                    hotkey_entry.delete(0, tk.END)
                    hotkey_entry.insert(0, current_hotkey[0])
                    hotkey_entry.config(state='readonly')
            elif event.type == tk.EventType.KeyRelease:
                if key_name in dialog_keys:
                    dialog_keys.remove(key_name)
            
            return "break" if is_capturing_hotkey else None
        
        hotkey_frame.bind('<Button-1>', on_hotkey_frame_click)
        dialog.bind('<KeyPress>', on_dialog_key)
        dialog.bind('<KeyRelease>', on_dialog_key)
        
        def save_prompt():
            if not name_entry.get() or not current_hotkey[0]:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            try:
                weight = float(weight_entry.get())
                self.prompts.append({
                    "name": name_entry.get(),
                    "hotkey": current_hotkey[0],
                    "weight": weight
                })
                dialog.destroy()
                # Restore global keyboard hook
                self._load_keyboard_listener()
                self._update_config_display()
            except ValueError:
                messagebox.showerror("Error", "Weight must be a number")
        
        def on_dialog_close():
            dialog.destroy()
            # Restore global keyboard hook
            self._load_keyboard_listener()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        ttk.Button(dialog, text="Save", command=save_prompt).pack(pady=10)
        
        # Set initial focus to name entry
        name_entry.focus_set()
    
    def _save_config_as(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            self.current_config_file = filename
            self._save_config()
    
    def _save_config(self):
        if not self.current_config_file:
            self._save_config_as()
            return
            
        config = {
            "prompts": self.prompts,
            "visible_prompts": self.visible_prompts,
            "sequence_groups": self.sequence_groups
        }
        with open(self.current_config_file, 'w') as f:
            json.dump(config, f)
    
    def _load_config(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, 'r') as f:
                config = json.load(f)
                self.prompts = config["prompts"]
                self.visible_prompts = config["visible_prompts"]
                self.sequence_groups = config.get("sequence_groups", [])
                self.current_config_file = filename
                self._update_display()
                self._update_config_display()
    
    def _toggle_hotkeys(self):
        self.show_hotkeys = not self.show_hotkeys
        self._update_display()
    
    def _update_display(self):
        # Clear existing prompts
        for widget in self.prompts_frame.winfo_children():
            widget.destroy()
        
        # Get next prompts if we don't have enough displayed
        if not self.displayed_prompts:
            next_prompts = self._get_next_prompts()
            if next_prompts:
                self.displayed_prompts = next_prompts
        
        # Display prompts
        for i, prompt in enumerate(self.displayed_prompts):
            frame = ttk.Frame(self.prompts_frame)
            frame.pack(fill=tk.X, pady=2)
            
            name = prompt["name"]
            hotkey = f" ({prompt['hotkey']})" if self.show_hotkeys else ""
            
            # Create a horizontal container for the prompt and indicator
            content_frame = ttk.Frame(frame)
            content_frame.pack(fill=tk.X, expand=True)
            
            # Add the prompt text
            ttk.Label(content_frame, text=f"{name}{hotkey}").pack(side=tk.LEFT)
            
            # Add red circle indicator if this is the bottom prompt and there was a wrong attempt
            if i == len(self.displayed_prompts) - 1 and self.wrong_attempt:
                canvas = tk.Canvas(content_frame, width=10, height=10, highlightthickness=0)
                canvas.pack(side=tk.LEFT, padx=5)
                canvas.create_oval(2, 2, 8, 8, fill='red', outline='red')
    
    def _get_next_prompts(self):
        if not self.prompts:
            return []
        
        # Handle sequences
        if self.current_sequence:
            if len(self.current_sequence) >= self.visible_prompts:
                return self.current_sequence[:self.visible_prompts]
            else:
                self.current_sequence = None
        
        # Select prompts based on weights
        weights = [self.weights[p["name"]] * p["weight"] for p in self.prompts]
        selected = random.choices(self.prompts, weights=weights, k=self.visible_prompts)
        
        return selected
    
    def _normalize_key(self, key):
        """Normalize key names to handle modifiers consistently."""
        key = key.lower()
        return self.modifier_map.get(key, key)

    def _normalize_hotkey(self, keys):
        """Normalize a set of keys into a consistent hotkey string."""
        normalized = {self._normalize_key(k) for k in keys}
        return '+'.join(sorted(normalized))

    def _update_visible_prompts(self, value):
        try:
            new_value = int(value)
            if 1 <= new_value <= 10:
                old_value = self.visible_prompts
                self.visible_prompts = new_value
                # Only reset display if the value actually changed
                if old_value != new_value:
                    self.displayed_prompts = []  # Reset displayed prompts
                    self._update_display()
        except ValueError:
            pass

    def _load_keyboard_listener(self):
        def on_key_down(event):
            # Only process if main window is focused and not in a dialog
            if not self.root.focus_displayof() or any(w.winfo_exists() for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)):
                return

            # Normalize the key name
            key_name = self._normalize_key(event.name)
            self.current_keys.add(key_name)
            
            # Update display with normalized hotkey
            hotkey_name = self._normalize_hotkey(self.current_keys)
            self.last_pressed_hotkey = hotkey_name
            self.hotkey_display.config(text=hotkey_name)
            
            if not self.displayed_prompts:  # Skip if no prompts are displayed
                return
            
            # Get the bottom-most prompt
            current_prompt = self.displayed_prompts[-1]
            
            # Update weights regardless of position
            if hotkey_name == current_prompt["hotkey"]:
                self.consecutive_correct[current_prompt["name"]] += 1
                if self.consecutive_correct[current_prompt["name"]] > 2:
                    self.weights[current_prompt["name"]] *= 0.8
                
                # Only update display if the bottom-most prompt was correct
                self.wrong_attempt = False
                
                # Remove the completed prompt
                self.displayed_prompts.pop()
                
                # Add a new prompt at the top if we have room
                if len(self.displayed_prompts) < self.visible_prompts:
                    next_prompts = self._get_next_prompts()
                    if next_prompts:
                        self.displayed_prompts.insert(0, next_prompts[0])
            else:
                self.weights[current_prompt["name"]] *= 1.2
                self.consecutive_correct[current_prompt["name"]] = 0
                self.wrong_attempt = True
            
            self._update_display()
            return False  # Prevent default handling for all keys
        
        def on_key_up(event):
            normalized_key = self._normalize_key(event.name)
            if normalized_key in self.current_keys:
                self.current_keys.remove(normalized_key)
            return False  # Prevent default handling for all keys
        
        keyboard.on_press(on_key_down, suppress=True)
        keyboard.on_release(on_key_up, suppress=True)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HotkeyTrainer()
    app.run()
