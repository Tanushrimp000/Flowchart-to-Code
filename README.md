# Flowchart-to-Code: Intelligent Code Generation System

## 📌 Project Overview
Flowchart-to-Code is an intelligent application that converts flowcharts into executable source code using Optical Character Recognition (OCR), flowchart logic interpretation, and automated code generation. It helps bridge the gap between visual algorithms and programming by translating flowchart structures into code across multiple programming languages.

## 🎯 Key Features
- **Flowchart Recognition:** Extracts text and logic from flowchart images using OCR.
- **Multi-Language Code Generation:** Generates code in Python, C, C++, Java, JavaScript, Go, and Rust.
- **Logic Interpretation:** Processes common flowchart constructs, including sequential operations and conditional IF–ELSE statements.
- **Complexity Analysis:** Estimates time and space complexity using Big-O notation.
- **Test Case Generation:** Supports normal, zero, and negative input scenarios for supported expressions.
- **Expected Output Evaluation:** Provides expected outputs for supported simple expressions.
- **Interactive Interface:** Offers a Streamlit-based interface for interacting with the system.
- **Deterministic Processing:** Uses rule-based logic for predictable code generation, with optional LLM integration where configured.

## 🛠️ Technology Stack
- **Programming Language:** Python
- **User Interface:** Streamlit
- **OCR:** Tesseract OCR
- **Code Generation:** Rule-based generation engine
- **Supported Languages:** Python, C, C++, Java, JavaScript, Go, Rust
- **AI Integration:** Optional Gemini/OpenAI integration, depending on configuration
- **Testing:** Python testing framework

## ⚙️ How It Works
1. Upload a flowchart image through the application.
2. Extract text from the image using OCR.
3. Interpret the extracted content and supported flowchart logic.
4. Generate source code in the selected programming language.
5. Analyze the algorithm's estimated time and space complexity.
6. Generate supported test cases and expected outputs for validation.

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or later
- Git
- Tesseract OCR installed and configured in your system PATH
- Required Python dependencies

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/Flowchart-to-Code.git
cd Flowchart-to-Code
```

Create and activate a virtual environment:

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If your repository does not contain a `requirements.txt`, install the dependencies listed in your project configuration instead.

### Run the Application

For a Streamlit application, run:

```bash
streamlit run app.py
```

Replace `app.py` with the actual Streamlit entry-point filename if it differs in your project.

## 🧪 Testing
Run the project's available automated tests using:

```bash
python -m pytest
```

Ensure that the required dependencies are installed and that the tests are compatible with your current project configuration.

## 💡 Use Cases
- Learning programming logic through visual algorithms.
- Converting flowchart-based problem statements into source code.
- Understanding conditional logic and algorithm complexity.
- Generating test cases for basic algorithm validation.
- Supporting programming education and algorithm prototyping.

## 🔮 Future Enhancements
- Improved recognition of complex and handwritten flowcharts.
- Support for loops, nested conditions, and additional flowchart symbols.
- More robust syntax and semantic validation.
- Execution-based testing across supported programming languages.
- Enhanced complexity analysis for more complex algorithms.
- Improved error handling and visual debugging.

## 👩‍💻 Project Goal
The goal of Flowchart-to-Code is to simplify algorithm implementation by transforming visual logic into readable, multi-language source code while providing complexity insights and basic validation support.

---

