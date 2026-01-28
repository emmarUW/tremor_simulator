import tkinter as tk
from tkinter import ttk, messagebox
import threading
import sys
import os
import pickle

# Add src to path using relative logic
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)
from src.robot_control.xarm_control import TremorEmulator

class TremorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("xArm 5 Tremor Emulator Control")
        self.root.geometry("1000x550")
        
        self.emulator = TremorEmulator(is_simulation=True)
        self.is_simulation_active = False
        
        # Load Data using relative path
        data_path = os.path.join(base_dir, 'data', 'imu_data.pkl')
        try:
            with open(data_path, 'rb') as f:
                self.full_data = pickle.load(f)
            self.subjects = sorted(self.full_data.keys())
        except Exception as e:
            messagebox.showerror("Data Error", f"Could not load IMU data at {data_path}\nRun src/data_processing/clean_data.py first.")
            self.subjects = []

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Connection.TLabelframe", font=('Helvetica', 10, 'bold'))

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="xArm 5 Tremor Replication System", style="Header.TLabel").pack(pady=(0, 20))
        
        # Horizontal layout for main sections
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Column: Connection & Data Selection
        left_col = ttk.Frame(content_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # --- Connection Section ---
        conn_frame = ttk.LabelFrame(left_col, text="Robot Connection", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(conn_frame, text="IP Address:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_var = tk.StringVar(value="192.168.1.220")
        self.ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=15)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        self.connect_btn = ttk.Button(conn_frame, text="Connect to xArm", command=self.connect_robot)
        self.connect_btn.grid(row=0, column=2, padx=10, pady=5)

        # --- Subject Selection Section ---
        sub_frame = ttk.LabelFrame(left_col, text="Data Selection", padding=10)
        sub_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Label(sub_frame, text="Select Subject:").pack(anchor=tk.W)
        subject_list = []
        for s_id in self.subjects:
            if s_id == 999:
                status = "WORST CASE"
            else:
                status = "Parkinson's" if self.full_data[s_id]['annotation'].get('pd_status') == 1 else "Control"
            subject_list.append(f"Subject {s_id} ({status})")

        self.subject_var = tk.StringVar()
        self.subject_dropdown = ttk.Combobox(sub_frame, textvariable=self.subject_var, values=subject_list, state="readonly")
        self.subject_dropdown.pack(fill=tk.X, pady=5)
        if subject_list:
            self.subject_dropdown.current(0)

        self.info_text = tk.Text(sub_frame, height=10, width=40, state='disabled', font=('Consolas', 9))
        self.info_text.pack(pady=10, fill=tk.BOTH, expand=True)
        self.subject_dropdown.bind("<<ComboboxSelected>>", self.update_info)
        self.update_info()

        # --- Motion Configuration Section ---
        config_frame = ttk.LabelFrame(left_col, text="Motion Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=10)
        
        # Control Mode (IK vs Direct)
        ttk.Label(config_frame, text="Control Mode:").grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="Cartesian")
        ttk.Radiobutton(config_frame, text="Cartesian (IK)", variable=self.mode_var, value="Cartesian", command=self.update_axis_availability).grid(row=1, column=0, sticky=tk.W, padx=20)
        ttk.Radiobutton(config_frame, text="Joint (Direct)", variable=self.mode_var, value="Joint", command=self.update_axis_availability).grid(row=2, column=0, sticky=tk.W, padx=20)
        
        # Active Axis selection
        ttk.Label(config_frame, text="Active Tremor Axis:").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        self.axis_var = tk.StringVar(value="X")
        self.axis_radios = {}
        axes = [("X-Axis", "X"), ("Y-Axis", "Y"), ("Z-Axis", "Z"), ("All axes", "All (XYZ)")]
        for i, (text, val) in enumerate(axes):
            rb = ttk.Radiobutton(config_frame, text=text, variable=self.axis_var, value=val)
            rb.grid(row=i+1, column=1, sticky=tk.W, padx=40)
            self.axis_radios[val] = rb

        self.explanation_label = ttk.Label(config_frame, text="", wraplength=250, font=('Helvetica', 8, 'italic'), foreground="gray")
        self.explanation_label.grid(row=5, column=0, columnspan=2, pady=5, sticky=tk.W)
        
        self.update_axis_availability()
        
        # Right Column: Controls & Telemetry
        right_col = ttk.Frame(content_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # --- Robot Controls Section ---
        control_frame = ttk.LabelFrame(right_col, text="Hardware Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        btn_grid = ttk.Frame(control_frame)
        btn_grid.pack()

        self.stance_btn = ttk.Button(btn_grid, text="Testing Stance", command=lambda: self.run_async(self.emulator.set_testing_stance), state='disabled')
        self.stance_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        self.open_gripper_btn = ttk.Button(btn_grid, text="Open Gripper", command=lambda: self.run_async(self.emulator.open_gripper), state='disabled')
        self.open_gripper_btn.grid(row=1, column=0, padx=5, pady=5)

        self.close_gripper_btn = ttk.Button(btn_grid, text="Close Gripper", command=lambda: self.run_async(self.emulator.close_gripper), state='disabled')
        self.close_gripper_btn.grid(row=1, column=1, padx=5, pady=5)

        self.tremor_btn = ttk.Button(control_frame, text="START TREMOR REPLICATION", command=self.toggle_tremor_gui, state='disabled')
        self.tremor_btn.pack(fill=tk.X, pady=10)

        # --- Telemetry Section ---
        telemetry_frame = ttk.LabelFrame(right_col, text="Live Robot Telemetry (mm)", padding=10)
        telemetry_frame.pack(fill=tk.X, pady=10)

        self.telemetry_vars = {
            'X': tk.StringVar(value="0.00"),
            'Y': tk.StringVar(value="0.00"),
            'Z': tk.StringVar(value="0.00"),
            'Roll': tk.StringVar(value="0.00"),
            'Pitch': tk.StringVar(value="0.00"),
            'Yaw': tk.StringVar(value="0.00")
        }

        t_grid = ttk.Frame(telemetry_frame)
        t_grid.pack(fill=tk.X)

        for i, (label, var) in enumerate(self.telemetry_vars.items()):
            row = i // 3
            col = (i % 3) * 2
            ttk.Label(t_grid, text=f"{label}:", font=('Helvetica', 9, 'bold')).grid(row=row, column=col, padx=5, pady=2, sticky=tk.E)
            ttk.Label(t_grid, textvariable=var, font=('Consolas', 10), foreground="blue", width=10).grid(row=row, column=col+1, padx=5, pady=2, sticky=tk.W)

        # --- Simulation Section ---
        sim_frame = ttk.LabelFrame(right_col, text="Simulation Mode", padding=10)
        sim_frame.pack(fill=tk.X, pady=10)

        self.launch_sim_btn = ttk.Button(sim_frame, text="Launch MuJoCo Simulation", command=self.start_sim_thread)
        self.launch_sim_btn.pack(side=tk.LEFT, padx=10)

        # --- Bottom Status Bar ---
        self.status_var = tk.StringVar(value="Disconnected")
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Label(status_frame, text="System Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="red", font=('Helvetica', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=5)

    def update_info(self, event=None):
        selection = self.subject_var.get()
        if not selection: return
        
        s_id = int(selection.split()[1])
        data = self.full_data[s_id]
        is_pd = data['annotation'].get('pd_status') == 1
        dur = len(data['imu_accel']) / 100.53
        
        info = f"Subject ID: {s_id}\n"
        info += f"Clinical Status: {'PD Patient' if is_pd else 'Healthy Control'}\n"
        info += f"Trial Duration: {dur:.2f} seconds\n"
        info += "-"*30 + "\n"
        info += "Calibration: 1.0g accel \u2248 4mm displacement\n"
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state='disabled')

    def connect_robot(self):
        ip = self.ip_var.get()
        self.status_var.set("Connecting...")
        self.root.update_idletasks()
        
        def do_connect():
            success, message = self.emulator.connect(ip)
            if success:
                self.root.after(0, lambda: self.on_connect_success(message, ip))
            else:
                self.root.after(0, lambda: self.on_connect_error(message))
        
        threading.Thread(target=do_connect, daemon=True).start()

    def on_connect_success(self, message, ip):
        messagebox.showinfo("Success", message)
        self.status_var.set(f"Connected to {ip}")
        self.status_label.config(foreground="green")
        self.enable_controls()
        self.launch_sim_btn.config(state='disabled')
        self.start_telemetry_polling()

    def on_connect_error(self, message):
        messagebox.showerror("Error", message)
        self.status_var.set("Connection Failed")
        self.status_label.config(foreground="red")

    def start_telemetry_polling(self):
        """Starts the periodic refresh of robot position data."""
        def poll():
            if not self.emulator or not self.emulator.is_connected:
                self.root.after(500, poll)
                return

            # Sync Button State if tremor finished on its own
            is_active = self.emulator.tremor_active
            current_btn_text = self.tremor_btn.cget('text')
            
            if not is_active and "STOP" in current_btn_text:
                self.tremor_btn.config(text="START TREMOR REPLICATION")
                self.status_var.set(f"Connected to {self.emulator.ip}")
                self.status_label.config(foreground="green")
            elif is_active and "START" in current_btn_text:
                self.tremor_btn.config(text="STOP TREMOR REPLICATION")
                self.status_var.set("TREMOR ACTIVE")
                self.status_label.config(foreground="orange")

            # Update X, Y, Z, Roll, Pitch, Yaw from the emulator's pose
            # We no longer skip this during tremor because we switched to non-blocking 'arm.position'
            pose = self.emulator.get_current_pose()
            if pose and len(pose) >= 6:
                labels = ['X', 'Y', 'Z', 'Roll', 'Pitch', 'Yaw']
                for i, label in enumerate(labels):
                    self.telemetry_vars[label].set(f"{pose[i]:.2f}")
            
            # Poll every 100ms
            self.root.after(100, poll)
        
        poll()

    def update_axis_availability(self):
        """Restricts axis selection based on the chosen Control Mode (IK constraints)."""
        mode = self.mode_var.get()
        if mode == "Cartesian":
            # X and Z work, Y and All fail IK in downward stance
            self.axis_radios['X'].config(state='normal')
            self.axis_radios['Y'].config(state='disabled')
            self.axis_radios['Z'].config(state='normal')
            self.axis_radios['All (XYZ)'].config(state='disabled')
            if self.axis_var.get() in ['Y', 'All (XYZ)']:
                self.axis_var.set('X')
            self.explanation_label.config(text="Cartesian: Y and 3D mode rejected by 5-DOF IK.")
        else:
            # Joint mode is used for 3D jitter. Individual axes are less useful here.
            self.axis_radios['X'].config(state='disabled')
            self.axis_radios['Y'].config(state='disabled')
            self.axis_radios['Z'].config(state='disabled')
            self.axis_radios['All (XYZ)'].config(state='normal')
            self.axis_var.set('All (XYZ)')
            self.explanation_label.config(text="Joint: Bypasses IK safety to allow 3D vibration.")

    def enable_controls(self):
        self.stance_btn.config(state='normal')
        self.open_gripper_btn.config(state='normal')
        self.close_gripper_btn.config(state='normal')
        self.tremor_btn.config(state='normal')

    def run_async(self, func):
        """Run blocking robot commands in a thread."""
        threading.Thread(target=func, daemon=True).start()

    def toggle_tremor_gui(self):
        selection = self.subject_var.get()
        s_id = int(selection.split()[1])
        subject_data = self.full_data[s_id]
        selected_axis = self.axis_var.get()
        selected_mode = self.mode_var.get()

        active = self.emulator.toggle_tremor(subject_data, axis=selected_axis, mode=selected_mode)
        if active:
            self.tremor_btn.config(text="STOP TREMOR REPLICATION")
            self.status_var.set("TREMOR ACTIVE")
            self.status_label.config(foreground="orange")
        else:
            self.tremor_btn.config(text="START TREMOR REPLICATION")
            self.status_var.set(f"Connected to {self.emulator.ip}")
            self.status_label.config(foreground="green")

    def start_sim_thread(self):
        self.is_simulation_active = True
        self.launch_sim_btn.config(state='disabled')
        self.status_var.set("Running Simulation...")
        
        thread = threading.Thread(target=self.run_simulation, daemon=True)
        thread.start()

    def run_simulation(self):
        try:
            selection = self.subject_var.get()
            s_id = int(selection.split()[1])
            self.emulator.run_subject_simulation(s_id)
            self.root.after(0, self.on_sim_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))
            self.root.after(0, self.on_sim_complete)

    def on_sim_complete(self):
        self.is_simulation_active = False
        self.launch_sim_btn.config(state='normal')
        self.status_var.set("Ready (Sim Mode)")

if __name__ == "__main__":
    root = tk.Tk()
    app = TremorGUI(root)
    root.mainloop()
