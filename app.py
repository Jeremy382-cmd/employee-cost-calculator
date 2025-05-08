# GPT App: Ontario Employee Cost Calculator

import streamlit as st
import pandas as pd
import json
import os
import requests

# Fetch dynamic rates for CPP and EI (2025)
def fetch_contribution_rates():
    # Hardcoded from reliable 2025 sources
    cpp_employer_rate = 5.95  # Employer rate in %
    cpp_employee_rate = 5.95
    ei_employee_rate = 1.64
    ei_employer_rate = ei_employee_rate * 1.4  # Employer pays 1.4x
    return cpp_employer_rate, cpp_employee_rate, ei_employer_rate, ei_employee_rate

# Employee Class
class Employee:
    def __init__(self, name, employment_type, base_wage, weekly_hours, overtime_hours,
                 vacation_pct, cpp_rate, ei_rate, wsib_rate,
                 health_benefits):
        self.name = name
        self.employment_type = employment_type
        self.base_wage = base_wage
        self.weekly_hours = weekly_hours
        self.overtime_hours = overtime_hours
        self.vacation_pct = vacation_pct
        self.cpp_rate = cpp_rate
        self.ei_rate = ei_rate
        self.wsib_rate = wsib_rate
        self.health_benefits = health_benefits

    def average_hourly_rate(self):
        overtime_wage = self.base_wage * 1.5
        total_hours = self.weekly_hours + self.overtime_hours
        total_wages = (self.weekly_hours * self.base_wage) + (self.overtime_hours * overtime_wage)
        return total_wages / total_hours if total_hours else self.base_wage

    def cost_components(self):
        base = self.average_hourly_rate()
        return {
            "Base Wage": base,
            "Vacation Pay": base * self.vacation_pct / 100,
            "CPP (Employer)": base * self.cpp_rate / 100,
            "CPP (Employee)": base * cpp_employee_rate / 100,
            "EI (Employer)": base * self.ei_rate / 100,
            "EI (Employee)": base * ei_employee_rate / 100,
            "WSIB": base * self.wsib_rate / 100,
            "Health Benefits": self.health_benefits,
        }

    def total_hourly_cost(self):
        c = self.cost_components()
        employer_total = c["Base Wage"] + c["Vacation Pay"] + c["CPP (Employer)"] + c["EI (Employer)"] + c["WSIB"] + c["Health Benefits"]
        employee_total = c["CPP (Employee)"] + c["EI (Employee)"]
        return employer_total, employee_total, employer_total * (self.weekly_hours + self.overtime_hours) * 52, employee_total * (self.weekly_hours + self.overtime_hours) * 52

    def to_dict(self):
        return self.__dict__

# Utility functions
PROFILE_FILE = "employee_profiles.json"

def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

# Streamlit UI
st.title("Ontario Employee Cost Calculator")

# Fetch dynamic contribution rates
cpp_rate, cpp_employee_rate, ei_rate, ei_employee_rate = fetch_contribution_rates()

# Display current dynamic rates
with st.expander("ℹ️ Contribution Rate Information", expanded=True):
    st.markdown("""
    - **CPP (Canada Pension Plan):**
        - Employer Contribution: **5.95%**
        - Employee Contribution: **5.95%**
    - **EI (Employment Insurance):**
        - Employer Contribution: **2.30%** (1.4x employee rate)
        - Employee Contribution: **1.64%**
    - **WSIB:** Manually entered based on your NAICS industry rate.
    """)

profiles = load_profiles()
profile_names = list(profiles.keys())

st.sidebar.header("Employee Inputs")
selected_profile = st.sidebar.selectbox("Load Existing Profile (Optional)", [""] + profile_names)

if selected_profile and selected_profile in profiles:
    p = profiles[selected_profile]
else:
    p = {}

name = st.sidebar.text_input("Employee Name", value=p.get("name", ""))
employment_type = st.sidebar.selectbox("Employment Type", ["Full-Time", "Part-Time", "Temporary", "Subcontractor", "Salaried", "Hourly"], index=["Full-Time", "Part-Time", "Temporary", "Subcontractor", "Salaried", "Hourly"].index(p.get("employment_type", "Full-Time")))
base_wage = st.sidebar.number_input("Base Hourly Wage ($)", min_value=0.0, step=0.01, value=p.get("base_wage", 0.0))
weekly_hours = st.sidebar.number_input("Average Weekly Hours", min_value=0, step=1, value=p.get("weekly_hours", 0))
overtime_hours = st.sidebar.number_input("Overtime Hours/Week", min_value=0, step=1, value=p.get("overtime_hours", 0))
vacation_pct = st.sidebar.number_input("Vacation Pay (%)", min_value=0.0, step=0.1, value=p.get("vacation_pct", 4.0))
wsib_rate = st.sidebar.number_input("WSIB Rate (%)", min_value=0.0, step=0.01, value=p.get("wsib_rate", 1.30))
health_benefits = st.sidebar.number_input("Health Benefits ($/hr)", min_value=0.0, step=0.01, value=p.get("health_benefits", 0.0))

if st.sidebar.button("Calculate Cost"):
    emp = Employee(name, employment_type, base_wage, weekly_hours, overtime_hours,
                   vacation_pct, cpp_rate, ei_rate, wsib_rate,
                   health_benefits)
    components = emp.cost_components()
    employer_total, employee_total, annual_employer_total, annual_employee_total = emp.total_hourly_cost()

    st.subheader(f"Hourly Cost Breakdown for {name}")
    df = pd.DataFrame(components.items(), columns=["Cost Component", "$ per Hour"])
    st.dataframe(df)
    st.metric(label="Employer Hourly Cost", value=f"${employer_total:.2f}")
    st.metric(label="Employee Deductions", value=f"${employee_total:.2f}")
    st.metric(label="Annual Employer Cost", value=f"${annual_employer_total:,.2f}")
    st.metric(label="Annual Employee Deductions", value=f"${annual_employee_total:,.2f}")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Cost Breakdown as CSV", csv, f"{name}_hourly_cost.csv", "text/csv")

    if st.checkbox("Save/Update Employee Profile"):
        profiles[name] = emp.to_dict()
        save_profiles(profiles)
        st.success(f"Profile for {name} saved successfully.")
