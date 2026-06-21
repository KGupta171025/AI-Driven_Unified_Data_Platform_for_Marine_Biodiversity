# Complete AI-Driven Unified Data Platform for Marine Biodiversity
# Integrated Backend Server
# Author: Krishna Gupta
# Contact: hg497kg@gmail.com | +91 9993153109

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import json
import warnings
import os
import time
import threading
from datetime import datetime, timedelta

# Flask imports for web interface
from flask import Flask, render_template, jsonify, request

warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# Static Configuration
# ---------------------------------------------------------
STATIONS = {
    "Pacific Station Alpha": {"lat": 36.7783, "lon": -119.4179, "zone": "Temperate"},
    "Atlantic Station Beta": {"lat": 25.7617, "lon": -80.1918, "zone": "Subtropical"},
    "Coral Sea Monitor": {"lat": -18.2871, "lon": 147.6992, "zone": "Tropical Reef"},
    "Arctic Research Point": {"lat": 75.0, "lon": 0.0, "zone": "Polar"},
    "South Atlantic Deep": {"lat": -23.5505, "lon": -46.6333, "zone": "Deep Sea"}
}

SPECIES_METADATA = {
    "Atlantic Bluefin Tuna": {"scientific_name": "Thunnus thynnus", "zone": "North Atlantic", "base_cpue": 12.5, "price": 24.50, "risk_factors": ["Overfishing", "Ocean warming", "Spawning habitat disruption"]},
    "Pacific Salmon": {"scientific_name": "Oncorhynchus kisutch", "zone": "North Pacific", "base_cpue": 28.3, "price": 16.20, "risk_factors": ["River temperature spikes", "Dam construction", "Ocean acidification"]},
    "European Sardine": {"scientific_name": "Sardina pilchardus", "zone": "Mediterranean", "base_cpue": 145.7, "price": 5.80, "risk_factors": ["Plankton availability shift", "Coastal pollution", "Predation pressure"]},
    "Antarctic Krill": {"scientific_name": "Euphausia superba", "zone": "Southern Ocean", "base_cpue": 890.2, "price": 3.90, "risk_factors": ["Sea ice retreat", "Acidification on larvae", "Commercial harvest increase"]},
    "North Sea Cod": {"scientific_name": "Gadus morhua", "zone": "North Sea", "base_cpue": 34.6, "price": 13.50, "risk_factors": ["Warm water displacement", "Bycatch mortality", "Habitat loss"]}
}

EDNA_SPECIES_LIST = [
    {"name": "Orcinus orca", "common": "Killer Whale", "taxa": "Mammal"},
    {"name": "Carcharodon carcharias", "common": "Great White Shark", "taxa": "Elasmobranch"},
    {"name": "Chelonia mydas", "common": "Green Sea Turtle", "taxa": "Reptile"},
    {"name": "Gadus morhua", "common": "Atlantic Cod", "taxa": "Actinopterygii"},
    {"name": "Thunnus thynnus", "common": "Atlantic Bluefin Tuna", "taxa": "Actinopterygii"},
    {"name": "Sardina pilchardus", "common": "European Sardine", "taxa": "Actinopterygii"},
    {"name": "Euphausia superba", "common": "Antarctic Krill", "taxa": "Crustacea"},
    {"name": "Dermochelys coriacea", "common": "Leatherback Sea Turtle", "taxa": "Reptile"},
    {"name": "Balaenoptera musculus", "common": "Blue Whale", "taxa": "Mammal"},
    {"name": "Manta birostris", "common": "Giant Oceanic Manta Ray", "taxa": "Elasmobranch"}
]

# ---------------------------------------------------------
# 1. Oceanographic Analyzer
# ---------------------------------------------------------
class OceanographicAnalyzer:
    """Handles oceanographic data analysis and environmental monitoring."""
    
    def __init__(self):
        self.data = None
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(contamination=0.08, random_state=42)
        
    def generate_oceanographic_data(self, days_history=30):
        """Generate synthetic oceanographic timeseries for designated stations."""
        np.random.seed(42)
        records = []
        now = datetime.now()
        
        for name, info in STATIONS.items():
            lat, lon, zone = info["lat"], info["lon"], info["zone"]
            
            # Establish baseline values based on climate zones
            if zone == "Temperate":
                base_temp, temp_std = 15.0, 1.8
                base_salinity, salinity_std = 33.8, 0.3
                base_ph, ph_std = 8.1, 0.04
                base_do, do_std = 8.0, 0.4
                base_chlorophyll, chloro_std = 2.2, 0.4
                base_turbidity, turb_std = 1.0, 0.2
                depth_dist = lambda: np.random.exponential(150.0)
            elif zone == "Subtropical":
                base_temp, temp_std = 22.5, 1.5
                base_salinity, salinity_std = 36.1, 0.2
                base_ph, ph_std = 8.15, 0.03
                base_do, do_std = 7.1, 0.3
                base_chlorophyll, chloro_std = 0.6, 0.15
                base_turbidity, turb_std = 0.5, 0.1
                depth_dist = lambda: np.random.exponential(250.0)
            elif zone == "Tropical Reef":
                base_temp, temp_std = 27.2, 1.2
                base_salinity, salinity_std = 35.0, 0.2
                base_ph, ph_std = 8.22, 0.03
                base_do, do_std = 6.4, 0.3
                base_chlorophyll, chloro_std = 1.1, 0.2
                base_turbidity, turb_std = 0.3, 0.08
                depth_dist = lambda: np.random.uniform(5.0, 45.0)
            elif zone == "Polar":
                base_temp, temp_std = 1.5, 1.4
                base_salinity, salinity_std = 32.4, 0.4
                base_ph, ph_std = 8.05, 0.05
                base_do, do_std = 9.8, 0.5
                base_chlorophyll, chloro_std = 1.4, 0.5
                base_turbidity, turb_std = 1.8, 0.4
                depth_dist = lambda: np.random.exponential(350.0)
            else:  # Deep Sea
                base_temp, temp_std = 2.4, 0.4
                base_salinity, salinity_std = 34.7, 0.06
                base_ph, ph_std = 7.82, 0.04
                base_do, do_std = 4.6, 0.2
                base_chlorophyll, chloro_std = 0.02, 0.005
                base_turbidity, turb_std = 0.4, 0.15
                depth_dist = lambda: np.random.normal(2800.0, 400.0)
            
            for day in range(days_history):
                timestamp = now - timedelta(days=days_history - day)
                
                # Diurnal/seasonal variations
                time_factor = np.sin((day / 30.0) * 2 * np.pi)
                
                temp = base_temp + (temp_std * time_factor) + np.random.normal(0, temp_std * 0.3)
                salinity = base_salinity + np.random.normal(0, salinity_std * 0.3)
                ph = base_ph + np.random.normal(0, ph_std * 0.3)
                do = base_do - (0.1 * (temp - base_temp)) + np.random.normal(0, do_std * 0.3)
                chlorophyll = max(0.01, base_chlorophyll + (chloro_std * time_factor) + np.random.normal(0, chloro_std * 0.2))
                turbidity = max(0.01, base_turbidity + np.random.normal(0, turb_std * 0.3))
                depth = max(1.0, depth_dist())
                
                records.append({
                    "timestamp": timestamp.isoformat(),
                    "station_name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "zone": zone,
                    "depth_m": depth,
                    "temperature_c": temp,
                    "salinity_psu": salinity,
                    "ph_level": ph,
                    "dissolved_oxygen_mg_l": do,
                    "chlorophyll_a_mg_m3": chlorophyll,
                    "turbidity_ntu": turbidity
                })
        
        self.data = pd.DataFrame(records)
        
        # Train and fit anomaly detection
        features = ['temperature_c', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_l', 'chlorophyll_a_mg_m3', 'turbidity_ntu']
        X = self.data[features].fillna(self.data[features].median())
        X_scaled = self.scaler.fit_transform(X)
        self.anomaly_detector.fit(X_scaled)
        
        self.detect_anomalies()
        return self.data
    
    def detect_anomalies(self):
        """Run IsolationForest anomaly detection on current data."""
        if self.data is None:
            raise ValueError("Oceanographic data not loaded.")
        
        features = ['temperature_c', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_l', 'chlorophyll_a_mg_m3', 'turbidity_ntu']
        X = self.data[features].fillna(self.data[features].median())
        X_scaled = self.scaler.transform(X)
        
        preds = self.anomaly_detector.predict(X_scaled)
        self.data['anomaly'] = preds == -1
        return self.data[self.data['anomaly']]
    
    def get_station_history(self, station_name, limit=30):
        """Fetch historical records for a specific station."""
        if self.data is None:
            return []
        
        station_df = self.data[self.data['station_name'] == station_name].sort_values('timestamp')
        history = station_df.tail(limit)
        
        # Format timestamps for ChartJS
        dates = [datetime.fromisoformat(t).strftime('%m-%d') for t in history['timestamp']]
        
        return {
            'dates': dates,
            'temperature': history['temperature_c'].round(2).tolist(),
            'salinity': history['salinity_psu'].round(2).tolist(),
            'ph_levels': history['ph_level'].round(2).tolist(),
            'dissolved_oxygen': history['dissolved_oxygen_mg_l'].round(2).tolist(),
            'chlorophyll': history['chlorophyll_a_mg_m3'].round(2).tolist(),
            'turbidity': history['turbidity_ntu'].round(2).tolist()
        }

# ---------------------------------------------------------
# 2. Fisheries Analyzer
# ---------------------------------------------------------
class FisheriesAnalyzer:
    """Handles fisheries stock assessments and catch modeling."""
    
    def __init__(self):
        self.data = None
        
    def generate_fisheries_data(self, history_points=30):
        """Simulate fish catches and biological stock indexes over time."""
        np.random.seed(42)
        records = []
        now = datetime.now()
        
        for name, meta in SPECIES_METADATA.items():
            base_cpue = meta["base_cpue"]
            zone = meta["zone"]
            
            # Simulate historical trends
            # Overfished species will exhibit declining biomass and higher effort
            if name in ["Atlantic Bluefin Tuna", "North Sea Cod"]:
                biomass_trend = np.linspace(1.1, 0.45, history_points)
                effort_trend = np.linspace(8.0, 12.0, history_points)
            elif name in ["Pacific Salmon", "Yellowfin Tuna"]:
                biomass_trend = np.linspace(0.95, 0.85, history_points)
                effort_trend = np.linspace(6.0, 7.5, history_points)
            else:  # Sustainable species (Sardines, Krill)
                biomass_trend = np.linspace(1.1, 1.25, history_points)
                effort_trend = np.linspace(4.0, 4.5, history_points)
                
            for i in range(history_points):
                timestamp = now - timedelta(days=history_points - i)
                noise = np.random.normal(0, 0.05)
                
                biomass = max(0.1, biomass_trend[i] + noise)
                effort = max(1.0, effort_trend[i] + np.random.normal(0, 0.5))
                
                # CPUE = biomass * catchability coefficient
                cpue = base_cpue * biomass * np.random.lognormal(0, 0.15)
                catch_kg = cpue * effort
                
                records.append({
                    "timestamp": timestamp.isoformat(),
                    "species": name,
                    "scientific_name": meta["scientific_name"],
                    "fishing_zone": zone,
                    "catch_kg": catch_kg,
                    "fishing_effort_hours": effort,
                    "cpue": cpue,
                    "biomass_index": biomass,  # B/Bmsy proxy
                    "mortality_index": (effort / 8.0) * np.random.uniform(0.8, 1.2)  # F/Fmsy proxy
                })
                
        self.data = pd.DataFrame(records)
        return self.data
    
    def stock_assessment(self):
        """Assess sustainability based on biological reference points (B/Bmsy and F/Fmsy)."""
        if self.data is None:
            raise ValueError("Fisheries data not loaded.")
        
        assessment = {}
        # Get latest records for each species
        for name in SPECIES_METADATA.keys():
            species_df = self.data[self.data['species'] == name].sort_values('timestamp')
            latest = species_df.iloc[-1]
            
            b_ratio = float(latest['biomass_index'])
            f_ratio = float(latest['mortality_index'])
            
            # Classification
            if b_ratio >= 1.0 and f_ratio <= 1.1:
                status = "Sustainable"
            elif b_ratio < 0.75:
                status = "Overfished"
            else:
                status = "Moderate"
                
            # Compute recent CPUE slope
            cpue_values = species_df['cpue'].tail(10).values
            slope = float(np.polyfit(range(len(cpue_values)), cpue_values, 1)[0])
            
            assessment[name] = {
                "scientific_name": latest['scientific_name'],
                "zone": latest['fishing_zone'],
                "cpue": float(latest['cpue']),
                "b_ratio": b_ratio,
                "f_ratio": f_ratio,
                "cpue_trend": slope,
                "status": status,
                "average_catch": float(species_df['catch_kg'].mean()),
                "total_value": float(latest['catch_kg'] * SPECIES_METADATA[name]['price']),
                "risk_factors": SPECIES_METADATA[name]['risk_factors']
            }
            
        return assessment

# ---------------------------------------------------------
# 3. Molecular Biodiversity Analyzer
# ---------------------------------------------------------
class MolecularBiodiversityAnalyzer:
    """Handles molecular DNA monitoring and ecological index calculations."""
    
    def __init__(self):
        self.data = None
        
    def generate_molecular_data(self, zones=7, samples_per_zone=20):
        """Simulate eDNA sequencing results across distinct zones (Zone A-G)."""
        np.random.seed(42)
        records = []
        zone_names = [f"Zone {chr(65+i)}" for i in range(zones)]
        
        for zone in zone_names:
            # Set different richness baselines for zones
            if zone in ["Zone C", "Zone E"]:  # Coral Sea Reef & Coastal Estuaries - high diversity
                abundance_multiplier = 4.0
                richness_prob = [0.85, 0.70, 0.90, 0.60, 0.75, 0.80, 0.40, 0.78, 0.50, 0.85]
            elif zone in ["Zone D", "Zone G"]:  # Polar & Deep Trench - low richness, specialized abundance
                abundance_multiplier = 2.5
                richness_prob = [0.10, 0.05, 0.05, 0.85, 0.20, 0.15, 0.92, 0.05, 0.35, 0.15]
            else:  # Moderate zones
                abundance_multiplier = 3.0
                richness_prob = [0.45, 0.50, 0.30, 0.60, 0.50, 0.55, 0.50, 0.35, 0.40, 0.45]
                
            for s in range(samples_per_zone):
                sample_id = f"eDNA_{zone.replace(' ', '')}_{s:02d}"
                species_counts = {}
                
                for idx, item in enumerate(EDNA_SPECIES_LIST):
                    sp_name = item["name"]
                    # Calculate abundance using Log-Normal distribution
                    if np.random.random() < richness_prob[idx]:
                        count = int(np.random.lognormal(mean=2.0, sigma=0.8) * abundance_multiplier)
                        if count > 0:
                            species_counts[sp_name] = count
                            
                # Ensure we have at least some counts
                if not species_counts:
                    species_counts[EDNA_SPECIES_LIST[0]["name"]] = 5
                    
                records.append({
                    "sample_id": sample_id,
                    "zone": zone,
                    "species_abundance": species_counts,
                    "depth_m": np.random.uniform(2, 500)
                })
                
        self.data = records
        return self.data
    
    def calculate_biodiversity_indices(self):
        """Calculate Shannon-Weiner, Simpson's, and Pielou's Evenness indices."""
        if self.data is None:
            raise ValueError("Molecular eDNA data not loaded.")
        
        zone_metrics = {}
        # Group samples by zone
        df = pd.DataFrame(self.data)
        for zone in df['zone'].unique():
            zone_samples = df[df['zone'] == zone]
            
            # Aggregate abundances across all samples in this zone
            total_abundance = {}
            for abundance_dict in zone_samples['species_abundance']:
                for sp, count in abundance_dict.items():
                    total_abundance[sp] = total_abundance.get(sp, 0) + count
                    
            counts = np.array(list(total_abundance.values()), dtype=float)
            total_sum = counts.sum()
            proportions = counts / total_sum
            
            # Richness (S)
            richness = len(counts)
            
            # Shannon Index (H') = -sum(pi * ln(pi))
            shannon = -np.sum(proportions * np.log(proportions)) if richness > 1 else 0.0
            
            # Simpson Index (D) = sum(pi^2) -> Simpson's Index of Diversity = 1 - D
            simpson = 1.0 - np.sum(proportions ** 2) if richness > 1 else 0.0
            
            # Pielou's Evenness (J') = H' / ln(S)
            evenness = shannon / np.log(richness) if richness > 1 else 0.0
            
            # Margalef's Richness Index (d) = (S - 1) / ln(N)
            margalef = (richness - 1) / np.log(total_sum) if total_sum > 1 else 0.0
            
            # Berger-Parker Dominance (d_BP) = N_max / N
            berger_parker = counts.max() / total_sum if total_sum > 0 else 0.0
            
            zone_metrics[zone] = {
                "richness": int(richness),
                "shannon_diversity": float(shannon),
                "simpson_diversity": float(simpson),
                "evenness": float(evenness),
                "margalef_richness": float(margalef),
                "dominance": float(berger_parker),
                "total_sequences": int(total_sum)
            }
            
        return zone_metrics

# ---------------------------------------------------------
# 4. Unified Data Platform (Platform Coordinator)
# ---------------------------------------------------------
class UnifiedDataPlatform:
    """Main coordinator class representing the active data platform state."""
    
    def __init__(self):
        self.ocean_analyzer = OceanographicAnalyzer()
        self.fisheries_analyzer = FisheriesAnalyzer()
        self.molecular_analyzer = MolecularBiodiversityAnalyzer()
        self.last_update = datetime.now()
        self.feed_logs = []
        self._initialize_default_logs()
        
    def _initialize_default_logs(self):
        now = datetime.now()
        self.feed_logs = [
            {"timestamp": (now - timedelta(minutes=5)).strftime("%H:%M:%S"), "message": "Unified Marine Platform initialized successfully", "type": "success"},
            {"timestamp": (now - timedelta(minutes=3)).strftime("%H:%M:%S"), "message": "Connected to 5 global oceanographic monitoring stations", "type": "update"},
            {"timestamp": (now - timedelta(minutes=1)).strftime("%H:%M:%S"), "message": "AI Anomaly Detection and Stock Assessment engines loaded", "type": "success"}
        ]
        
    def initialize_platform(self):
        """Load and compute all core scientific datasets."""
        self.ocean_analyzer.generate_oceanographic_data()
        self.fisheries_analyzer.generate_fisheries_data()
        self.molecular_analyzer.generate_molecular_data()
        self.last_update = datetime.now()
        
    def comprehensive_analysis(self):
        """Compile reports from all three analyzer engines."""
        ocean_df = self.ocean_analyzer.data
        anomalies = ocean_df[ocean_df['anomaly'] == True]
        
        fisheries_assessment = self.fisheries_analyzer.stock_assessment()
        molecular_indices = self.molecular_analyzer.calculate_biodiversity_indices()
        
        return {
            'oceanographic': {
                'total_records': len(ocean_df),
                'anomalies_count': len(anomalies),
                'anomalies_by_station': ocean_df.groupby('station_name')['anomaly'].sum().to_dict()
            },
            'fisheries': fisheries_assessment,
            'molecular': molecular_indices
        }
        
    def ai_insights_generator(self, analysis_results):
        """Generate sophisticated biological and chemical conservation reports."""
        insights = []
        recommendations = []
        
        # Analyze oceanographic anomalies
        anom_count = analysis_results['oceanographic']['anomalies_count']
        if anom_count > 30:
            insights.append("🚨 ECOSYSTEM STRESS ALERT: Widespread anomalies detected across multiple stations. Runoff or warming anomalies indicate regional thermal pressure.")
            recommendations.append("🌐 Deploy supplementary mobile buoyancy probes in warning sectors.")
        else:
            insights.append("✅ CHEMICAL STATUS: Temperature, salinity, and pH conditions remain stable across most monitored oceanic basins.")
            
        # Analyze fisheries
        overfished = [sp for sp, data in analysis_results['fisheries'].items() if data['status'] == "Overfished"]
        sustainable = [sp for sp, data in analysis_results['fisheries'].items() if data['status'] == "Sustainable"]
        
        if overfished:
            insights.append(f"🐟 FISHERIES THREAT: Overfishing indicators triggered for {', '.join(overfished)}. Spawning stock biomass represents a historical low.")
            recommendations.append("🎣 Enforce biological catch moratoriums in replenishment zones.")
        if sustainable:
            insights.append(f"🌿 STOCK REPORT: Sustainable recovery observed in {', '.join(sustainable)} catch biomasses.")
            
        # Analyze biodiversity
        avg_shannon = np.mean([data['shannon_diversity'] for data in analysis_results['molecular'].values()])
        if avg_shannon > 1.8:
            insights.append(f"🧬 GENOMIC RESILIENCE: High molecular biodiversity index (Shannon Mean: {avg_shannon:.2f}) observed. Healthy trophic webs indicated.")
        else:
            insights.append("⚠️ GENOMIC LOSS WARN: Weakened Shannon diversity index. Habitat fragmentation suspected.")
            recommendations.append("🧬 Expand eDNA bio-sentinel monitoring in industrial channels.")
            
        # General Recommendations fallback
        if not recommendations:
            recommendations.extend([
                "🔬 Expand autonomous eDNA sampling intervals.",
                "🎣 Adopt adaptive catch quotas dynamically tied to real-time CPUE indexes."
            ])
            
        # Calculate health score
        health_score = self._calculate_ecosystem_health(analysis_results)
        
        return {
            'insights': insights,
            'recommendations': recommendations,
            'ecosystem_health_score': health_score
        }
        
    def _calculate_ecosystem_health(self, results):
        """Ecological composite index mapping to a 0-100 scale."""
        score = 80.0
        
        # Anomaly penalties
        anom_ratio = results['oceanographic']['anomalies_count'] / results['oceanographic']['total_records']
        score -= min(25.0, anom_ratio * 150.0)
        
        # Fisheries stock status scores
        stocks = results['fisheries']
        overfished_count = len([s for s, d in stocks.items() if d['status'] == 'Overfished'])
        sustainable_count = len([s for s, d in stocks.items() if d['status'] == 'Sustainable'])
        
        score -= overfished_count * 8.0
        score += sustainable_count * 3.0
        
        # Shannon molecular indices
        shannons = [d['shannon_diversity'] for d in results['molecular'].values()]
        mean_shannon = np.mean(shannons) if shannons else 1.5
        score += (mean_shannon - 1.8) * 10.0
        
        return max(0.0, min(100.0, score))
        
    def get_dashboard_data(self):
        """Query state and compile complete JSON dashboard report."""
        results = self.comprehensive_analysis()
        insights_report = self.ai_insights_generator(results)
        
        # Format default trend data (use Pacific Station Alpha as baseline)
        baseline_trend = self.ocean_analyzer.get_station_history("Pacific Station Alpha")
        
        return {
            'metrics': {
                'ecosystem_health_score': round(insights_report['ecosystem_health_score'], 1),
                'species_count': len(results['fisheries']),
                'anomalies_count': results['oceanographic']['anomalies_count'],
                'diversity_index': round(np.mean([d['shannon_diversity'] for d in results['molecular'].values()]), 2)
            },
            'oceanographic': {
                'trend_data': baseline_trend,
                'anomalies_count': results['oceanographic']['anomalies_count']
            },
            'fisheries': {
                'species_data': [
                    {
                        'name': name,
                        'scientific_name': data['scientific_name'],
                        'status': data['status'],
                        'cpue': round(data['cpue'], 1),
                        'trend': round(data['cpue_trend'], 2),
                        'location': data['zone'],
                        'b_ratio': round(data['b_ratio'], 2),
                        'f_ratio': round(data['f_ratio'], 2),
                        'average_catch': round(data['average_catch'], 1),
                        'risk_factors': data['risk_factors']
                    }
                    for name, data in results['fisheries'].items()
                ]
            },
            'molecular': {
                'biodiversity_indices': results['molecular'],
                'genetic_zones': {
                    'zones': list(results['molecular'].keys()),
                    'diversity_values': [round(d['shannon_diversity'], 2) for d in results['molecular'].values()]
                }
            },
            'ai_insights': insights_report['insights'] + insights_report['recommendations'],
            'last_updated': self.last_update.strftime('%Y-%m-%d %H:%M:%S')
        }

    def simulate_real_time_update(self):
        """Simulate real-time diurnal fluctuations and update status reports."""
        self.last_update = datetime.now()
        timestamp_str = self.last_update.strftime("%H:%M:%S")
        
        # Randomly pick a station to update
        station_name = np.random.choice(list(STATIONS.keys()))
        station_mask = self.ocean_analyzer.data['station_name'] == station_name
        station_indices = self.ocean_analyzer.data[station_mask].index
        
        if len(station_indices) > 0:
            latest_idx = station_indices[-1]
            row = self.ocean_analyzer.data.loc[latest_idx].copy()
            
            # Apply slight drift (diurnal cycle simulation)
            temp_drift = np.random.normal(0.0, 0.2)
            new_temp = row['temperature_c'] + temp_drift
            
            # Constrain to realistic boundaries
            self.ocean_analyzer.data.at[latest_idx, 'temperature_c'] = round(new_temp, 2)
            
            # Recheck anomaly status
            features = ['temperature_c', 'salinity_psu', 'ph_level', 'dissolved_oxygen_mg_l', 'chlorophyll_a_mg_m3', 'turbidity_ntu']
            sample = self.ocean_analyzer.data.loc[[latest_idx], features]
            sample_scaled = self.ocean_analyzer.scaler.transform(sample)
            is_anomaly = self.ocean_analyzer.anomaly_detector.predict(sample_scaled)[0] == -1
            
            old_anomaly = row['anomaly']
            self.ocean_analyzer.data.at[latest_idx, 'anomaly'] = is_anomaly
            
            # Add updates logs to feed queue
            if is_anomaly and not old_anomaly:
                self.feed_logs.append({
                    "timestamp": timestamp_str,
                    "message": f"🚨 WARNING: Anomaly detected at {station_name}: Temperature reached {new_temp:.1f}°C!",
                    "type": "alert"
                })
            elif not is_anomaly and old_anomaly:
                self.feed_logs.append({
                    "timestamp": timestamp_str,
                    "message": f"✅ RECOVERY: Readings normalized at {station_name}.",
                    "type": "success"
                })
            else:
                self.feed_logs.append({
                    "timestamp": timestamp_str,
                    "message": f"🔄 Sensor sync: {station_name} temperature updated to {new_temp:.1f}°C",
                    "type": "update"
                })
                
        # Limit feed queue
        if len(self.feed_logs) > 20:
            self.feed_logs = self.feed_logs[-20:]

# ---------------------------------------------------------
# Flask Web Application Setup
# ---------------------------------------------------------
app = Flask(__name__)
# Enable CORS for API access
from flask_cors import CORS
CORS(app)

platform = UnifiedDataPlatform()
platform.initialize_platform()

@app.route('/')
def dashboard():
    """Serve the unified dashboard template."""
    return render_template('dashboard.html')

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Fetch aggregated platform summaries."""
    try:
        data = platform.get_dashboard_data()
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stations')
def get_stations():
    """Retrieve current coordinates and parameters for all stations."""
    try:
        records = []
        for name, info in STATIONS.items():
            station_df = platform.ocean_analyzer.data[platform.ocean_analyzer.data['station_name'] == name]
            latest = station_df.sort_values('timestamp').iloc[-1]
            
            records.append({
                'name': name,
                'latitude': info['lat'],
                'longitude': info['lon'],
                'zone': info['zone'],
                'temperature': round(float(latest['temperature_c']), 2),
                'salinity': round(float(latest['salinity_psu']), 2),
                'ph': round(float(latest['ph_level']), 2),
                'oxygen': round(float(latest['dissolved_oxygen_mg_l']), 2),
                'chlorophyll': round(float(latest['chlorophyll_a_mg_m3']), 2),
                'turbidity': round(float(latest['turbidity_ntu']), 2),
                'anomaly': bool(latest['anomaly']),
                'status': 'Warning' if latest['anomaly'] else ('Maintenance' if name == "Coral Sea Monitor" and np.random.random() < 0.15 else 'Active')
            })
        return jsonify({'status': 'success', 'stations': records})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/station-history/<station_name>')
def get_station_history(station_name):
    """Retrieve timeseries history for ChartJS plots."""
    try:
        history = platform.ocean_analyzer.get_station_history(station_name)
        return jsonify({'status': 'success', 'history': history})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/realtime-feed')
def get_realtime_feed():
    """Fetch live updating activities logs queue."""
    return jsonify({
        'status': 'success',
        'feed': list(reversed(platform.feed_logs))
    })

@app.route('/api/advanced-genomics')
def get_advanced_genomics():
    """Fetch advanced molecular statistics (Ne, Heterozygosity, and Inbreeding)."""
    np.random.seed(int(time.time()) % 1000)
    data = []
    for zone in platform.molecular_analyzer.calculate_biodiversity_indices().keys():
        # Synthesize values dynamically
        ne = int(np.random.uniform(3000, 15000))
        he = float(np.random.uniform(0.65, 0.85))
        fis = float(np.random.uniform(-0.05, 0.15))
        migration = float(np.random.uniform(0.01, 0.05))
        
        data.append({
            'zone': zone,
            'effective_population_size': ne,
            'expected_heterozygosity': round(he, 3),
            'inbreeding_coefficient': round(fis, 3),
            'migration_rate': round(migration, 3)
        })
    return jsonify({'status': 'success', 'genomics': data})

@app.route('/api/update-data')
def update_data():
    """Manual endpoint trigger to test/force sensor variations."""
    try:
        platform.simulate_real_time_update()
        data = platform.get_dashboard_data()
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/export-data')
def export_data():
    """Export complete platform snapshot for download."""
    try:
        data = platform.get_dashboard_data()
        return jsonify({
            'export_timestamp': datetime.now().isoformat(),
            'platform_snapshot': data,
            'metadata': {
                'developer': 'Krishna Gupta',
                'system': 'AI-Driven Unified Data Platform for Marine Biodiversity'
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/species/<species_name>')
def get_species_details(species_name):
    """Fetch analytical profiles for a single fish species."""
    try:
        assessment = platform.fisheries_analyzer.stock_assessment()
        sp_data = assessment.get(species_name)
        if not sp_data:
            return jsonify({'status': 'error', 'message': 'Species not found'}), 404
        return jsonify({'status': 'success', 'data': sp_data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def background_updater():
    """Background simulator thread looping parameter fluctuations."""
    while True:
        time.sleep(10)  # Fluctuate sensor values every 10 seconds
        try:
            platform.simulate_real_time_update()
        except Exception as e:
            print(f"Background thread warning: {e}")

# Decoupled template initialization
def create_dashboard_template():
    """Ensures templates folder exists."""
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        
if __name__ == "__main__":
    create_dashboard_template()
    
    # Avoid spawning background thread in the parent process during debug mode reloads
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        update_thread = threading.Thread(target=background_updater, daemon=True)
        update_thread.start()
        print("[START] Background simulator thread active")
        
    print("[SERVER] Running Marine Biodiversity API Server on port 5000...")
    app.run(debug=True, host='0.0.0.0', port=5000)