# AI-Driven Unified Data Platform for Marine Biodiversity

An advanced, glassmorphic client-server platform that consolidates physical oceanography, commercial fisheries assessment, and molecular genomics into a unified real-time dashboard. The application runs dynamic machine learning anomaly detection on the backend and features a resilient hybrid offline fallback mode for zero-cost static web hosting.

---

## 🚀 How to Run the Project (Step-by-Step)

### Prerequisites
- **Python 3.11+** installed on your system.
- A modern web browser (Google Chrome, Firefox, or Edge).

### Step 1: Clone the Repository
Open a terminal (or PowerShell on Windows) and run:
```bash
git clone https://github.com/KGupta171025/AI-Driven_Unified_Data_Platform_for_Marine_Biodiversity.git
cd AI-Driven_Unified_Data_Platform_for_Marine_Biodiversity
```

### Step 2: Set Up Virtual Environment & Install Dependencies
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt)**:
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux**:
     ```bash
     source venv/bin/activate
     ```
3. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3: Run the Backend Flask Server
Start the Python application:
```bash
python AI_Driven_Unified.py
```
*Note: The server will start on `http://127.0.0.1:5000/`. A background daemon thread will automatically start drifting station sensor parameters and training the machine learning models.*

### Step 4: Access the Frontend Dashboard
Simply open `http://127.0.0.1:5000/` in your web browser. Alternatively, double-click the local `index.html` file at the project root to launch it.

### Step 5: Test the Static Fallback (Offline Mode)
If you close the Python backend terminal (stopping the Flask server) and refresh `index.html` in your browser, the dashboard will automatically detect the connection failure, print a warning in the console, and launch the **Client-Side Simulation Fallback Engine**, running the entire platform mockup locally using browser-based random walk calculations.

---

## 🛠️ Architecture & Core Components

```
                           ┌──────────────────────────────────────────────┐
                           │               Oceanic Sensors                │
                           └──────────────────────┬───────────────────────┘
                                                  │ Raw Readings
                                                  ▼
┌──────────────┐   User Requests   ┌──────────────┐   Visual Layers   ┌──────────────┐
│  Researcher  ├──────────────────>│ Marine Platform├─────────────────>│  Web Browser │
└──────────────┘                   └──────────────┘                   └──────────────┘
```

The platform is structured around a decoupled **three-tier architecture**:

1. **Presentation Layer (Frontend)**:
   - **Leaflet.js Map**: Renders an interactive GIS map styled in dark mode, plotting colored circle markers that represent the 5 stations. Clicking a marker loads details in a popup.
   - **Chart.js Timelines**: Plots 30-day timeline variations of temperature, salinity, and pH. Clicking a map marker dynamically updates this chart.
   - **Ecosystem Feed**: Polling script that retrieves real-time warning logs from the Flask server.
   - **Species Database Explorer**: Renders a list of fish populations filtered by name search or status tags. Clicking an entry opens a detailed risk metrics modal.
   - **Advanced mode**: Exposes Expected Heterozygosity bar charts and correlation matrices.

2. **Application Layer (Backend)**:
   - **Flask API**: Exposes JSON endpoints to serve live station states, chronological historical datasets, and genomics.
   - **Background Daemon**: Spawns a background thread that runs every 10 seconds, modifying sensor values via a normal distribution drift and updating an alert queue.
   - **StandardScaler Preprocessor**: Standardizes multivariate coordinates.
   - **IsolationForest Model**: Evaluates vectors to identify outliers (flagged as anomalies).

3. **Data Layer (In-memory Dataframes)**:
   - Structures baseline profiles representing 5 climate zones (Temperate, Subtropical, Tropical Reef, Polar, Deep Sea) into Pandas DataFrames, seeded with 150 historical records each.

---

## 📖 Key Scientific & Technical Terminology

- **Isolation Forest**: An unsupervised machine learning algorithm used for anomaly detection. Instead of profiling normal data points, it isolates anomalies by randomly partitioning feature splits. Outliers are isolated closer to the root of the tree structures, leading to faster detection.
- **StandardScaler**: A normalization method that standardizes features by removing the mean and scaling to unit variance:
  $$z = \frac{x - \mu}{\sigma}$$
  This ensures that parameters with different units (e.g. salinity in PSU vs. temperature in Celsius) are weighted equally by the machine learning model.
- **Biomass Reference Point ($B/B_{MSY}$)**: The ratio of current spawning fish biomass ($B$) to the biomass that yields maximum sustainable harvests ($B_{MSY}$). Ratios below $1.0$ indicate depleted stocks.
- **Fishing Mortality Reference Point ($F/F_{MSY}$)**: The ratio of current fishing mortality rates ($F$) to the mortality rate corresponding to maximum sustainable yield ($F_{MSY}$). Ratios above $1.0$ indicate overfishing.
- **Shannon-Weiner Index ($H'$)**: A mathematical measure of species diversity:
  $$H' = -\sum p_i \ln p_i$$
  It accounts for both species richness (how many species are present) and evenness (how equally abundance is distributed among species).
- **Simpson's Diversity Index ($1-D$)**: Represents the probability that two individuals randomly selected from a sample belong to different species:
  $$1 - D = 1 - \sum p_i^2$$
- **Pielou's Evenness ($J'$)**: Measures how evenly species abundances are distributed:
  $$J' = \frac{H'}{\ln(S)}$$
  Where $S$ is the total number of species.
- **Environmental DNA (eDNA)**: Nuclear or mitochondrial DNA shed by organisms into the surrounding water (via scales, mucus, waste). Sequencing this DNA allows researchers to log species presence without capturing them.
- **Hybrid Offline Fallback**: A connection check built into the frontend script. It pings the Flask server; if a 404/500 error or connection failure is caught, it seamlessly switches all data calls to a client-side random-walk simulation, allowing the UI to remain fully operational when offline.

---

## 🎤 How to Present the Project (Developer Pitch Guide)

When presenting this project to professors, examiners, or other developers, follow this structured narrative to explain your implementation choices clearly and confidently:

### 1. The Hook (The "Why")
> "Existing marine databases operate as fragmented, static archives. Ocean physical chemistry is stored separately from commercial fishing logs and environmental DNA profiles. Because these datasets are siloed, we cannot dynamically observe how a physical chemistry drift—like a sudden drop in pH or temperature anomaly—impacts local biodiversity. Our platform unifies these three domains into a single interactive dashboard powered by real-time data flows and machine learning."

### 2. The Core Backend & ML Logic (The "How")
> "We structured the backend in Python using Flask. Rather than relying on static mock databases, we created a dynamic simulator that models 5 stations across different climate zones. To make the platform smart, we implemented an unsupervised **Isolation Forest** model from Scikit-Learn.
>
> Every 10 seconds, a background daemon thread introduces diurnal drift to station parameters. These vectors are passed through a `StandardScaler` pipeline and evaluated by the Isolation Forest. If a multivariate anomaly is detected (such as pH dropping concurrently with temperature rising), the system logs an alert to a real-time feed queue, which the client UI polls every 5 seconds.
>
> For biology, the platform calculates biological reference points ($B/B_{MSY}$ and $F/F_{MSY}$) to track overfishing, and implements molecular biology equations to compute Shannon, Simpson, and Pielou diversity indices from environmental DNA sequence tables."

### 3. The Frontend Aesthetics & Resilience (The "UI & Hosting")
> "For the interface, we implemented a premium glassmorphic dark UI using HTML, CSS grid, and JavaScript. We integrated a **Leaflet GIS map** with a dark tile overlay to map the stations. We bound map markers to **Chart.js timeline plots** so that clicking on a station dynamically re-plots its historical dataset.
>
> One of our key engineering highlights is the **Hybrid Offline Fallback Mode**. Realizing that hosting active Python Flask servers continuously is expensive, we implemented a connection monitor. If the server is offline, the client script pings the endpoint, catches the failure, and launches a local client-side random-walk engine. This allows us to host the dashboard for free on GitHub Pages as a static site while keeping all charts, map actions, feeds, and explorers fully animated and interactive."

### 4. Technical QA: Questions & Answers

*   **Q: Why use an Isolation Forest instead of a standard classifier?**
    *   *A: "Environmental data lacks labels (i.e. we don't have thousands of pre-flagged 'anomaly' records). Isolation Forest is an unsupervised algorithm that doesn't need labels. It works by isolating data points. Anomalies are isolated much faster and require fewer partitions than normal points, making this model highly efficient and robust for high-frequency multivariate streams."*
*   **Q: How does the hybrid fallback detect the server state?**
    *   *A: "During DOM content loading, the frontend makes an async `fetch('/api/stations')` call inside a `try-catch` block. If the server is offline, the request fails and throws an error. The `catch` block catches this error, logs a console warning, and calls `initializeClientSimulation()`, which loads local state arrays and starts the random-walk update cycles."*
*   **Q: Why standard scaling?**
    *   *A: "Ocean parameters have vastly different units. Temperature is in Celsius (0-30), Salinity is in PSU (30-36), and pH is 0-14. Without standard scaling, the Isolation Forest would over-index on temperature changes because its numerical range is wider. `StandardScaler` normalizes features to a mean of 0 and variance of 1, ensuring every sensor parameter contributes equally to anomaly classification."*
