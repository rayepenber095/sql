# SQLi Engine

> Security testing only. Use this tool only on systems you own or have explicit written permission to test. Unauthorized use may be illegal and can result in legal consequences.

## How to run this application

### Option 1: Install on Kali Linux (recommended)
1. Open a terminal in the project directory.
2. Run:
   ```bash
   sudo bash install.sh
   ```
3. Start the app:
    ```bash
    sqli-engine
    ```

### Option 2: Run with Docker on Kali Linux
1. Allow the local root user (container default user) to use your X server:
   ```bash
   xhost +SI:localuser:root
   ```
2. Build and run:
   ```bash
   docker compose up --build
   ```
3. When done, stop the container:
   ```bash
   docker compose down
   ```
4. (Optional) Revoke X access:
   ```bash
   xhost -SI:localuser:root
   ```

### Option 3: Run directly from source
1. Open a terminal in the project directory.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python3 main.py
   ```
