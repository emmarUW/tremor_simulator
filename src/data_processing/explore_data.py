import pickle
import pandas as pd
import numpy as np
import os

def explore_dataset(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Loading dataset from {file_path}...")
    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    print(f"Dataset type: {type(data)}")
    print(f"Number of subjects: {len(data)}")

    if len(data) > 0:
        # Find first subject with sessions
        subject_with_sessions = next((s for s in data if len(s.get('sessions', [])) > 0), None)
        
        if subject_with_sessions:
            print("\nSubject Info (with sessions):")
            print(f"Keys: {list(subject_with_sessions.keys())}")
            print(f"Subject ID: {subject_with_sessions.get('subject_id')}")
            
            sessions = subject_with_sessions.get('sessions', [])
            print(f"Number of sessions: {len(sessions)}")
            
            if len(sessions) > 0:
                first_session = sessions[0]
                print(f"First session shape: {first_session.shape}")
                print(f"Sample data (first 5 rows):\n{first_session[:5]}")
                
            annotations = subject_with_sessions.get('annotation', {})
            print(f"Annotations: {annotations}")
        else:
            print("\nNo subjects with sessions found.")

def find_tremor_subjects(data):
    tremor_subjects = [s for s in data if s.get('annotation', {}).get('sp_expert') == 1]
    print(f"Number of subjects with expert-confirmed tremor: {len(tremor_subjects)}")
    for s in tremor_subjects[:5]:
        print(f"Subject ID: {s.get('subject_id')}, Sessions: {len(s.get('sessions', []))}, PD Status: {s.get('annotation', {}).get('pd_status')}")
    return tremor_subjects

if __name__ == "__main__":
    file_path = r"C:\Users\emmar\Desktop\Tremor_Emulator\data\raw\tremor_dataset.pickle"
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    tremor_subjects = find_tremor_subjects(data)
