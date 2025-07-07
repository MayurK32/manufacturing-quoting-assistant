# Quoting Assistant

A modern quoting assistant for manufacturing parts, built to demonstrate LLM-powered feature extraction and both rule-based and ML-driven price prediction.

## 🚀 Project Overview

This project simulates how an AI assistant can help manufacturers generate quick and accurate quotes for CNC parts and similar items.

**Key features:**
- Users enter a part description (or upload a CSV of parts).
- The app uses a language model to extract features (material, size, operations, finish).
- Pricing is calculated using a rule-based system (Phase 1).
- With more data, a custom ML model predicts prices (Phase 2).

## 🛠️ Tech Stack

- Python 3.11+
- OpenAI GPT (for NLP/feature extraction)
- Streamlit (for UI)
- Pandas
- scikit-learn (for ML phase)
- ChromaDB (for similarity search/RAG)

## 💡 How It Works

1. **Phase 1 (MVP):**
   - LLM extracts features from user input.
   - Rule-based logic calculates a quote.

2. **Phase 2 (ML extension):**
   - Train a regression model on part data.
   - Model predicts price from extracted features.

## 📁 Project Structure
quoting-assistant/
│
├── README.md
├── requirements.txt
├── data/
│ └── sample_parts.csv
├── src/
│ └── app.py


