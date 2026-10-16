# 🛠️ Troubleshooting Guide

Each problem is listed as **Symptom → Reason → Solution → Prevention**.

---

## 1. Installation errors

### `'python' is not recognized as an internal or external command` (Windows)
- **Reason:** Python is not on your PATH.
- **Solution:** Re-run the Python installer → *Modify* → tick **"Add python.exe to PATH"**. Or use the launcher: `py -3.11 -m venv venv`.
- **Prevention:** Always tick "Add to PATH" when installing Python.

### `venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled`
- **Reason:** PowerShell execution policy blocks scripts.
- **Solution:** `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (answer `Y`), then activate again. Or use Command Prompt: `venv\Scripts\activate.bat`.
- **Prevention:** Set the policy once per machine.

### `ERROR: Could not build wheels for ...` / `Microsoft Visual C++ 14.0 is required`
- **Reason:** Your Python version is too new or too old, so pip tries to compile from source.
- **Solution:** Use Python **3.10 – 3.13**, upgrade pip (`python -m pip install --upgrade pip`), retry.
- **Prevention:** Stick to the Python version in the README.

### `ModuleNotFoundError: No module named 'statsmodels'` (or any library)
- **Reason:** The virtual environment is not activated, or you installed into a different Python.
- **Solution:** Activate the venv (you should see `(venv)` in the prompt), then `pip install -r requirements.txt`. Check with `python -c "import sys; print(sys.executable)"` — the path must contain `venv`.
- **Prevention:** Activate the venv every time you open a new terminal.

## 2. Library conflicts

### `numpy.dtype size changed, may indicate binary incompatibility`
- **Reason:** A library was compiled against a different NumPy version.
- **Solution:** `pip install --upgrade --force-reinstall numpy pandas scikit-learn statsmodels`.
- **Prevention:** Install everything from `requirements.txt` in a *fresh* venv; don't mix `conda` and `pip` in one environment.

### `FutureWarning` / `DeprecationWarning` flood
- **Reason:** Newer pandas/seaborn versions warn about old syntax. Warnings are **not errors**.
- **Solution:** Ignore, or pin versions from `requirements.txt`.

## 3. Dataset loading issues

### `FileNotFoundError: data/raw/climate_data_raw.csv not found`
- **Reason:** Data has not been generated yet (raw CSVs are git-ignored).
- **Solution:** `python main.py --step generate` (or just `python main.py`).
- **Prevention:** Always run commands from the project root folder (`Climate-Trend-Analyzer/`).

### `ValueError: Dataset is missing required columns`
- **Reason:** You're loading an external CSV whose column names differ.
- **Solution:** Rename columns with `load_external_csv(path, column_map={...})` in `src/data_loader.py`, or rename in Excel to: `date, city, temp_mean, temp_max, temp_min, rainfall_mm, humidity_pct`.

### `UnicodeDecodeError` while reading a CSV
- **Solution:** `pd.read_csv(path, encoding="latin-1")`.

## 4. Date parsing issues

### Dates become `NaT`, or months and days are swapped (03/04 read as 4 March)
- **Reason:** Ambiguous formats like `DD/MM/YYYY` vs `MM/DD/YYYY`.
- **Solution:** Be explicit: `pd.to_datetime(df["date"], format="%d/%m/%Y")` or `dayfirst=True`.
- **Prevention:** Store dates as ISO `YYYY-MM-DD` (this project does).

### `TypeError: Only valid with DatetimeIndex` when resampling
- **Solution:** `df["date"] = pd.to_datetime(df["date"])` and `df.set_index("date")` before `.resample()`.

## 5. Plotting errors

### Charts don't appear / `UserWarning: Matplotlib is currently using agg`
- **Reason:** This project uses the non-GUI `Agg` backend on purpose — charts are **saved to `outputs/figures/`**, not shown in a window.
- **Solution:** Open the PNG files, or use the notebook / Streamlit dashboard for interactive views.

### `_tkinter.TclError: no display name`
- **Reason:** Running on a server without a screen.
- **Solution:** Already handled (`matplotlib.use("Agg")` in `src/utils.py`).

### Squashed or overlapping labels
- **Solution:** `fig.tight_layout()` or increase `figsize`.

## 6. Trend analysis issues

### Trend is "not significant" even though the chart rises
- **Reason:** Year-to-year variability is large compared with the trend, or the series is short.
- **Solution:** That *is* the correct answer — report it. Use ≥ 30 years of data for climate trends (WMO guideline).
- **Interview tip:** "Not significant" ≠ "no change"; it means the evidence isn't strong enough at α = 0.05.

### OLS and Sen's slope disagree
- **Reason:** Outliers (e.g. one extreme year) pull OLS; Sen's slope is robust. Trust Sen's slope + Mann-Kendall for climate series.

## 7. Anomaly detection issues

### Way too many anomalies in recent years
- **Reason:** Comparing against a fixed baseline without removing the warming trend → everything recent looks "hot".
- **Solution:** Detect on the **de-trended residual** (`temp_residual`) — already done in `feature_engineering.py`.

### Too few / too many anomalies overall
- **Solution:** Tune `ZSCORE_THRESHOLD` (2.5 = more sensitive, 3.5 = stricter) and `ISOLATION_CONTAMINATION` in `src/config.py`. Check `anomaly_detection_evaluation.csv` to see the precision/recall effect.

## 8. Forecasting issues

### `ConvergenceWarning: Maximum Likelihood optimization failed to converge`
- **Reason:** SARIMA optimiser struggled; common and usually harmless.
- **Solution:** Try `fit(disp=False, maxiter=200)` or a simpler order like `(1,0,0)(0,1,1,12)`.

### `LinAlgError: Schur decomposition solver error` / `LU decomposition error`
- **Reason:** Missing values or a constant series.
- **Solution:** `series.asfreq("MS").interpolate()` before fitting (already done).

### Forecast is a flat line
- **Reason:** No trend term. Add `trend="c"` with seasonal differencing (done), or use the linear trend model.

### Want Prophet?
- `pip install prophet` — it's optional. Prophet can fail to install on Windows; SARIMA covers the same need.

## 9. Git errors

### `fatal: not a git repository`
- **Solution:** `cd` into the project folder, then `git init`.

### `Author identity unknown — Please tell me who you are`
- **Solution:**
  ```bash
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
  ```

### `warning: LF will be replaced by CRLF`
- Harmless on Windows. To silence: `git config --global core.autocrlf true`.

### Accidentally committed `venv/`
- **Solution:** `git rm -r --cached venv` → make sure `venv/` is in `.gitignore` → commit.

## 10. GitHub upload issues

### `remote: Support for password authentication was removed`
- **Reason:** GitHub no longer accepts account passwords on the command line.
- **Solution:** Sign in with **GitHub CLI** (`gh auth login`) or **Git Credential Manager** (opens a browser login automatically on Windows). You can also create a Personal Access Token in GitHub → Settings → Developer settings — paste it yourself when Git asks; never commit it into a file.

### `! [rejected] main -> main (fetch first)`
- **Reason:** The GitHub repo has a commit (e.g. README created on the website) your local copy doesn't have.
- **Solution:** `git pull origin main --rebase` then `git push`.

### `error: src refspec main does not match any`
- **Reason:** No commits yet, or branch is called `master`.
- **Solution:** Make a commit first, then `git branch -M main` and push.

### `File ... is 105 MB; this exceeds GitHub's file size limit of 100 MB`
- **Solution:** Don't commit big CSVs (they're git-ignored here). If already committed: `git rm --cached <file>`, add to `.gitignore`, commit, push.

### README images don't show on GitHub
- **Reason:** Wrong relative path or case mismatch (GitHub is case-sensitive: `Image.PNG` ≠ `image.png`).
- **Solution:** Use paths relative to README, e.g. `![trend](outputs/figures/06_temperature_trend.png)`, and make sure the image is committed.
