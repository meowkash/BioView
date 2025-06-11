# Contributing

## Project Structure

```bash
bioview/
├── app.py              # Main application
├── biopac/             # BIOPAC integration
├── common/             # Common functionality
├── constants/          # App-specific constants
├── types/              # Custom data-types 
├── ui/                 # GUI components
├── usrp/               # USRP core functionality
└── utils/              # Utility functions
```

## Instructions

Contributing changes requires you to have ```git``` installed in your system to be able to install the editable version of the app. In a terminal window, follow the steps listed below. *On Windows, use Git Bash for this. On Linux and macOS, use the native terminal app.*

```bash
# Clone repository 
cd ~ 
git clone https://github.com/meowkash/bioview.git 

# Run installer script
cd bioview
chmod +x install.sh
./install.sh 
```
