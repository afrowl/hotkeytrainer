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
        self.waiting_for_combination = False  # Track if we're waiting for a complete combination
        self.target_hotkey_parts = set()  # Track parts of the target hotkey
        
        # Key mapping for normalization
        self.modifier_map = {
            # Ctrl variants
            'left ctrl': 'ctrl', 'right ctrl': 'ctrl', 'control_l': 'ctrl', 'control_r': 'ctrl', 'control': 'ctrl',
            'strg': 'ctrl',  # German
            # Alt variants
            'left alt': 'alt', 'right alt': 'alt', 'alt_l': 'alt', 'alt_r': 'alt', 'alt': 'alt',
            'alt gr': 'alt', 'altgr': 'alt', 'alt_graph': 'alt',  # AltGr variants
            # Shift variants
            'left shift': 'shift', 'right shift': 'shift', 'shift_l': 'shift', 'shift_r': 'shift', 'shift': 'shift',
            'umschalt': 'shift',  # German
            # Windows/Super/Meta variants
            'left windows': 'win', 'right windows': 'win', 'windows': 'win', 'win_l': 'win', 'win_r': 'win',
            'super_l': 'win', 'super_r': 'win', 'super': 'win',
            'meta_l': 'win', 'meta_r': 'win', 'meta': 'win',
        }
        
        # Common key name normalizations
        self.key_map = {
            # Special characters
            'minus': '-', 'plus': '+', 'comma': ',', 'period': '.', 'dot': '.',
            'slash': '/', 'backslash': '\\', 'semicolon': ';', 'colon': ':',
            'bracketleft': '[', 'bracketright': ']', 'braceleft': '{', 'braceright': '}',
            'parenleft': '(', 'parenright': ')', 'equal': '=', 'quotedbl': '"',
            'apostrophe': "'", 'grave': '`', 'asciitilde': '~', 'numbersign': '#',
            'dollar': '$', 'percent': '%', 'ampersand': '&', 'asterisk': '*',
            'question': '?', 'exclaim': '!', 'at': '@', 'asciicircum': '^',
            'underscore': '_', 'space': 'space',
            # Function keys
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5',
            'f6': 'f6', 'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10',
            'f11': 'f11', 'f12': 'f12',
            # Navigation keys
            'return': 'enter', 'enter': 'enter',
            'escape': 'esc', 'esc': 'esc',
            'tab': 'tab',
            'backspace': 'backspace',
            'delete': 'del', 'del': 'del',
            'insert': 'ins', 'ins': 'ins',
            'home': 'home', 'end': 'end',
            'pageup': 'pgup', 'pgup': 'pgup', 'prior': 'pgup',
            'pagedown': 'pgdn', 'pgdn': 'pgdn', 'next': 'pgdn',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            # German specific
            'adiaeresis': 'ä', 'odiaeresis': 'ö', 'udiaeresis': 'ü',
            'ssharp': 'ß',
            # Number pad
            'kp_0': '0', 'kp_1': '1', 'kp_2': '2', 'kp_3': '3', 'kp_4': '4',
            'kp_5': '5', 'kp_6': '6', 'kp_7': '7', 'kp_8': '8', 'kp_9': '9',
            'kp_decimal': '.', 'kp_divide': '/', 'kp_multiply': '*',
            'kp_subtract': '-', 'kp_add': '+', 'kp_enter': 'enter',
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
        
        # Add focus handlers for the sequence entry
        def on_sequence_entry_focus(event):
            keyboard.unhook_all()
        
        def on_sequence_entry_focusout(event):
            self._load_keyboard_listener()
        
        self.sequence_entry.bind('<FocusIn>', on_sequence_entry_focus)
        self.sequence_entry.bind('<FocusOut>', on_sequence_entry_focusout)
        
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
                
                # Create weight entry
                weight_var = tk.StringVar(value=str(group.get("weight", 1.0)))
                weight_entry = ttk.Entry(frame, textvariable=weight_var, width=8)
                
                # Update weight when changed
                def update_weight(idx=i, var=weight_var):
                    try:
                        self.sequence_groups[idx]["weight"] = float(var.get())
                    except ValueError:
                        var.set("1.0")
                        self.sequence_groups[idx]["weight"] = 1.0
                
                weight_var.trace_add("write", lambda *args, idx=i, var=weight_var: update_weight(idx, var))
                
                ttk.Label(frame, text=f"Group {i+1}: {group['name']} - {','.join(group['prompts'])}").pack(side=tk.LEFT)
                ttk.Label(frame, text="Weight:").pack(side=tk.RIGHT, padx=(5, 0))
                weight_entry.pack(side=tk.RIGHT, padx=(0, 5))
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
                self.sequence_groups.append({
                    "name": name.strip(),
                    "prompts": prompt_list,
                    "weight": 1.0  # Default weight
                })
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
        
        # Make the hotkey input area more visible with a distinct background
        hotkey_area = ttk.Frame(hotkey_frame)
        hotkey_area.pack(fill=tk.X, pady=5, padx=5)
        
        # Create a border effect
        hotkey_area.configure(relief="solid", borderwidth=1)
        
        hotkey_entry = ttk.Entry(hotkey_area, state='readonly', justify='center')
        hotkey_entry.pack(pady=5, padx=5, fill=tk.X)
        
        hotkey_status = ttk.Label(hotkey_area, text="Click here or press Tab to capture hotkey...", wraplength=300)
        hotkey_status.pack(pady=5, padx=5)
        
        dialog_keys = set()
        current_hotkey = [""]  # Use a list to store the current hotkey
        is_capturing_hotkey = [False]  # Use a list to store the state
        
        def start_hotkey_capture():
            is_capturing_hotkey[0] = True
            dialog_keys.clear()
            current_hotkey[0] = ""
            hotkey_entry.config(state='normal')
            hotkey_entry.delete(0, tk.END)
            hotkey_entry.config(state='readonly')
            hotkey_status.config(text="Press your hotkey combination... (Click again to stop)")
            hotkey_area.configure(relief="sunken")
            
            # Set up keyboard hook for capturing
            keyboard.hook(on_dialog_key_event, suppress=True)
        
        def stop_hotkey_capture():
            is_capturing_hotkey[0] = False
            hotkey_status.config(text="Click here or press Tab to capture hotkey...")
            hotkey_area.configure(relief="solid")
            
            # Remove keyboard hook
            keyboard.unhook_all()
        
        def on_dialog_key_event(event):
            if not is_capturing_hotkey[0]:
                return
            
            # Get the key name and normalize it
            key_name = event.name
            normalized_key = self._normalize_key(key_name)
            
            if event.event_type == keyboard.KEY_DOWN:
                if normalized_key not in dialog_keys:
                    dialog_keys.add(normalized_key)
                    current_hotkey[0] = self._normalize_hotkey(dialog_keys)
                    hotkey_entry.config(state='normal')
                    hotkey_entry.delete(0, tk.END)
                    hotkey_entry.insert(0, current_hotkey[0])
                    hotkey_entry.config(state='readonly')
            elif event.event_type == keyboard.KEY_UP:
                if normalized_key in dialog_keys:
                    dialog_keys.remove(normalized_key)
            
            return False  # Always suppress when capturing
        
        # Make the entire area clickable
        def on_area_click(event):
            if is_capturing_hotkey[0]:
                stop_hotkey_capture()
            else:
                start_hotkey_capture()
        
        hotkey_area.bind('<Button-1>', on_area_click)
        hotkey_entry.bind('<Button-1>', on_area_click)
        hotkey_status.bind('<Button-1>', on_area_click)
        
        # Add tab navigation
        def on_tab_focus(event):
            if not is_capturing_hotkey[0]:
                start_hotkey_capture()
            return "break"  # Prevent default tab behavior
        
        hotkey_area.bind('<FocusIn>', on_tab_focus)
        hotkey_entry.bind('<FocusIn>', on_tab_focus)
        hotkey_status.bind('<FocusIn>', on_tab_focus)
        
        # Make the area focusable via Tab
        hotkey_area.configure(takefocus=1)
        hotkey_entry.configure(takefocus=1)
        
        ttk.Label(dialog, text="Weight:").pack(pady=5)
        weight_entry = ttk.Entry(dialog)
        weight_entry.insert(0, "1.0")
        weight_entry.pack(pady=5)
        
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
            stop_hotkey_capture()  # Make sure to stop capturing
            dialog.destroy()
            # Restore global keyboard hook
            self._load_keyboard_listener()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        ttk.Button(dialog, text="Save", command=save_prompt).pack(pady=10)
        
        # Set initial focus to name entry
        name_entry.focus_set()
    
    def _save_config_as(self):
        # Temporarily disable keyboard hook
        keyboard.unhook_all()
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        # Restore keyboard hook
        self._load_keyboard_listener()
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
        # Temporarily disable keyboard hook
        keyboard.unhook_all()
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        # Restore keyboard hook
        self._load_keyboard_listener()
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
        # Only update if the prompts have changed
        current_prompts = [(p["name"], p["hotkey"]) for p in self.displayed_prompts]
        
        # Get next prompts if we don't have enough displayed
        if not self.displayed_prompts:
            next_prompts = self._get_next_prompts()
            if next_prompts:
                self.displayed_prompts = next_prompts
                current_prompts = [(p["name"], p["hotkey"]) for p in self.displayed_prompts]
        
        # Check if we need to update the display
        widgets = self.prompts_frame.winfo_children()
        if len(widgets) == len(self.displayed_prompts):
            needs_update = False
            for i, (widget, prompt) in enumerate(zip(widgets, self.displayed_prompts)):
                content_frame = widget.winfo_children()[0]
                label = content_frame.winfo_children()[0]
                name = prompt["name"]
                hotkey = f" ({prompt['hotkey']})" if self.show_hotkeys else ""
                if label["text"] != f"{name}{hotkey}":
                    needs_update = True
                    break
                # Check if wrong indicator needs updating
                if i == len(self.displayed_prompts) - 1:
                    has_indicator = len(content_frame.winfo_children()) > 1
                    if bool(has_indicator) != self.wrong_attempt:
                        needs_update = True
                        break
            if not needs_update:
                return
        
        # Clear and rebuild display only if needed
        for widget in widgets:
            widget.destroy()
        
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
        if not self.prompts and not self.sequence_groups:
            return []
        
        # Handle current sequence if it exists
        if self.current_sequence:
            if len(self.current_sequence) >= self.visible_prompts:
                return self.current_sequence[:self.visible_prompts]
            else:
                self.current_sequence = None
        
        # Combine individual prompts and sequence groups for selection
        choices = []
        weights = []
        
        # Add individual prompts
        for prompt in self.prompts:
            choices.append(("prompt", prompt))
            weights.append(self.weights[prompt["name"]] * prompt["weight"])
        
        # Add sequence groups
        for group in self.sequence_groups:
            choices.append(("sequence", group))
            weights.append(group.get("weight", 1.0))
        
        # Select based on weights
        if not choices:
            return []
        
        selected = random.choices(choices, weights=weights, k=1)[0]
        
        if selected[0] == "prompt":
            # If a single prompt was selected, select the rest normally
            result = [selected[1]]
            remaining_count = self.visible_prompts - 1
            if remaining_count > 0 and self.prompts:
                remaining_weights = [self.weights[p["name"]] * p["weight"] for p in self.prompts]
                result.extend(random.choices(self.prompts, weights=remaining_weights, k=remaining_count))
            return result
        else:
            # If a sequence was selected, store it and return first part
            self.current_sequence = selected[1]["prompts"]
            return self.current_sequence[:self.visible_prompts]
    
    def _normalize_key(self, key):
        """Normalize key names to handle modifiers and special keys consistently."""
        key = str(key).lower()
        
        # Handle shift + key combinations for special characters
        if key.startswith('shift+'):
            base_key = key[6:]  # Remove 'shift+'
            # Map shifted numbers and symbols
            shift_map = {
                '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
                '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
                '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
                ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
                '`': '~'
            }
            if base_key in shift_map:
                return shift_map[base_key]
        
        # Check modifier map first
        if key in self.modifier_map:
            return self.modifier_map[key]
        
        # Check key map next
        if key in self.key_map:
            return self.key_map[key]
        
        # Handle single characters
        if len(key) == 1:
            return key
        
        # If no special mapping exists, return the key as is
        return key

    def _normalize_hotkey(self, keys):
        """Normalize a set of keys into a consistent hotkey string."""
        # Split modifiers and regular keys
        modifiers = sorted(k for k in keys if k in {'ctrl', 'alt', 'shift', 'win'})
        other_keys = sorted(k for k in keys if k not in {'ctrl', 'alt', 'shift', 'win'})
        
        # Combine modifiers first, then other keys
        normalized = modifiers + other_keys
        return '+'.join(normalized)

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
            target_hotkey = current_prompt["hotkey"]
            
            # Split the target hotkey into parts
            target_parts = set(target_hotkey.split('+'))
            
            # Handle single non-modifier key hotkeys differently
            if len(target_parts) == 1 and not any(part in {'ctrl', 'alt', 'shift', 'win'} for part in target_parts):
                # For single non-modifier keys, check exact match immediately
                target_key = next(iter(target_parts))
                # Only check non-modifier keys in current_keys
                non_modifier_keys = {k for k in self.current_keys if k not in {'ctrl', 'alt', 'shift', 'win'}}
                
                if len(non_modifier_keys) == 1 and key_name == target_key:
                    # Correct single key press
                    self.consecutive_correct[current_prompt["name"]] += 1
                    if self.consecutive_correct[current_prompt["name"]] > 2:
                        self.weights[current_prompt["name"]] *= 0.8
                    
                    self.wrong_attempt = False
                    self.displayed_prompts.pop()
                    
                    # Add a new prompt at the top if we have room
                    if len(self.displayed_prompts) < self.visible_prompts:
                        next_prompts = self._get_next_prompts()
                        if next_prompts:
                            self.displayed_prompts.insert(0, next_prompts[0])
                    
                    self._update_display()
                elif len(non_modifier_keys) > 1 or (non_modifier_keys and key_name != target_key):
                    # Wrong key pressed (ignoring modifiers)
                    self.weights[current_prompt["name"]] *= 1.2
                    self.consecutive_correct[current_prompt["name"]] = 0
                    self.wrong_attempt = True
                    self._update_display()
                return
            
            # Handle combination hotkeys
            if not self.waiting_for_combination:
                if key_name in target_parts:
                    self.waiting_for_combination = True
                    self.target_hotkey_parts = target_parts
                    self.wrong_attempt = False
                    self._update_display()
                return
            
            # If we are waiting for a combination, check if the pressed key makes it wrong
            if self.waiting_for_combination:
                current_parts = set(hotkey_name.split('+'))
                
                # Check if we've pressed a key that's not in the target combination
                if not current_parts.issubset(self.target_hotkey_parts):
                    self.waiting_for_combination = False
                    self.target_hotkey_parts.clear()
                    self.weights[current_prompt["name"]] *= 1.2
                    self.consecutive_correct[current_prompt["name"]] = 0
                    self.wrong_attempt = True
                    self._update_display()
                # Check if we've completed the correct combination
                elif current_parts == self.target_hotkey_parts:
                    self.waiting_for_combination = False
                    self.target_hotkey_parts.clear()
                    self.consecutive_correct[current_prompt["name"]] += 1
                    if self.consecutive_correct[current_prompt["name"]] > 2:
                        self.weights[current_prompt["name"]] *= 0.8
                    
                    self.wrong_attempt = False
                    self.displayed_prompts.pop()
                    
                    # Add a new prompt at the top if we have room
                    if len(self.displayed_prompts) < self.visible_prompts:
                        next_prompts = self._get_next_prompts()
                        if next_prompts:
                            self.displayed_prompts.insert(0, next_prompts[0])
                    
                    self._update_display()
                    
                    # If there are still keys held down that match the next prompt's hotkey,
                    # start waiting for that combination immediately
                    if self.displayed_prompts:
                        next_prompt = self.displayed_prompts[-1]
                        next_target_parts = set(next_prompt["hotkey"].split('+'))
                        current_parts = set(self._normalize_hotkey(self.current_keys).split('+'))
                        
                        # If any of the currently held keys are part of the next target
                        if any(part in next_target_parts for part in current_parts):
                            self.waiting_for_combination = True
                            self.target_hotkey_parts = next_target_parts
                            self.wrong_attempt = False
                            self._update_display()
            
            return False  # Prevent default handling for all keys
        
        def on_key_up(event):
            normalized_key = self._normalize_key(event.name)
            if normalized_key in self.current_keys:
                self.current_keys.remove(normalized_key)
                
                # If we're waiting for a combination and all keys are released, cancel the wait
                if self.waiting_for_combination:
                    current_parts = set(self._normalize_hotkey(self.current_keys).split('+'))
                    
                    # Only cancel if we have no keys pressed or if remaining keys don't match target
                    if not current_parts or not current_parts.issubset(self.target_hotkey_parts):
                        self.waiting_for_combination = False
                        self.target_hotkey_parts.clear()
                        if not self.wrong_attempt:  # Only update if we haven't already marked it wrong
                            current_prompt = self.displayed_prompts[-1]
                            self.weights[current_prompt["name"]] *= 1.2
                            self.consecutive_correct[current_prompt["name"]] = 0
                            self.wrong_attempt = True
                            self._update_display()
                # Handle single key release for non-combination hotkeys
                elif self.displayed_prompts:
                    current_prompt = self.displayed_prompts[-1]
                    target_parts = set(current_prompt["hotkey"].split('+'))
                    
                    # Only process for single non-modifier key hotkeys
                    if len(target_parts) == 1 and not any(part in {'ctrl', 'alt', 'shift', 'win'} for part in target_parts):
                        # Only check for non-modifier keys being held
                        non_modifier_keys = {k for k in self.current_keys if k not in {'ctrl', 'alt', 'shift', 'win'}}
                        # Only mark as wrong if we're holding non-modifier keys
                        if non_modifier_keys and not self.wrong_attempt:
                            self.weights[current_prompt["name"]] *= 1.2
                            self.consecutive_correct[current_prompt["name"]] = 0
                            self.wrong_attempt = True
                            self._update_display()
            
            return False  # Prevent default handling for all keys
        
        keyboard.on_press(on_key_down, suppress=True)
        keyboard.on_release(on_key_up, suppress=True)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = HotkeyTrainer()
    app.run()
