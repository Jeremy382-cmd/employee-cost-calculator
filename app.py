# app.py

import streamlit as st
import pandas as pd
import json
import os
import datetime

# Fetch dynamic rates for CPP and EI (2025)
def fetch_contribution_rates():
    cpp_employer_rate = 5.95
    cpp_employee_rate = 5.95
    ei_employee_rate = 1.64
    ei_employer_rate = ei_employee_rate * 1.4
    return cpp_employer_rate, cpp_employee_rate, ei_employer_rate, ei_employee_rate

# 2025 Contribution Maximums
CPP_MAX_ANNUAL = 4055.50
EI_MAX_EMPLOYEE = 1049.12
EI_MAX_EMPLOYER = 1468.77

# Employee Class
class Employee:
    def __init__(self, name, employment_type, base_wage, weekly_hours, overtime_hours,
                 vacation_pct, cpp_rate, ei_rate, wsib_rate,
                 health_benefits, apply_caps=True, apply_overtime=True, include_vacation=True, wsib_on_ot=True):
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
        self.apply_caps = apply_caps
        self.apply_overtime = apply_overtime
        self.include_vacation = include_vacation
        self.wsib_on_ot = wsib_on_ot
        self.warnings = []

    def average_hourly_rate(self):
        # Overtime at 1.5× when enabled
        rate = 1.5 if self.apply_overtime else 1.0
        overtime_wage = self.base_wage * rate
        total_hours = self.weekly_hours + self.overtime_hours
        total_wages = (self.weekly_hours * self.base_wage) + (self.overtime_hours * overtime_wage)
        return total_wages / total_hours if total_hours else self.base_wage

    def cost_components(self):
        base = self.average_hourly_rate()
        annual_hours = (self.weekly_hours + self.overtime_hours) * 52
        annual_earnings = base * annual_hours

        # Raw annual CPP/EI
        cpp_emp = annual_earnings * self.cpp_rate / 100
        cpp_ee  = annual_earnings * 5.95 / 100
        ei_emp  = annual_earnings * self.ei_rate / 100
        ei_ee   = annual_earnings * 1.64 / 100

        # Apply annual caps if enabled
        if self.apply_caps:
            if cpp_emp > CPP_MAX_ANNUAL:
                cpp_emp = CPP_MAX_ANNUAL
                self.warnings.append("⚠️ CPP maximum employer contribution reached.")
            if cpp_ee > CPP_MAX_ANNUAL:
                cpp_ee = CPP_MAX_ANNUAL
                self.warnings.append("⚠️ CPP maximum employee deduction reached.")
            if ei_emp > EI_MAX_EMPLOYER:
                ei_emp = EI_MAX_EMPLOYER
                self.warnings.append("⚠️ EI maximum employer contribution reached.")
            if ei_ee > EI_MAX_EMPLOYEE:
                ei_ee = EI_MAX_EMPLOYEE
                self.warnings.append("⚠️ EI maximum employee deduction reached.")

        return {
            "Base Wage": base,
            "Vacation Pay": base * self.vacation_pct / 100 if self.include_vacation else 0,
            "CPP (Employer)": cpp_emp / annual_hours,
            "CPP (Employee)": cpp_ee / annual_hours,
            "EI (Employer)": ei_emp / annual_hours,
            "EI (Employee)": ei_ee / annual_hours,
            "WSIB": (
                base * self.wsib_rate / 100
                if (self.wsib_on_ot or self.overtime_hours == 0)
                else self.base_wage * self.wsib_rate / 100
            ),
            "Health Benefits": self.health_benefits,
        }

    def total_hourly_cost(self):
        comps = self.cost_components()
        employer = (
            comps["Base Wage"]
            + comps["Vacation Pay"]
            + comps["CPP (Employer)"]
            + comps["EI (Employer)"]
            + comps["WSIB"]
            + comps["Health Benefits"]
        )
        employee = comps["CPP (Employee)"] + comps["EI (Employee)"]
        annual_hours = (self.weekly_hours + self.overtime_hours) * 52
        return employer, employee, employer * annual_hours, employee * annual_hours

    def to_dict(self):
        return self.__dict__.copy()

# Persistence
PROFILE_FILE = "employee_profiles.json"
def load_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    return {}
def save_profiles(profiles):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

# --- Streamlit UI ---
st.title("Ontario Employee Cost Calculator")

# Load and manage profiles
profiles = load_profiles()
search = st.sidebar.text_input("🔍 Search Profiles")
names = [k for k in profiles if search.lower() in k.lower()]

st.sidebar.markdown("---")
st.sidebar.subheader("Manage Profiles")
del_sel = st.sidebar.selectbox("Delete Profile", [""] + names)
if del_sel and st.sidebar.button("Delete"):
    profiles.pop(del_sel, None); save_profiles(profiles)
    st.sidebar.success(f"Deleted {del_sel}")

# Inputs
st.sidebar.header("Employee Inputs")
sel = st.sidebar.selectbox("Load Profile", [""] + names)
p = profiles.get(sel, {})

name = st.sidebar.text_input("Name", value=p.get("name", ""))
etype = st.sidebar.selectbox("Type",
    ["Full-Time","Part-Time","Temporary","Subcontractor","Salaried","Hourly"],
    index= ["Full-Time","Part-Time","Temporary","Subcontractor","Salaried","Hourly"].index(p.get("employment_type","Full-Time"))
)
bw = st.sidebar.number_input("Base Wage ($/hr)", 0.0, value=p.get("base_wage",0.0), step=0.01)
wh = st.sidebar.number_input("Weekly Hours", 0, value=p.get("weekly_hours",0))
ot = st.sidebar.number_input("Overtime Hrs/Wk", 0, value=p.get("overtime_hours",0))
vac = st.sidebar.number_input("Vacation Pay (%)", 0.0, value=p.get("vacation_pct",4.0), step=0.1)
wsb = st.sidebar.number_input("WSIB Rate (%)", 0.0, value=p.get("wsib_rate",1.30), step=0.01)
hb = st.sidebar.number_input("Health Benefits ($/hr)", 0.0, value=p.get("health_benefits",0.0), step=0.01)

with st.sidebar.expander("Assumptions", expanded=True):
    cap  = st.checkbox("Apply CPP/EI Caps", value=p.get("apply_caps",True))
    omt  = st.checkbox("1.5× Overtime",    value=p.get("apply_overtime",True))
    vacf = st.checkbox("Include Vacation", value=p.get("include_vacation",True))
    wsbf = st.checkbox("WSIB on Overtime", value=p.get("wsib_on_ot",True))

# Show assumption status
st.caption(f"📌 CPP/EI Caps: {'Yes' if cap else 'No'}")
st.caption(f"📌 Overtime×1.5: {'Yes' if omt else 'No'}")
st.caption(f"📌 Vacation: {'Yes' if vacf else 'No'}")
st.caption(f"📌 WSIB on OT: {'Yes' if wsbf else 'No'}")

if st.sidebar.button("Calculate"):
    cpp_r, ee_cpp_r, ei_r, ee_ei_r = fetch_contribution_rates()
    emp = Employee(name, etype, bw, wh, ot, vac, cpp_r, ei_r, wsb, hb, cap, omt, vacf, wsbf)
    hrly, ded, annual_e, annual_d = emp.total_hourly_cost()

    st.subheader(f"Cost Breakdown:  {name}")
    df = pd.DataFrame(emp.cost_components().items(), columns=["Component","$/hr"])
    st.dataframe(df)
    st.metric("Employer $/hr", f"${hrly:.2f}")
    st.metric("Employee Deduction $/hr", f"${ded:.2f}")
    st.metric("Annual Employer Cost", f"${annual_e:,.2f}")
    st.metric("Annual Deductions", f"${annual_d:,.2f}")
    for w in emp.warnings:
        st.warning(w)

    # Export CSV
    assump = pd.DataFrame({
        "Assumption": ["Caps","Overtime×1.5","Vacation","WSIB on OT"],
        "Value":      ["Yes" if cap else "No","Yes" if omt else "No","Yes" if vacf else "No","Yes" if wsbf else "No"]
    })
    combo = pd.concat([df, pd.DataFrame([{"Component":"","$/hr":""}]), assump.rename(columns={"Assumption":"Component","Value":"$/hr"})])
    csv = combo.to_csv(index=False).encode()
    ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button("Download CSV", csv, f"{name}_{ts}.csv","text/csv")

    # Save profile as new timestamped
    prof_key = f"{name}_{ts}"
    profiles[prof_key] = emp.to_dict()
    save_profiles(profiles)
    st.success(f"Saved profile: {prof_key}")
