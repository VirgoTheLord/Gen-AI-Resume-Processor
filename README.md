# Gen-AI-Resume-Processor

A Python-based tool designed to extract, standardize, and export resume data using PDF parsing and database handling with ORM techniques. Ideal for developers or HR tech projects that require organizing resume data at scale.

---

## 🚀 Features

- 📄 **PDF Resume Extraction** – Extracts text content from uploaded PDF files.
- 📋 **Template Generation** – Produces a clean, standardized format from resume data.
- 🗃️ **ORM Integration** – Uses an Object-Relational Mapper for managing data storage.
- 📊 **CSV Export** – Outputs resume information into a CSV file for easy analysis.

---

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/VirgoTheLord/Gen-AI-Resume-Processor.git
   cd Gen-AI-Resume-Processor
(Optional) Create and activate a virtual environment:

bash
Copy
Edit
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
🧪 Usage
Extract PDF content:

bash
Copy
Edit
python extractpdf.py
Generate structured resume text:

bash
Copy
Edit
python textgenerationfn.py
Export data to CSV:

bash
Copy
Edit
python export_as_csv.py
📁 Project Structure
graphql
Copy
Edit
Gen-AI-Resume-Processor/
│
├── apps.py               # ORM setup and app initialization
├── extractpdf.py         # PDF text extraction logic
├── textgenerationfn.py   # Resume text formatting and processing
├── export_as_csv.py      # Data export to CSV
├── requirements.txt      # Python package dependencies
🤝 Contributing
Pull requests are welcome! If you have suggestions for improvements or fixes, feel free to fork the repo and submit a PR.

📄 License
This project is licensed under the MIT License. See the LICENSE file for more info.

🙏 Acknowledgements
Thanks to open-source contributors and the Python community for providing the libraries used in this project.

⭐ If you found this project helpful, feel free to star the repo!









