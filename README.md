# AI IT Support Ticket Generator

## Overview
An interactive web application that generates realistic IT support tickets and helps users practice their troubleshooting skills using AI-powered feedback. The application provides hints and evaluates proposed solutions to help users improve their IT support abilities.

## share.streamlit.io
try here:  https://itticketgen.streamlit.app/

## Features
- **Dynamic Ticket Generation**: Creates IT support tickets at three difficulty levels (simple, medium, complex)
- **AI-Powered Feedback**: Provides helpful hints and validates if solutions would fix the issue
- **Interactive Learning**: Two-step learning process with hints and solution evaluation
- **Google Gemini Integration**: Uses Google's AI models for ticket generation and feedback
- **Difficulty Levels**: 
  - 🟢 **Simple**: Basic IT issues for beginners
  - 🟡 **Medium**: Standard IT problems for intermediate users
  - 🔴 **Complex**: Advanced technical challenges for experts

## How It Works
1. **Generate Ticket**: Create a realistic IT support ticket based on selected difficulty
2. **Propose Solution**: Write how you would solve the issue
3. **Get Hints**: Receive AI-powered guidance to improve your solution
4. **Check Solution**: Validate if your solution would actually fix the problem
5. **Learn & Improve**: Revise your approach based on feedback



## Setup Instructions

### Prerequisites
- Python 3.8+
- Google AI Studio API key (free tier available)
- Internet connection

### Installation
1. Clone or download the application files
2. Install required packages:
```bash
pip install streamlit google-generativeai
```

3. Configure your API key:
   - Open the application file (`app.py`)
   - Find line with: `GOOGLE_API_KEY = "apikey"`
   - Replace `"apikey"` with your actual Google AI Studio API key
   - Or enter it directly in the application sidebar

4. Run the application:
```bash
streamlit run app.py
```

### Getting an API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Get API key"
4. Create a new API key
5. Copy and paste it into the application



## Usage Guide

### 1. Initial Setup
- Launch the application
- Enter your Google AI API key in the sidebar
- Click "Load Available Models" to see available AI models
- Select your preferred model

### 2. Select Difficulty
- Choose from three difficulty levels:
  - **Simple**: Basic troubleshooting practice
  - **Medium**: Standard IT problem-solving
  - **Complex**: Advanced technical challenges

### 3. Generate and Practice
- Click "Generate Practice Ticket" to create a new IT issue
- Read the ticket description carefully
- Type your solution in the text area
- Use the buttons to:
  - Get hints for improvement
  - Check if your solution would work
  - Generate a new ticket

### 4. Learning Cycle
- Try solving the issue on your own first
- Use hints when you need guidance
- Check your solution's effectiveness
- Revise and improve based on feedback
- Generate new tickets to practice different scenarios

## Evaluation System
Solutions are evaluated as:
- **✅ YES**: Solution would likely fix the issue
- **⚠️ PARTIALLY**: Solution might help but needs improvements
- **❌ NO**: Solution would not fix the issue

## Hint System
- **Simple Level**: Gentle guidance and general suggestions
- **Medium Level**: Targeted improvements and specific advice
- **Complex Level**: Expert insights and strategic thinking prompts



## Troubleshooting

### Common Issues
1. **API Key Errors**: Ensure you have a valid Google AI Studio API key
2. **Model Not Found**: Click "Load Available Models" to refresh available options
3. **Connection Issues**: Check your internet connection
4. **External URL Not Working**: Use `http://localhost:8501` instead

### Quick Fixes
- Restart the application if models fail to load
- Verify API key is correctly entered
- Ensure you have the latest packages installed
- Check Google AI Studio dashboard for usage limits

## Learning Objectives
- Develop systematic troubleshooting methodology
- Improve technical documentation skills
- Practice clear communication with users
- Learn common IT issue patterns and solutions
- Enhance problem-solving approaches

## Technical Details
- **Framework**: Streamlit
- **AI Provider**: Google Gemini API
- **Backend**: Python 3.8+
- **Dependencies**: 
  - streamlit
  - google-generativeai
  - json, re, datetime (standard libraries)

## Tips for Effective Learning
1. **Be Specific**: Write detailed, step-by-step solutions
2. **Think Systematically**: Start with basic troubleshooting before complex solutions
3. **Use the Hints**: Get guidance when stuck, but try to solve first
4. **Learn from Feedback**: Understand why solutions work or don't work
5. **Practice Regularly**: Generate multiple tickets to cover different scenarios

## Support
For issues or questions:
1. Check the troubleshooting section above
2. Verify your API key and internet connection
3. Ensure you're using supported models
4. Review Google AI Studio documentation for API limits

## License
Free for educational and personal use. Google AI API usage subject to Google's terms and conditions.
