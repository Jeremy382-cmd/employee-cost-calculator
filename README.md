# Ontario Employee Cost Calculator

This Streamlit app helps businesses in Ontario calculate the true hourly and annual cost of employees, factoring in employer contributions, benefits, and other configurable assumptions.

## 🔧 Features
- Calculates total **hourly** and **annual** employer costs
- Separates **employee deductions** (CPP, EI)
- Dynamic inputs for:
  - Full-time, part-time, subcontract, temp, salaried, or hourly
  - Overtime hours
  - Vacation pay
  - WSIB rate
  - Health benefits
- Real-time toggles for:
  - CPP/EI annual contribution caps
  - 1.5x overtime multiplier
  - Vacation pay inclusion
  - WSIB on overtime
- Save and reload employee profiles
- Searchable, overwriteable, and deletable profile management
- Downloadable cost breakdown with assumptions embedded in CSV

## 📁 Files
| File | Description |
|------|-------------|
| `app.py` | The full Streamlit app code |
| `employee_profiles.json` | Stores saved profiles (initially `{}`) |
| `requirements.txt` | Required libraries (Streamlit, pandas) |

## 🚀 How to Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy on Streamlit Cloud
1. Push all files to a GitHub repo
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Link your repo and deploy `app.py`

## ✅ Requirements
```
streamlit
pandas
```

## 📌 Example Assumptions (2025)
- CPP: 5.95% (max $4,055.50)
- EI: 1.64% employee / 2.30% employer (max $1,049.12 / $1,468.77)
- WSIB: Manual rate input per $100 earnings

## 📞 Support
For help or feedback, contact your developer or submit an issue on your repository.
