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
        self.root.geometry("500x600")
        
        self.emulator = None
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
        style.configure("TButton", padding=10, font=('Helvetica', 10))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'))

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="xArm 5 Tremor Replication System", style="Header.TLabel").pack(pady=10)
        
        ttk.Label(main_frame, text="Select Subject:").pack(anchor=tk.W, pady=(10, 0))
        
        subject_list = []
        for s_id in self.subjects:
            status = "Parkinson's" if self.full_data[s_id]['annotation'].get('pd_status') == 1 else "Control"
            subject_list.append(f"Subject {s_id} ({status})")

        self.subject_var = tk.StringVar()
        self.subject_dropdown = ttk.Combobox(main_frame, textvariable=self.subject_var, values=subject_list, state="readonly")
        self.subject_dropdown.pack(fill=tk.X, pady=5)
        if subject_list:
            self.subject_dropdown.current(0)

        self.info_text = tk.Text(main_frame, height=10, width=50, state='disabled', font=('Consolas', 9))
        self.info_text.pack(pady=10)

        self.subject_dropdown.bind("<<ComboboxSelected>>", self.update_info)
        self.update_info()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)

        self.launch_btn = ttk.Button(btn_frame, text="Launch Simulation", command=self.start_sim_thread)
        self.launch_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Simulation", command=self.stop_sim, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, text="Status:").pack(anchor=tk.W)
        ttk.Label(main_frame, textvariable=self.status_var, foreground="blue").pack(anchor=tk.W)

    def update_info(self, event=None):
        selection = self.subject_var.get()
        if not selection: return
        
        s_id = int(selection.split()[1])
        data = self.full_data[s_id]
        is_pd = data['annotation'].get('pd_status') == 1
        
        dur = len(data['imu_accel']) / 100.53
        
        info = f"Subject ID: {s_id}\n"
        info += f"Clinical Status: {'PD Patient (EXPECT HIGH JITTER)' if is_pd else 'Healthy Control (STABLE)'}\n"
        info += f"Trial Duration: {dur:.2f} seconds\n"
        info += "-"*30 + "\n"
        info += "Clinical Mapping: Unified Clinical Scale (1:1)\n"
        info += "Multiplier: NONE (Disabled group-based gain bias)\n"
        info += f"Status: {'Parkinsonian Tremor' if is_pd else 'Physiological Jitter'}\n"
        info += "\nCalibration: 1.0g accel ≈ 4mm peak displacement\n"
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info)
        self.info_text.config(state='disabled')

    def start_sim_thread(self):
        self.is_simulation_active = True
        self.launch_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("Running Simulation...")
        
        thread = threading.Thread(target=self.run_simulation, daemon=True)
        thread.start()

    def run_simulation(self):
        try:
            selection = self.subject_var.get()
            s_id = int(selection.split()[1])
            self.emulator = TremorEmulator(is_simulation=True)
            self.emulator.run_subject_simulation(s_id)
            self.root.after(0, self.on_sim_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Simulation Error", str(e)))
            self.root.after(0, self.on_sim_complete)

    def on_sim_complete(self):
        self.is_simulation_active = False
        self.launch_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Ready")

    def stop_sim(self):
        messagebox.showinfo("Stop", "Please close the MuJoCo viewer window to return to the GUI.")

if __name__ == "__main__":
    root = tk.Tk()
    app = TremorGUI(root)
    root.mainloop()
