# Linguaspark

Linguaspark is a Streamlit web app that lets students practice German conversations and exam scenarios with an AI partner called **Sir Felix**. Prompts and replies come from OpenAI's API and adapt to the selected level (A1–C1).

## Setup

1. Install the requirements:

```bash
pip install -r requirements.txt
```

2. Add your OpenAI API key using Streamlit secrets. Create a file at `.streamlit/secrets.toml` containing:

```toml
[general]
OPENAI_API_KEY = "your-openai-key"
```

(You can also set `OPENAI_API_KEY` as an environment variable.)

3. Launch the app with:

```bash
streamlit run lingua.py
```

## Student Codes

`student_codes.csv` stores one code per learner. On startup the app asks for a code and only those present in this file are accepted. To add another student, append their code to the list.

## Usage

1. Run the app and enter your student code.
2. Choose your level and preferred mode (exam simulation, custom chat or presentation practice).
3. Follow the prompts from Sir Felix and reply in German. Corrections and tips appear in English.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
