# Machine Learning Based Intrusion Detection System

This project implements an intelligent Intrusion Detection System (IDS) that analyzes network traffic behaviour using Machine Learning techniques. 
The system classifies traffic as **Normal** or **Attack** and visualizes alerts through a Security Operations Center (SOC) style dashboard.

## Project Overview

Modern networks generate large volumes of traffic, making manual monitoring difficult. Traditional firewalls rely on fixed rules and struggle to detect evolving threats.  
This project demonstrates how Machine Learning can enhance cybersecurity by learning traffic patterns and identifying anomalies automatically.

Instead of monitoring real websites, the system is trained using recorded benchmark datasets because real network traffic is private.


## Objectives

- Detect malicious network behaviour using Machine Learning
- Simulate real-time monitoring through a dashboard
- Classify traffic as normal or intrusion
- Visualize attack alerts and threat levels

## Technologies Used

- Python
- Machine Learning (Random Forest, SVM, KNN)
- Flask (Backend API)
- HTML, CSS, JavaScript (Frontend Dashboard)
- Git & GitHub


## System Architecture

Dataset → Model Training → Flask Backend → SOC Dashboard


- Model trained using network traffic dataset
- Flask API performs predictions
- Dashboard displays monitoring alerts

## Machine Learning Approach

The system was trained using multiple ML algorithms including:

- Random Forest
- Support Vector Machine
- K-Nearest Neighbors

After evaluation, **Random Forest** was selected due to better accuracy and stability in classification.


## Features

- Auto network traffic scanning simulation
- Real-time alert visualization
- Attack type identification
- Threat level meter
- SOC-style monitoring interface


##  Why Not Real Websites?

Real companies like Google or Amazon monitor attacks internally using servers and network sensors.  
External systems cannot access private network traffic, so benchmark datasets are used to simulate intrusion detection behaviour.


## How to Run the Project

1. Clone the repository
2. Install dependencies
3. Run backend:
python app.py
4. Open `index.html` in browser

## Future Improvements

- Real-time packet capture
- Deep Learning based IDS
- Cloud deployment


## Author

Hemasri M
