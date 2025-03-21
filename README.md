# GitHub Repository Analyzer

This project analyzes GitHub repositories using Azure OpenAI to extract specific information about Azure accelerators and similar solutions.

## Features

- Takes a GitHub URL as input
- Analyzes repository content using Azure OpenAI
- Extracts key information like RBAC support, Azure Gov compatibility, etc.
- Presents findings in a structured table format
- Compares against known solutions (AskSage, NIPRGPT, CamoGPT)

## Setup

1. Clone this repository
2. Install required packages: `pip install -r requirements.txt`
3. Create a `.env` file with your Azure OpenAI credentials:
   ```
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_KEY=your_key
   AZURE_OPENAI_DEPLOYMENT=your_deployment
   ```
4. Launch Jupyter: `jupyter notebook`
5. Open `Accelerator_Info.ipynb`

## Usage

Follow the instructions in the notebook to analyze GitHub repositories and generate insights.
