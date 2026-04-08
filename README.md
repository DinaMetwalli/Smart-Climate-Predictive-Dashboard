# Smart Climate Predictive Dashboard
Code repository for Final Year Project :]

## Dashboard Features
* Running a live analysis to predict future temperature anomalies up to 5 years into the future for 6 continents using NOAA's & OWID's* APIs
* Registering & modifying an account to run custom analysis and view and edit custom analysis history.
* Running a custom analysis by uploading your own temporal datasets for the desired continents from the custom uploads page.
* Viewing live and custom analysis charts and performance metrics.
* Selecting different time horizons from the produced results to see future changes (e.g. predicted continental temperature anomalies for march 2031).

## Running The Application
To use the dashboard, please follow the steps below.

### 1. Prerequisites
* Make sure you have Python version 3.12.0 & Git installed on your machine.
* Clone the repository to your local machine by opening command prompt and running the following in the desired folder/directory.
```
git clone https://github.com/DinaMetwalli/Smart-Climate-Predictive-Dashboard.git
```

### 2. Install requirements
Go into the code directory and run the following commands to install all the needed requirements.

Go to the correct directory
```
cd Smart-Climate-Predictive-Dashboard
```

Create a virtual machine
```
py -m venv .\venv
```

Activate Virtual Machine
```
.\venv\Scripts\activate
```

Install requirements
```
pip install -r requirements.txt
```
### 3. Starting the application
To start the application, simply run the following command. Please wait for the command to finish loading fully before you use the dashboard.
```
py start.py
```

### 4. Using the Dashboard (& Supported Browsers)
You can use the dashboard by opening your desired web browser and navigating to `localhost:5000`. The dashboard is fully supported on the following browsers:
* Opera
* Google Chrome
* Microsoft Edge

## Running Unit Tests
If you would like to see unit tests running, simply run the following command from the terminal and observe the output.
```
python -W ignore -m pytest -v
```