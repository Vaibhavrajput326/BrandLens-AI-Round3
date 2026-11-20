# BrandLens AI – Brand Intelligence & Governance Platform

**BrandLens AI** is an AI-powered brand intelligence and governance platform designed to help organizations maintain brand consistency, verify content against brand knowledge, and manage content review workflows.

It provides a centralized workspace for analyzing brand-related content, identifying potential inconsistencies, and supporting human review and approval.

## 🚀 Key Features

### 1. Dashboard
- Centralized overview of brand reviews and activities.
- Review statistics and issue monitoring.
- Quick access to important platform modules.

### 2. Content Studio
- Analyze content against registered brand guidelines.
- Identify potential brand consistency issues.
- Generate review findings and suggestions.

### 3. Brand Knowledge Base
- Store brand-related information and reference knowledge.
- Compare submitted content against available brand knowledge.
- Support evidence-based content verification.

### 4. Semantic Content Verification
- Uses Sentence Transformers (`all-MiniLM-L6-v2`).
- Applies TF-IDF and cosine similarity techniques.
- Helps identify semantically relevant content.
- Includes numeric mismatch detection for supported units and values.

### 5. Human Review & Audit Workflow
- Manage review statuses: Pending, Approved, and Rejected.
- Edit and save final content.
- Maintain review history and audit records.

### 6. Analytics & Review History
- Track review activity.
- Monitor detected issues.
- View historical review information.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| Streamlit | User interface |
| SQLite | Database |
| Scikit-learn | TF-IDF and cosine similarity |
| Sentence Transformers | Semantic similarity |
| NumPy | Numerical operations |

## 🏗️ Project Structure

```text
BrandLens_AI/
│
├── app.py
├── app copy.py
├── engine.py
├── database.py
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/Vaibhavrajput326/BrandLens-AI-Round3.git
```

### 2. Navigate to the project directory

```bash
cd BrandLens-AI-Round3
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

**Windows:**
```bash
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
streamlit run app.py
```

The application will open in your browser at:

`http://localhost:8501`

## 🧠 How It Works

1. Brand-related information is stored in the knowledge base.
2. Users submit content through Content Studio.
3. The platform analyzes content using available verification techniques.
4. Potential inconsistencies and findings are presented for review.
5. Human reviewers can approve, reject, or edit the final content.
6. Review activities are maintained in the database for tracking and audit purposes.

## 🎯 Project Objective

The objective of BrandLens AI is to provide a structured and intelligent approach to brand governance by combining semantic content analysis, knowledge-based verification, and human-in-the-loop review workflows.

## 🔮 Future Scope

- Advanced evidence management and source traceability.
- More comprehensive brand guideline validation.
- Improved semantic verification accuracy.
- Advanced analytics and reporting.
- Multi-brand support and collaborative review workflows.

## 👨‍💻 Author

**Vaibhav Rajput**

B.Tech – Computer Science Engineering (AI & ML)

## 📌 Project Information

**Project:** BrandLens AI  
**Repository:** [BrandLens-AI-Round3](https://github.com/Vaibhavrajput326/BrandLens-AI-Round3)

---

*BrandLens AI – Building consistency, trust, and intelligence into brand governance.*
