
# Cloud Drive Application

This is a Django-based cloud drive application that allows users to upload, view, preview, and manage files and folders. The application supports file preview for images, videos, audio, PDFs, text files, and Office documents using Google Docs Viewer.

## Project Structure

The project is organized as follows:

- **accounts/**: Contains the Django app for user account management, including authentication, templates, and template tags.
  - `models.py`: Defines user-related models.
  - `forms.py`: Contains forms for user registration and login.
  - `views.py`: Handles user-related views like login, registration, and profile management.
  - `urls.py`: URL configurations for the accounts app.
  - `templates/`: Templates for account-related pages.

- **cloud_drive/**: Contains the main project settings and configuration files.
  - `settings.py`: Django settings file for the project.
  - `urls.py`: Root URL configuration.
  - `wsgi.py` and `asgi.py`: Entry points for WSGI and ASGI servers.

- **drive/**: Contains the Django app that manages file and folder functionalities.
  - `models.py`: Defines models for files and folders.
  - `views.py`: Handles views for uploading, previewing, and managing files and folders.
  - `urls.py`: URL configurations for the drive app.
  - `templates/`: Templates for file and folder management.

- **media/**: Directory where uploaded files are stored.

- **db.sqlite3**: SQLite database for storing application data.

- **manage.py**: Django’s command-line utility for administrative tasks.

- **requirements.txt**: File containing the Python dependencies for the project.

## Installation

To get started with this project, follow these steps:

1. **Clone the repository**:
   ```bash
   cd CLOUD_DRIVE
   ```

2. **Create and activate a virtual environment**:
   ```bash
   pipenv shell
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   Open your web browser and go to `http://127.0.0.1:8000` to access the application.

## Usage

- **File Management**: Users can upload, preview, and manage files and folders. Supported previews include images, videos, audio, PDFs, text files, and Office documents.
- **Account Management**: Users can register, log in, and manage their account settings.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
