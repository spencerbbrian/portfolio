# Market App

This is a Flask-based web application for a market system where users can register, log in, buy, and sell items. The app uses Flask extensions such as `SQLAlchemy`, `Flask-WTF`, `Flask-Login`, and `Flask-Bcrypt` for database management, form handling, user authentication, and password hashing.

---

## Features

- **User Registration and Login**: Users can register with a unique username and email, and log in securely.
- **Market System**: Users can view available items, purchase items within their budget, and sell owned items.
- **Budget Management**: Users have a default budget of $1000 and can manage their funds through buying and selling.
- **Item Management**: Admin functionality to add new items to the market.

---

## Technologies Used

- **Backend**: Flask
- **Database**: SQLite (via Flask-SQLAlchemy)
- **Frontend**: HTML, CSS, Bootstrap (for responsive design)
- **Authentication**: Flask-Login and Flask-Bcrypt
- **Forms**: Flask-WTF with WTForms

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd market
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```

5. **Access the application**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

---

## Folder Structure

- **`market/`**: Contains the core application logic.
  - **`models.py`**: Defines the database models (User and Item).
  - **`routes.py`**: Defines the app's routes and functionality.
  - **`forms.py`**: Contains form classes for registration, login, purchase, and selling.

- **`templates/`**: Contains HTML templates.
  - **`base.html`**: Base template used for all pages.
  - **`home.html`**: Home page template.
  - **`market.html`**: Market page template.
  - **`register.html`**: Registration form template.

- **`static/`**: Contains static files (CSS, JavaScript, images).

---

## Notes

- **Default Budget**: Each user starts with $1000 in their account.
- **Adding Items**: Admins can add new items to the database via the backend.
- **Dependencies**: Ensure all dependencies in `requirements.txt` are installed.

---

## Contributing

Feel free to fork the repository and submit pull requests for new features, bug fixes, or improvements. 

---
