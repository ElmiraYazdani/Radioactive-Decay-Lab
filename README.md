 # ⚛️ Radioactive Decay Lab

An interactive teaching app for parent–daughter radioactive decay:
- Secular equilibrium
- Transient equilibrium
- No equilibrium
- Bateman daughter-activity equation
- Daughter activity maximum
- Interactive graphs, example comparisons, and a short quiz

## Run on Windows

1. Install Python 3.10 or newer.
2. Open PowerShell in this folder.
3. Create and activate a virtual environment (recommended):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```powershell
pip install -r requirements.txt
```

5. Start the platform:

```powershell
streamlit run app.py
```

The app will open in your browser, usually at http://localhost:8501.

## Physics notes

The app uses the exact two-member Bateman activity equation for a parent feeding one daughter.
The secular/transient classification uses a transparent teaching convention:
Tp/Td >= 100 is labeled secular, 1 < Tp/Td < 100 transient, and Tp/Td <= 1 no equilibrium.
The 100-fold cutoff is a practical classroom threshold, not a universal physical boundary.

For the Ra-226 → Rn-222 example, the Rn-222 half-life is set to approximately 3.8235 days.
