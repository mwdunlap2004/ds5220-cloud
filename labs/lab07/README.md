# Lab: Reproducible Data Science with Dev Containers

**Course:** DS5220 | **Duration:** 45 minutes | **Tools:** VS Code or Cursor

---

## Learning Objectives

By the end of this lab you will be able to:

- Create a project with a Dev Container configuration
- Write a `Dockerfile` and `requirements.txt` to define a reproducible environment
- Open a project inside a running container
- Write a short data science script that fetches, cleans, and visualizes real data

---

## Background

A **Dev Container** packages your development environment — Python version, libraries, system tools — into a Docker container. Anyone who opens the project gets the exact same environment, eliminating "works on my machine" problems. This is especially important for data science, where library version mismatches routinely break code.

This is another powerful use case for containers, in what DevOps calls a shift-left strategy - implementing a technology earlier in the development process (the left end) and not only in production (the right end).

---

## Prerequisites

Before starting, make sure you have:

- [ ] [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and **running** (check for the whale icon in your menu bar)
- [ ] [VS Code](https://code.visualstudio.com/) or [Cursor](https://www.cursor.com/) installed
- [ ] The **Dev Containers** extension installed in your IDE. (Or install the custom [**SDS Extension Pack**](https://marketplace.visualstudio.com/items?itemName=uva-school-of-data-science.sds-vscode).)

### Confirm the Dev Containers extension is installed

1. Open VS Code or Cursor
2. Click the **Extensions** icon in the left sidebar (or press `Cmd+Shift+X` / `Ctrl+Shift+X`)
3. Search for **Dev Containers** (publisher: Microsoft)
4. If it shows **Install**, click it — otherwise you are good to go

> **Tip:** You should see a small green `><` icon in the very bottom-left corner of your IDE window once the extension is active.

---

## Part 1 — Create a New Project (5 min)

**Step 1.** Create a new folder for your project. Open a terminal and run:

```bash
mkdir worldbank-lab && cd worldbank-lab
```

**Step 2.** Open the folder in your IDE:

```bash
code .        # VS Code
# or
cursor .      # Cursor
```

You should see an empty Explorer panel on the left.

---

## Part 2 — Add Dev Container Configuration (10 min)

**Step 3.** Create the `.devcontainer` directory and its configuration file. In your IDE, create the following folder and file:

```
worldbank-lab/
└── .devcontainer/
    └── devcontainer.json
```

You can do this from the Explorer panel: click **New Folder**, name it `.devcontainer`, then click **New File** inside it and name it `devcontainer.json`.

**Step 4.** Paste the following into `devcontainer.json`:

```json
{
  "name": "World Bank Lab",
  "build": {
    "dockerfile": "Dockerfile"
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  },
  "postCreateCommand": "pip install -r requirements.txt"
}
```

> **What this does:**
> - `"build"` points to a `Dockerfile` in the same folder
> - `"extensions"` auto-installs the Python extension inside the container
> - `"postCreateCommand"` runs `pip install` automatically when the container is first created

**Step 5.** Create the `Dockerfile` inside `.devcontainer/`:

```
worldbank-lab/
└── .devcontainer/
    ├── devcontainer.json
    └── Dockerfile          <-- new
```

Paste the following into the `Dockerfile`:

```dockerfile
FROM python:3.13-slim  # could use 3.11 or 3.12

# Install system dependencies needed by matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
```

> **What this does:** Starts from an official Python 3.11 image, installs the C compiler that some Python packages need, and sets `/workspace` as the working directory.

**Step 6.** Create `requirements.txt` in the **root** of your project (not inside `.devcontainer`):

```
worldbank-lab/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
└── requirements.txt        <-- new
```

Paste the following:

```
requests==2.31.0
pandas==2.2.2
matplotlib==3.9.0
```

Your project tree should now look like this:

```
worldbank-lab/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Dockerfile
└── requirements.txt
```

---

## Part 3 — Reopen in the Dev Container (5 min)

**Step 7.** Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) and run:

```
Dev Containers: Reopen in Container
```

Your IDE will:
1. Build the Docker image from your `Dockerfile` (this takes 1–2 minutes the first time)
2. Start a container from that image
3. Mount your project folder into the container
4. Install your Python packages via `postCreateCommand`
5. Reconnect your IDE window inside the running container

> **How to tell it worked:** The bottom-left corner of your IDE should show something like `Dev Container: World Bank Lab` in green.

**Step 8.** Verify the environment. Open the integrated terminal (`Ctrl+`` ` or Terminal > New Terminal`) and run:

```bash
python --version   # should show Python 3.11.x
pip list           # should show pandas, matplotlib, requests
```

---

## Part 4 — Write the Data Science Script (20 min)

You are going to reproduce a classic data visualization — the **Gapminder bubble chart** — using live data from the [World Bank Open Data API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392). No API key is required.

You will fetch three development indicators across every country on Earth:

| Indicator | World Bank Code |
|---|---|
| GDP per capita (current USD) | `NY.GDP.PCAP.CD` |
| Life expectancy at birth (years) | `SP.DYN.LE00.IN` |
| Total population | `SP.POP.TOTL` |

**Step 9.** Create `worldbank_analysis.py` in the project root.

**Step 10.** Work through each section below, running the script after each one.

---

### Section A — Fetch country metadata

The World Bank API mixes actual countries with regional aggregates ("East Asia & Pacific", "High income", etc.). The first thing we need is a clean list of real countries and which world region each belongs to.

```python
import requests
import pandas as pd

BASE = "https://api.worldbank.org/v2"

def wb_get(path, **params):
    """Call the World Bank API and return (metadata, data_list)."""
    params.setdefault("format", "json")
    params.setdefault("per_page", 1000)
    r = requests.get(f"{BASE}/{path}", params=params)
    r.raise_for_status()
    meta, data = r.json()
    return meta, data

# Step 1: load every country entry and keep only real sovereign countries
# (aggregates have region == "Aggregates")
_, raw_countries = wb_get("country", per_page=300)

countries = pd.DataFrame([{
    "iso2":   c["iso2Code"].strip(),
    "name":   c["name"],
    "region": c["region"]["value"],
    "income": c["incomeLevel"]["value"],
} for c in raw_countries])

countries = countries[countries["region"] != "Aggregates"].copy()
print(f"Countries loaded: {len(countries)}")
print(countries.head())
```

Run the script — you should see roughly 215 countries.

---

### Section B — Fetch the three indicators

```python
def fetch_indicator(code, col_name):
    """
    Fetch the most recent available value of an indicator for all countries.
    mrv=1 means 'most recent value' — no need to specify a year.
    """
    _, rows = wb_get(f"country/all/indicator/{code}", mrv=1)
    return pd.DataFrame([{
        "iso2":  row["country"]["id"].strip(),
        "year":  int(row["date"]),
        col_name: row["value"],
    } for row in rows if row["value"] is not None])

gdp  = fetch_indicator("NY.GDP.PCAP.CD", "gdp_per_capita")
life = fetch_indicator("SP.DYN.LE00.IN", "life_expectancy")
pop  = fetch_indicator("SP.POP.TOTL",    "population")

print(f"GDP rows:  {len(gdp)}")
print(f"Life rows: {len(life)}")
print(f"Pop rows:  {len(pop)}")
```

---

### Section C — Merge and clean

```python
# Merge the three indicators on country code, then join in region labels
df = gdp.merge(life[["iso2", "life_expectancy"]], on="iso2", how="inner")
df = df.merge(pop[["iso2",  "population"]],       on="iso2", how="inner")
df = df.merge(countries[["iso2", "name", "region", "income"]], on="iso2", how="inner")

# Drop any rows still missing values after the merge
df = df.dropna(subset=["gdp_per_capita", "life_expectancy", "population"])

# Sanity-check the ranges
print(f"\nRows after cleaning: {len(df)}")
print(f"GDP per capita:   ${df['gdp_per_capita'].min():,.0f}  –  ${df['gdp_per_capita'].max():,.0f}")
print(f"Life expectancy:  {df['life_expectancy'].min():.1f}  –  {df['life_expectancy'].max():.1f} years")
print(f"Population:       {df['population'].min():,.0f}  –  {df['population'].max():,.0f}")
print(f"\nRegions:\n{df['region'].value_counts()}")
```

Run and confirm the numbers look reasonable. Notice that GDP spans three orders of magnitude — that will matter for how we scale the axes.

---

### Section D — Fetch a time series for selected countries

For one of the plots we want to see how GDP per capita has evolved over time. We will pull annual data for six countries that tell a compelling story together.

```python
FOCUS_COUNTRIES = {
    "US": "United States",
    "CN": "China",
    "IN": "India",
    "BR": "Brazil",
    "NG": "Nigeria",
    "DE": "Germany",
}

codes = ";".join(FOCUS_COUNTRIES.keys())
_, ts_raw = wb_get(
    f"country/{codes}/indicator/NY.GDP.PCAP.CD",
    date="2000:2023",
    per_page=500,
)

ts = pd.DataFrame([{
    "iso2":          row["country"]["id"],
    "country":       row["country"]["value"],
    "year":          int(row["date"]),
    "gdp_per_capita": row["value"],
} for row in ts_raw if row["value"] is not None])

ts = ts.sort_values(["country", "year"])
print(ts.head(12))
```

---

### Section E — Plot

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 1, figsize=(12, 16))
fig.suptitle("Global Development Indicators — World Bank Open Data", fontsize=15)

# Assign a consistent color to each region
regions = sorted(df["region"].unique())
palette = plt.cm.Set2.colors
region_color = {r: palette[i % len(palette)] for i, r in enumerate(regions)}

# ── Plot 1: Gapminder bubble chart ───────────────────────────────────────────
ax = axes[0]

for region, group in df.groupby("region"):
    # Scale bubble area by square-root of population so China doesn't swamp everything
    sizes = (group["population"] ** 0.5) / 500
    ax.scatter(
        group["gdp_per_capita"],
        group["life_expectancy"],
        s=sizes,
        alpha=0.65,
        color=region_color[region],
        label=region,
        edgecolors="white",
        linewidths=0.3,
    )

# Label a handful of notable countries
LABEL_COUNTRIES = {"United States", "China", "India", "Nigeria", "Germany", "Brazil", "Japan"}
for _, row in df[df["name"].isin(LABEL_COUNTRIES)].iterrows():
    ax.annotate(row["name"],
                xy=(row["gdp_per_capita"], row["life_expectancy"]),
                fontsize=7, ha="left", va="bottom",
                xytext=(4, 2), textcoords="offset points")

ax.set_xscale("log")
ax.set_xlabel("GDP per Capita, USD (log scale)")
ax.set_ylabel("Life Expectancy (years)")
ax.set_title("GDP per Capita vs. Life Expectancy  (bubble size ∝ population)")
ax.legend(fontsize=7, loc="lower right", title="Region")

# ── Plot 2: Life expectancy by region (horizontal bar) ───────────────────────
ax = axes[1]
regional_life = (
    df.groupby("region")["life_expectancy"]
    .mean()
    .sort_values(ascending=True)
)
colors_bar = [region_color[r] for r in regional_life.index]
regional_life.plot(kind="barh", ax=ax, color=colors_bar, edgecolor="white")

global_avg = df["life_expectancy"].mean()
ax.axvline(global_avg, color="black", linestyle="--", linewidth=1,
           label=f"Global avg: {global_avg:.1f} yrs")
ax.set_xlabel("Average Life Expectancy (years)")
ax.set_title("Average Life Expectancy by World Region")
ax.legend()

# ── Plot 3: GDP per capita over time — selected countries ────────────────────
ax = axes[2]
for country, group in ts.groupby("country"):
    ax.plot(group["year"], group["gdp_per_capita"],
            marker="o", markersize=3, linewidth=1.5, label=country)

ax.set_xlabel("Year")
ax.set_ylabel("GDP per Capita (USD)")
ax.set_title("GDP per Capita Over Time — Selected Countries (2000 – 2023)")
ax.legend(fontsize=8)
ax.set_xlim(2000, 2023)

plt.tight_layout()
plt.savefig("worldbank_analysis.png", dpi=150, bbox_inches="tight")
print("\nPlot saved to worldbank_analysis.png")
```

**Step 11.** Run the complete script:

```bash
python worldbank_analysis.py
```

Open `worldbank_analysis.png` from the Explorer panel. You should see:

1. **Bubble chart** — the familiar S-curve: richer countries live longer; Asia's giants are unmistakable by bubble size
2. **Bar chart** — the life-expectancy gap between Sub-Saharan Africa and Europe is stark (~17 years)
3. **Time series** — China's rise from ~$1,000 to ~$12,000 per capita in two decades next to Nigeria's near-flat line

---

## Part 5 — Checkpoint & Discussion (5 min)

Answer the following questions as comments at the top of `worldbank_analysis.py`:

1. What problem does the `Dockerfile` solve that a plain `requirements.txt` cannot?
2. Why is `postCreateCommand` useful instead of asking users to run `pip install` manually?
3. If a teammate opens this repo, what single action replicates your entire environment?
4. The World Bank data uses `mrv=1` — "most recent value" — which means different countries may report different years. What are the implications for the bubble chart? How would you investigate or mitigate this?

---

## Bonus Challenges

If you finish early, try one or more of the following:

- **Rework the dataframes:** use either Polars or DuckDB to pull and transform the data. Do either of these have a distinct advantage?
- **Add a fourth indicator:** fetch school enrollment (`SE.PRI.ENRR`) or CO₂ emissions (`EN.ATM.CO2E.PC`) and add it as a color dimension to the bubble chart.
- **Annotate outliers:** find the five countries with the largest gap between their expected life expectancy (given their GDP) and their actual life expectancy, and annotate them on the scatter plot.
- **Snapshot the data:** save `df` to `snapshot.csv` immediately after cleaning — this makes your analysis reproducible even if the live API changes.
- **Add seaborn:** add `seaborn==0.13.2` to `requirements.txt`, run `Dev Containers: Rebuild Container`, and re-style the bar chart using `sns.barplot`.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Docker daemon not running" | Open Docker Desktop and wait for it to fully start |
| Build fails on `apt-get` | Check your internet connection; corporate proxies sometimes block package managers |
| `ModuleNotFoundError` after rebuild | Make sure `requirements.txt` is in the project root, not inside `.devcontainer` |
| Plot file is empty or corrupt | Ensure `matplotlib.use("Agg")` is called before `import matplotlib.pyplot` |
| `ValueError: not enough values to unpack` on `r.json()` | The API returned an error object instead of `[meta, data]`; print `r.text` to see the message |
| Zero rows after merge | Run `print(gdp["iso2"].head())` — extra whitespace in ISO codes is a common culprit; the `.strip()` calls in the fetch functions guard against this |

---

## Submitting Your Work

Create a single PDF containing the following, and upload to Canvas:

- [ ] `.devcontainer/devcontainer.json`
- [ ] `.devcontainer/Dockerfile`
- [ ] `requirements.txt`
- [ ] `worldbank_analysis.py`
- [ ] `worldbank_analysis.png`
