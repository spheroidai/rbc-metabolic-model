# RBC Metabolic Model - Streamlit Web Application

## 🌐 Live Application
**URL:** [Coming Soon - Will be deployed on Streamlit Cloud]

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11 or higher
- Git (for deployment)

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements_streamlit.txt
```

2. **Run the application:**
```bash
streamlit run streamlit_app/app.py
```

3. **Open browser:**
The app will automatically open at `http://localhost:8501`

---

## 📁 Project Structure

```
Mario_RBC_up/
├── streamlit_app/           # Web application
│   ├── app.py              # Home page (main entry point)
│   ├── pages/              # Multi-page application
│   │   └── 1_🧪_Simulation.py
│   ├── core/               # Backend modules
│   ├── assets/             # Images, CSS, etc.
│   └── utils/              # Utility functions
│
├── src/                    # CLI application (local simulations)
│   └── main.py            # Command-line interface
│
├── data/                   # Shared data files
├── .streamlit/            # Streamlit configuration
└── requirements_streamlit.txt
```

---

## 🚀 Deployment to Streamlit Cloud

### Step 1: Prepare GitHub Repository

```bash
# Initialize Git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - RBC Metabolic Model Web App"

# Add GitHub remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/rbc-metabolic-model.git

# Push to GitHub
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub account
4. Select repository: `rbc-metabolic-model`
5. Configure:
   - **Main file path:** `streamlit_app/app.py`
   - **Python version:** 3.11
   - **Requirements file:** `requirements_streamlit.txt`
6. Click "Deploy"!

**Your app will be live at:**
`https://YOUR_USERNAME-rbc-metabolic-model.streamlit.app`

---

## 🔧 Configuration

### Streamlit Settings
Edit `.streamlit/config.toml` to customize:
- Theme colors
- Server settings
- Browser behavior

### Secrets (Optional)
For API keys or sensitive data:
1. Create `.streamlit/secrets.toml` (not tracked by Git)
2. Add your secrets:
```toml
[passwords]
admin = "your_password_here"
```

---

## 📊 Features

### Current (Phase 1)
- ✅ Home page with model overview
- ✅ Simulation configuration interface
- ✅ Responsive design
- ✅ Multi-page navigation

### Coming Soon (Phase 2)
- 🔄 Backend simulation engine integration
- 🔄 Interactive result visualization
- 🔄 Data export (CSV, PDF, ZIP)
- 🔄 Bohr effect analysis
- 🔄 pH perturbation studies

---

## 🛠️ Development

### Local Testing
```bash
# Run with auto-reload
streamlit run streamlit_app/app.py --server.runOnSave true

# Run on specific port
streamlit run streamlit_app/app.py --server.port 8502
```

### Adding New Pages
Create new files in `streamlit_app/pages/`:
```python
# Example: streamlit_app/pages/2_📊_Results.py
import streamlit as st

st.title("Results Page")
# Your code here
```

### Debugging
- Check console output for errors
- Use `st.write()` for debugging
- Enable logging in config.toml

---

## 📝 Usage

### Web Application (Streamlit)
1. Navigate to the live URL or run locally
2. Use sidebar to access different pages
3. Configure simulation parameters
4. Run simulations and view results
5. Download outputs

### Command-Line (Local)
For batch processing or scripting:
```bash
# Activate virtual environment
.\activate_venv.ps1

# Run simulation
python src/main.py --curve-fit 1.0
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

---

## 📚 Documentation

- **Full Documentation:** See `Documentation/` folder
- **API Reference:** Coming soon
- **Tutorials:** Included in web app interface

---

## 📄 License

See LICENSE file for details.

---

## 👤 Author

**Jorgelindo da Veiga**

Based on the RBC metabolic model by Bordbar et al. (2015)

---

## 🙏 Acknowledgments

- Bordbar A, et al. (2015) for the original RBC metabolic model
- Streamlit team for the excellent web framework
- All contributors to this project

---

**Questions? Issues?**
- Check Documentation folder
- Open an issue on GitHub
- Contact: [Your email/contact]
