# Smart Attendance System

An AI-powered attendance system featuring **Facial Recognition** (DeepFace/ArcFace) and **Voice Verification** (Liveness Detection).

## 🚀 Features
- **Multi-Factor Authentication**: Combines face and voice biometrics.
- **Liveness Detection**: Prevents spoofing using dynamic challenge phrases and timed interactions.
- **Sapphire Night UI**: A modern, dark-themed responsive interface.
- **Secure**: Password hashing, server-side verification, and session management.

## 🛠️ Prerequisites
- Python 3.12.3
- MySQL Server

## 📦 Installation

1. **Clone/Open the project** in your terminal.

2. **Create and Activate Virtual Environment** (Optional but recommended):
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup**:
   - Open your MySQL client (e.g., HeidiSQL, Workbench).
   - Create a database named `attendance_db`.
   - Import the `attendance_db.sql` file provided in the root directory.
   - **Configure Credentials**: Edit `database.py` and update `user`, `password`, `host` if necessary.

## 🏃‍♂️ How to Run

1. **Start the Application**:
   ```bash
   python app.py
   ```

2. **Access the App**:
   - Open your browser and go to: `https://127.0.0.1:5000`
   - **Note**: You must accept the "Unsafe" warning (usually "Advanced > Proceed to localhost") because a self-signed SSL certificate is used to enable Camera/Microphone access locally.

## 📝 Usage Guide

1. **Register**: creates a new account.
2. **Biometric Setup**:
   - **Face**: Align your face in the camera.
   - **Voice**: Hold the record button and say the **Dynamic Phrase** (e.g., "Red Apple").
3. **Login**: Use your username/password.
4. **Mark Attendance**:
   - Click "Check In Now".
   - Hold the button, say the challenge phrase shown on screen.
   - Release to verify.
5. **View History**: Check your attendance logs and scores.

## ⚠️ Troubleshooting
- **Microphone/Camera Error**: Ensure you are using `HTTPS` and have granted browser permissions.
- **Database Connection**: Verify MySQL is running and credentials in `database.py` are correct.
- **Audio Headers**: If STT fails, ensure the browser supports standard WAV encoding (handled by built-in script).
