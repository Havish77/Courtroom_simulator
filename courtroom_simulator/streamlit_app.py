# streamlit_app.py — Groq-compatible trial interface

import streamlit as st
import pandas as pd
from agents.defendant import DefendantAgent
from agents.judge import JudgeAgent
from agents.lawyer import DefenseAgent, ProsecutionAgent
from agents.witness import WitnessAgent
from trial_manager import TrialManager
from agents.base_agent import BaseAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Load the case data
CASE_DATA = pd.read_csv("data.csv")
st.set_page_config("Courtroom Simulator", layout="wide")
st.title("⚖️ Courtroom Trial Simulator")

# --- Select a Case ---
st.sidebar.header("🔍 Select a Case")
case_index = st.sidebar.selectbox("Choose a case to simulate:", CASE_DATA.index)
selected_case = CASE_DATA.loc[case_index, "text"]
st.sidebar.markdown("---")
st.sidebar.code(selected_case[:500] + ("..." if len(selected_case) > 500 else ""))

# --- Session State Init ---
if "trial" not in st.session_state:
    judge = JudgeAgent()
    defense = DefenseAgent()
    prosecution = ProsecutionAgent()
    defendant = DefendantAgent()
    witnesses = [WitnessAgent()]
    trial = TrialManager(judge, defense, prosecution, defendant, witnesses)
    st.session_state.trial = trial

# --- Add New Witness Dynamically ---
st.sidebar.header("➕ Add Witness")
with st.sidebar.form("new_witness_form"):
    witness_name = st.text_input("Witness name")
    witness_prompt = st.text_area("Witness background")
    submitted = st.form_submit_button("Add Witness")
    if submitted and witness_name:
        agent_prompt = f"You are {witness_name}. {witness_prompt}\nRefer to this case:\n{selected_case}"
        new_witness = BaseAgent(witness_name, agent_prompt)
        st.session_state.trial.witnesses.append(new_witness)
        st.success(f"Witness '{witness_name}' added.")

# --- Run Next Trial Phase ---
st.markdown("## 🧑‍⚖️ Trial Transcript")
if st.button("▶️ Run Next Phase"):
    st.session_state.trial.run_next_step()
    st.rerun()

# --- Display Transcript ---
for agent in [
    st.session_state.trial.judge,
    st.session_state.trial.defense,
    st.session_state.trial.prosecution,
    st.session_state.trial.defendant,
    *st.session_state.trial.witnesses
]:
    with st.expander(f"{agent.name} - Transcript"):
        for entry in agent.history:
            role = entry["role"].capitalize()
            content = entry["content"]
            st.markdown(f"**{role}**: {content}")