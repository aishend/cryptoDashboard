# Binance Crypto Analysis Dashboard

## 📖 Description

This project is a Streamlit-based web application designed for analyzing cryptocurrency trading pairs from the Binance exchange. It empowers users to filter and sort pairs using technical indicators like the Stochastic oscillator and a normalized MACD Zero Lag across various timeframes. The dashboard provides an interactive interface to explore market conditions and identify potential trading opportunities based on user-defined criteria.

## ✨ Features

*   **Binance Data Integration**: Fetches cryptocurrency pair data directly from Binance.
*   **Multi-Timeframe Analysis**: Supports analysis across common timeframes (e.g., 15m, 1h, 4h, 1d), dynamically adapting to available data.
*   **Stochastic Oscillator Filtering**:
    *   Filter pairs where Stochastic values for *all selected timeframes* are above a user-defined threshold.
    *   Filter pairs where Stochastic values for *all selected timeframes* are below a user-defined threshold.
*   **Normalized MACD Zero Lag**:
    *   Calculates MACD Zero Lag histogram values.
    *   Normalizes these values for each trading pair using its historical minimum and maximum histogram values, then scales them from 0 to 100, centered around the zero-crossing.
    *   Allows users to select a specific timeframe for this MACD calculation and sorting.
*   **Interactive Data Table**: Displays filtered and sorted trading pairs, including relevant Stochastic columns and the normalized MACD Zero Lag value.
*   **Dynamic Sorting**: Sorts trading pairs based on the ascending order of the normalized MACD Zero Lag.
*   **Clear Statistics**: Shows the total number of pairs analyzed, how many pairs meet the filter criteria, and how many were excluded.
*   **Error Reporting**: Lists any symbols for which data fetching or processing failed.

## ⚙️ How It Works

The application operates in several stages:

1.  **Data Loading**: It starts by loading a pre-processed DataFrame (`df_valid`) containing market data, including Close prices and pre-calculated indicator components for various timeframes.
2.  **Timeframe Availability**: The dashboard dynamically determines available timeframes for Stochastic and MACD analysis based on the columns present in the loaded data.
3.  **User Input**: Through the Streamlit sidebar, users can:
    *   Select multiple timeframes for applying Stochastic filters.
    *   Enable and configure "All Above" or "All Below" Stochastic filters with specific threshold values.
    *   Choose a single timeframe for calculating and sorting by the normalized MACD Zero Lag.
4.  **Filtering**:
    *   If Stochastic filters are enabled, the application iterates through the selected Stochastic columns for the chosen timeframes and filters the DataFrame to include only pairs that meet the specified conditions (e.g., all selected Stochastics >= 70).
5.  **MACD Normalization & Sorting**:
    *   For the selected MACD timeframe, the MACD Zero Lag histogram value is normalized. This normalization uses the historical minimum and maximum values of the histogram *for each specific trading pair*, ensuring a pair-relative scaling.
    *   The normalized value is then adjusted so that the original zero-crossing point of the MACD histogram is mapped to 50 on a 0-100 scale.
    *   The DataFrame (either filtered or the original `df_valid`) is then sorted in ascending order based on this normalized MACD value.
6.  **Display**:
    *   The resulting DataFrame, showing "Symbol", relevant Stochastic columns, and the calculated `MACD0lag_norm_<tf>` column, is displayed.
    *   If filters result in an empty set, a warning is shown, and the unfiltered (but sorted) data may be displayed instead.
    *   Statistics and any data loading errors are also presented.

## 🛠️ Technologies Used

*   **Python 3.x**
*   **Streamlit**: For building the interactive web application.
*   **Pandas**: For data manipulation and analysis.
*   **Binance API**: For fetching cryptocurrency data (likely via a client library such as `python-binance`).

## 🚀 Setup and Installation

1.  **Prerequisites**:
    *   Python 3.7 or higher.
    *   `pip` (Python package installer).

2.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

3.  **Create and Activate a Virtual Environment** (Recommended):
    *   On Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        python -m venv venv
        source venv/bin/activate
        ```

4.  **Install Dependencies**:
    Create a `requirements.txt` file in the root of your project with the following content (add any other specific libraries you use, e.g., `python-binance`):
    ```txt
    streamlit
    pandas
    # python-binance  # Uncomment or add if you use this library
    ```
    Then, install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configuration (Binance API Keys)**:
    This application requires Binance API keys to fetch market data.

    *   The API keys are expected to be in a file named `config.py` within a `binance_client` directory (i.e., `binance_client/config.py`).
    *   Create this file with your actual Binance API key and secret:
        ```python
        # binance_client/config.py
        KEY    = "YOUR_BINANCE_API_KEY"
        SECRET = "YOUR_BINANCE_API_SECRET"
        ```

    *   **🔒 IMPORTANT SECURITY NOTICE**:
        *   **NEVER commit your actual API keys to any Git repository, especially public ones.**
        *   Ensure that the `binance_client/config.py` file is listed in your project's `.gitignore` file to prevent accidental commits. Add the following line to your `.gitignore`:
            ```
            # Ignore Binance API configuration
            binance_client/config.py
            ```
        *   For production or shared environments, consider using environment variables or a dedicated secrets management service to handle API keys securely.

## ▶️ Usage

1.  Ensure you have completed the setup and installation steps, including configuring your API keys.
2.  Navigate to the root directory of the project in your terminal.
3.  Run the Streamlit application:
    ```bash
    streamlit run dashboard.py
    ```
4.  Streamlit will typically open the application automatically in your default web browser. If not, open your browser and go to the local URL provided in the terminal (usually `http://localhost:8501`).
5.  Interact with the dashboard using the sidebar controls:
    *   **Select Timeframes**: Choose the timeframes (e.g., "1h", "4h") for which you want to apply Stochastic filters.
    *   **Stochastic Filters**:
        *   Enable "Ativar filtro 'Todos acima'" and use the slider to set a minimum Stochastic value.
        *   Enable "Ativar filtro 'Todos abaixo'" and use the slider to set a maximum Stochastic value.
    *   **MACD Sorting Timeframe**: Select the timeframe for the MACD Zero Lag normalization and subsequent sorting.
6.  The main area of the dashboard will display the filtered and sorted trading pairs based on your selections.

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.
