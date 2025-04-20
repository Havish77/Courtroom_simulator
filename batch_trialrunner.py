# batch_trial_runner.py — optimized for speed and Groq token limits

import os
import csv
import time
import pandas as pd
from agents.judge import JudgeAgent
from agents.lawyer import DefenseAgent, ProsecutionAgent
from agents.defendant import DefendantAgent
from agents.witness import WitnessAgent
from agents.plaintiff import PlaintiffAgent
from trial_manager import TrialManager

# === Load Data ===
DATA_PATH = "cases.csv"
df = pd.read_csv(DATA_PATH)

# Process only the first 50 cases
df = df.head(50)

# Prepare submission CSV
submission_path = "submission.csv"
with open(submission_path, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "label"])  # CSV header

# === Trial Loop ===
for idx, row in df.iterrows():
    case_id = row["id"]
    case_text = row["text"]

    print(f"\n=====================")
    print(f"🧾 Starting Trial {idx + 1}/{len(df)} for Case ID: {case_id}")
    print("=====================")

    # Inject case into each agent prompt
    judge = JudgeAgent()
    judge.system_prompt += f"\nThis is the case under trial:\n{case_text}"

    defense = DefenseAgent()
    defense.system_prompt += f"\nThis is the case under trial:\n{case_text}"

    prosecution = ProsecutionAgent()
    prosecution.system_prompt += f"\nThis is the case under trial:\n{case_text}"

    defendant = DefendantAgent()
    defendant.system_prompt += f"\nThis is the case under trial:\n{case_text}"

    witnesses = [WitnessAgent(name=f"Witness {i+1}") for i in range(1)]
    for witness in witnesses:
        witness.system_prompt += f"\nThis is the case under trial:\n{case_text}"

    # Run trial
    trial = TrialManager(judge, defense, prosecution, defendant, witnesses)
    while not trial.ended:
        trial.run_next_step()
        time.sleep(0.8)  # 🔁 Small delay between steps

    if (idx + 1) % 10 == 0:
        print("🕒 Batch checkpoint reached. Cooling down...")
        time.sleep(45)  # 🧊 Cool down between groups

print(f"\n✅ All trials complete. Results saved to {submission_path}")
