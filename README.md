# Amazon & Flipkart Web Scraper

This project is a **web scraping application** designed to extract key product details—including title, price, rating, and product link—from **Amazon** (with planned support for Flipkart). The system is developed using **Selenium** for automation, **Flask** for backend API integration, and a **frontend** built with HTML, CSS, and JavaScript.

---

## 🚀 **Current Project Status**
- ✅ Implemented a **Selenium-based scraper** for extracting product data.
- ✅ Developed a **Flask API** to connect the scraper with a web interface.
- ✅ Designed and integrated a **frontend (HTML, CSS, JavaScript)** for user interaction.
- ✅ Successfully tested data extraction from Amazon.
- ✅ Implemented **dynamic XPath handling** for more reliable element selection.
- ✅ Enhanced **error handling and performance optimization**.

---

## 📌 **Key Features**
- 🔍 Enables product search on **Amazon**.
- 📊 Extracts and returns **Title, Price, Rating, and Product URL**.
- ⚡ Provides a **frontend interface** for user interaction.
- 🌐 Utilizes a **Flask-based API** to handle backend requests.
- 🔄 Supports **headless browsing** for optimized performance.
- 🛠️ Designed for extensibility to **Flipkart and other e-commerce platforms**.

---

## 🛠 **Installation & Setup Guide**

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/your-repo/web-scraper.git
cd web-scraper
```

### **2️⃣ Install Required Dependencies**
Ensure **Python 3+** and **pip** are installed.

```sh
pip install -r requirements.txt
```
_(If `requirements.txt` is unavailable, refer to the dependencies list below.)_

### **3️⃣ Launch the Backend Server**
```sh
cd backend
python app.py
```
The API will start on: `http://127.0.0.1:5000`

### **4️⃣ Open the Frontend**
Simply open `frontend/index.html` in a browser.

---

## 🛠 **Dependencies**
The project relies on the following technologies:
- **Python 3.x** (Programming Language)
- **Flask** (Web API Framework)
- **Selenium** (Browser Automation for Scraping)
- **WebDriver Manager** (Automates WebDriver Installation)
- **Google Chrome** (Required for Selenium Execution)

### **Manual Dependency Installation**
If `requirements.txt` is unavailable, install dependencies manually:
```sh
pip install flask selenium webdriver-manager
```

---

## 🔥 **Usage Instructions**
1️⃣ Open `frontend/index.html` in a web browser.  
2️⃣ Enter a **product name** in the search field and submit the request.  
3️⃣ The **Flask API** triggers the Selenium-based scraper.  
4️⃣ Extracted product details are **displayed on the webpage**.  

---

## 📌 **Planned Enhancements**
- 🔄 **Extend support to Flipkart**.
- 🚀 **Deploy API to a cloud platform** (e.g., Heroku, Render, AWS).
- ⚡ **Optimize Selenium execution speed**.
- 🛠 **Enable multi-page scraping for more extensive data extraction**.
- 📊 **Implement CSV/JSON export functionality**.
- 🔐 **Improve anti-bot detection handling**.

---

## 💡 **Contributions & Contact**
Contributions are welcome! Feel free to fork the repository, report issues, or submit improvements.

📧 Contact: kdp88532@gmail.com

