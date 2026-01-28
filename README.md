# Tremor Emulator: Parkinson's Disease Replication on xArm 5

This project implements a high-fidelity tremor emulator that uses real-world accelerometry data from Parkinson's Disease (PD) patients to drive a UFACTORY xArm 5 robotic arm. It is designed to test assistive devices under standardized yet realistic pathological motion conditions.


### Status:
1.  **Clinical Data Integration**: Extracted and processed the Zenodo PD dataset, identifying a strong 6.2 Hz postural tremor.
2.  **Advanced Signal Processing**: Implemented a 5th-order Butterworth bandpass filter (3-10 Hz) to isolate pathological tremors from voluntary movement and noise.
3.  **High-Fidelity Simulation**: Created a MuJoCo 3.4.0 environment with exact mass and inertia tensors to ensure stability during high-frequency jitter.
4.  **Hardware Characterization (Breakpoint reached 2026-01-28)**: 
    *   **Identified Limits**: Physical hardware acceleration is capped at **2,000 mm/s²** (vs. ~7,100 mm/s² required for full severe tremor).
    *   **Cartesian Filtering**: Determined that the industrial Inverse Kinematics (IK) engine and "Path Smoothing" filters out high-frequency tremors (returning only ~6% of requested movement).
    *   **Path Forward**: Implementing **Joint-Space Servoing (Mode 1)** to bypass the Cartesian filter and tap into the $28,647 \text{ deg/s}^3$ joint jerk limits.
5.  **Robot/Gripper URDF Notes**: 
    *   **Gripper Orientation**: Correct mounting requires a **180-degree rotation around the Z-axis** (`quat="0 0 0 1"`) to prevent motor block collisions.
    *   **Collision Suppression**: Zero-offset mounting is enabled by ignoring collisions between the tool assembly and the robot wrist.
    
## Data Exploration

The following visualizations from our analysis notebooks illustrate the tremor characteristics:

### 1. Raw Session Data
A sample 10-second segment of Subject 9's accelerometry data showing the characteristic periodic oscillation.
![Raw Session Data](notebooks/sample_session.png)

### 2. Frequency Analysis (FFT)
Power Spectral Density (PSD) analysis reveals a sharp peak at ~6.2 Hz, consistent with classic Parkinsonian postural tremor.
![FFT Peak](notebooks/frequency_spectrum.png)

### 3. Filtered Motion Replay
The result of our displacement estimation algorithm after applying the Butterworth filter, showing the isolated jitter used to drive the robot.
![Filtered Tremor](notebooks/motion_simulation.png)

## Signal Processing Pipeline

The tremor isolation logic follows this mathematical path:

1.  **Bandpass Filtering**:
    Isolates the tremor from static gravity (0 Hz) and high-frequency sensor noise.
    
2.  **Displacement Estimation**:
    Since we only have acceleration, we perform double integration with high-pass filtering to estimate local displacement.

## Simulation Setup

The MuJoCo simulation leverages official URDF/STL parameters to prevent "NaN" physics errors that typically occur when applying high-frequency forces to primitive shapes with inaccurate inertia.

- **Integrator**: RK4 (Runge-Kutta 4th Order)
- **Timestep**: 0.001s (1000 Hz)
- **Scale Factor**: 0.004 results in 1:1 clinical replication (1g ≈ 4mm peak-to-peak).
- **Physics Stability**: Achieved via high joint damping, armature, and linear interpolation between 100Hz control samples.

## Dataset Handling
The full dataset (Subjects 1-11) is ~3.7GB and is excluded from this repository to maintain performance. 
- **Source**: Parkinson's Disease IMU Data (Accelerometer signals).
- **Setup**: 
  1. Download the raw data (PD_IMU_Data.zip).
  2. Place it in `data/raw/`.
  3. Run `python src/data_processing/clean_data.py` to generate the processed pickle files.
  4. See `scripts/download_data.py` for automated setup notes.
### Hardware Deployment (xArm 5 Specifics)

The system is designed to transition from simulation to a physical xArm 5 (5-DOF) for real-world device testing.

#### 5-DOF Geometric Constraints
During deployment on the xArm 5, we identified significant Inverse Kinematics (IK) constraints:
- **Cartesian Mode (IK)**: The robot can only follow 1-axis (X or Z) tremor reliably. Multi-axis movement (XY or XYZ) causes implicit IK rejection because the 5-DOF arm cannot maintain a constant tool orientation (Roll, Pitch, Yaw) while vibrating in 3D.
- **Joint Mode (Direct)**: By bypassing the Cartesian IK solver and commanding the motors directly, we can achieve 3D jitter. This is the preferred mode for "qualitative" shaking (e.g., utensil testing) as it is immune to geometric rejection.

#### Physical Realism & Scaling (`sens=0.5`)
- **Direct Mode Units**: In Joint mode, we translate **Millimeters** of offset into **Degrees** of rotation using a `sens = 0.5` sensitivity factor.
- **CAUTION**: This is a non-linear scaling. $1mm$ in clinical data does **not** equal $1^\circ$ of motor rotation at the tip. This mode is excellent for simulating the *character* and *frequency* of a tremor, but should not be used for high-precision amplitude verification.
- **Accuracy Fallback**: For tests requiring sub-millimeter amplitude accuracy, use **Cartesian Mode (X-Axis only)**, which provides 1:1 clinical displacement mapping.

#### Future Development
- **IMU Validation**: I intend to mount an independent IMU at or near the robot gripper to record the *actual* produced motion. This data will be compared against the requested clinical data to measure "Total Path Fidelity" in future versions.
## Replication Guide

### Prerequisites
- Python 3.10+
- MuJoCo 3.4+
- `numpy`, `scipy`, `mujoco-python-viewer`

### Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the GUI launcher:
   ```bash
   python src/gui/deployment_gui.py
   ```
4. Or run the simulation directly:
   ```bash
   python src/simulation/run_simulation.py [subject_id]
   ```

## Folder Structure
- `data/`: Contains `imu_data.pkl` (processed patient data)
- `src/data_processing/`: Butterworth filtering and displacement logic
- `src/simulation/`: MuJoCo MJCF model and simulation loop
- `src/gui/`: Tkinter-based control application
- `src/robot_control/`: xArm 5 SDK integration and hardware bridge

## Hardware Deployment

The system is designed to transition from simulation to a physical xArm 5 for real-world device testing.

### Movement Pipeline
The tremor data is transmitted to the robot using the following pipeline:
1.  **Data Retrieval**: Processed IMU data (sampled at 100Hz) is loaded into the controller.
2.  **Displacement Mapping**: Clinical acceleration values are converted to Cartesian displacement (mm) using the double-integration model validated in simulation.
3.  **Real-time Control**: The xArm-Python-SDK's `set_servo_cartesian` method is used to stream these high-frequency offsets (at 100Hz) relative to a base "Testing Stance".
4.  **Safety Layer**: Velocity and position limits are enforced by the SDK to prevent abrupt movements or collisions.

### Control GUI
The integrated deployment GUI provides the following controls:
- **Connection**: Connects to the robot at 192.168.1.220.
- **Stance Control**: Moves the arm to the standard testing pose [0, -35, -55, 0, 0].
- **Gripper Control**: Open (850) and Close (0) for tool attachment.
- **Tremor Replication**: Real-time toggle using Subject IMU data and 10Hz live telemetry.

## Hardware Constraints & Analysis (v1.11.1 Firmware)

Through diagnostic testing (January 2026), several key performance constraints were identified on the xArm 5:

### 1. The Physics Gap
To replicate a $6\text{ Hz}$ PD tremor at $5\text{ mm}$ amplitude, an acceleration of approximately **$7,100\text{ mm/s}^2$** is required.
- **Hardware Limit**: The xArm 5 firmware imposes a hard ceiling of **$2,000\text{ mm/s}^2$** for linear motion.
- **Result**: Severe clinical tremors (like Subject 999) will be physically scaled down by the hardware. Expected amplitude is $\sim 1.5\text{ mm}$ at $6\text{ Hz}$.

### 2. Cartesian Smoothing Problem
When using `set_servo_cartesian` (Mode 1), the robot's secondary controllers apply aggressive smoothing to ensure straight-line paths. 
- **The Symptom**: A $10\text{ mm}$ command at $1\text{ Hz}$ was only resulting in **$0.63\text{ mm}$** of actual physical travel (6% efficiency).
- **The Cause**: High-frequency jitter is treated as "mechanical noise" by the industrial motion planner.

### 3. Optimized Parameter Set (Manual UI Verification)
To achieve the best possible responsiveness, the following settings were manually applied in the UFACTORY Studio Web UI:

| Parameter | Value | Purpose |
| :--- | :--- | :--- |
| **Collision Sensitivity** | 1 (Lowest) | Prevents vibration from triggering safety stops. |
| **Line Motion Accel** | 2,000 mm/s² | Maximum linear ceiling. |
| **TCP Jerk** | 10,000 mm/s³ | Maximum tip rate of change. |
| **Joint Jerk** | 28,647 deg/s³ | Unlocked maximum for high-response motor spikes. |
| **Joint Accel** | 1,146 deg/s² | Maximum motor-space acceleration. |

### 4. Path Forward: Joint-Space Servoing
To bypass Cartesian filtering, the emulator is shifting to **Joint-Space Servos** (`set_servo_angle_j`). This allows the system to:
1.  Bypass the Inverse Kinematics (IK) calculation lag.
2.  Bypass the "Straight-Line" smoothing filter.
3.  Directly leverage the $28,647 \text{ deg/s}^3$ joint jerk limits for rapid oscillation.

## Safety & Reset Reference
**IMPORTANT**: The parameters modified for clinical tremor emulation are aggressive and disable several industrial safety cushions. **Always reset the robot** to industrial defaults before using it for heavy lifting or human-collaborative tasks.

| Parameter | Default (Industrial) | Emulator (Tuned) | Reset Value |
| :--- | :--- | :--- | :--- |
| **Collision Sensitivity** | 4 | **1 (Lowest)** | 4 (Essential Box Safety) |
| **Joint Jerk** | ~5,000 deg/s³ | **28,647 deg/s³** | 5,000 deg/s³ |
| **TCP Jerk** | 1,000 mm/s³ | **10,000 mm/s³** | 1,000 mm/s³ |
| **TCP Accel** | 1,000 mm/s² | **2,000 mm/s²** | 1,000 mm/s² |

3.  **Brake Release**: If the arm enters a collision state.
Once basic positioning is achieved via the OEM interface, the Emulator system takes over for precision tremor replication.
