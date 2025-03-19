# Fin-Mate: Your Simple Financial Companion

## What it Does

Fin-Mate is a straightforward application designed to help you manage your finances more effectively. It allows you to input financial actions (like expenses or income) and aims to understand and categorize them using smart technology. The goal is to provide you with a clear and simple overview of your financial activities.

## Tools We Use

To build Fin-Mate, we've used the following key tools:

* **Python:** The main programming language that powers the application.
* **Flask:** A lightweight tool for building the web-based interface you interact with.
* **Language Models (LLMs):** Intelligent systems that help us understand and categorize your financial inputs.

## Our Goal

The primary objective of Fin-Mate is to offer a user-friendly way to track and understand your personal finances without requiring deep technical knowledge or complex spreadsheets. We aim to make financial awareness accessible to everyone.

## Getting Started Locally

You can run Fin-Mate on your own computer using either the standard terminal or with Docker. Follow the steps below for your preferred method.

### Method 1: Running from the Terminal (Without Docker)

1.  **Make sure you have Python installed:** Fin-Mate requires Python 3.9.6 or a later version. You can check your Python version by opening your terminal and running:
    ```bash
    python --version
    ```
    If you don't have Python or have an older version, please install Python 3.9.6 or later from the official Python website.

2.  **Create a virtual environment (recommended):** Open your terminal, navigate to the project folder (the one containing the `requirements.txt` file), and run the following commands:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On macOS and Linux
    .venv\Scripts\activate  # On Windows
    ```
    This creates an isolated environment for the project's dependencies.

3.  **Install the necessary tools:** While still in the project folder and with the virtual environment activated, run:
    ```bash
    pip install -r requirements.txt
    ```
    This will download and install all the software libraries that Fin-Mate needs.

4.  **Create the configuration file:** In the root of your project folder, create a new file named `.env` (note the dot at the beginning). Inside this file, add the following lines, replacing the placeholder values with your actual API keys and settings:
    ```
    AKASH_API_BASE_URL=YOUR_LLM_API_BASE_URL_HERE
    AKASH_API_KEY=YOUR_LLM_API_KEY_HERE
    LLM_MODEL_NAME=NAME_OF_THE_LLM_MODEL_TO_USE
    LLM_TEMPERATURE=0.7
    ```
    **Important:** Keep your API keys private and do not share them.

5.  **Run the application:** In your terminal, with the virtual environment still activated and in the project folder, run:
    ```bash
    flask --app app.py run --host=0.0.0.0 --port=8080 --debug
    ```
    This will start the Fin-Mate application. You should see some messages in your terminal indicating that the server has started. You can then access the application through your web browser, usually at `http://localhost:8080`.

### Method 2: Running with Docker

Docker allows you to run Fin-Mate in an isolated container, which simplifies the setup process.

1.  **Install Docker:** If you don't have Docker installed on your computer, please follow the installation instructions for your operating system from the official Docker website.

2.  **Create the configuration file:** In the root of your project folder, create a new file named `.env` (note the dot at the beginning). Inside this file, add the following lines, replacing the placeholder values with your actual API keys and settings:
    ```
    AKASH_API_BASE_URL=YOUR_LLM_API_BASE_URL_HERE
    AKASH_API_KEY=YOUR_LLM_API_KEY_HERE
    LLM_MODEL_NAME=NAME_OF_THE_LLM_MODEL_TO_USE
    LLM_TEMPERATURE=0.7
    ```
    **Important:** Keep your API keys private and do not share them.

3.  **Run the application using Docker Compose:** Open your terminal, navigate to the project folder (the one containing the `docker-compose.yml` file), and run the following command:
    ```bash
    docker-compose up -d --build
    ```
    This command will build the Docker image for Fin-Mate and start the application in the background.

4.  **Access the application:** Once the Docker container is running, you can access the Fin-Mate application through your web browser, usually at `http://localhost:8080`.

**Stopping the Docker application:** To stop the application when running with Docker Compose, navigate to the project folder in your terminal and run:
```bash
docker-compose down