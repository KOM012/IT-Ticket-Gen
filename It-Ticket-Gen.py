import streamlit as st
import json
import re
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI IT Support Ticket Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🤖 AI IT Support Ticket Generator")
st.markdown("Generate IT tickets and get helpful hints for your solutions")

# Get API key from Streamlit Secrets
try:
    OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "") or st.secrets.get("API_KEY", "")
    
    if not OPENROUTER_API_KEY:
        # Use the specific key you provided
        OPENROUTER_API_KEY = "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"
    
    if not OPENROUTER_API_KEY:
        st.error("""
        ⚠️ **API Key Not Configured**
        
        Please configure your OpenRouter API key:
        
        **For Streamlit Cloud:**
        - Go to app settings → Secrets
        - Add: `OPENROUTER_API_KEY = "your-api-key-here"`
        
        **For local development:**
        - Create `.streamlit/secrets.toml`
        - Add: `OPENROUTER_API_KEY = "your-api-key-here"`
        
        Get a free API key from: https://openrouter.ai/settings/keys
        """)
        st.stop()
        
except Exception as e:
    st.error(f"Error loading API key: {str(e)[:100]}")
    st.stop()

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://it-ticket-generator.streamlit.app",
    "X-Title": "IT Ticket Generator",
    "Content-Type": "application/json"
}

# Available models on OpenRouter
AVAILABLE_MODELS = [
    "google/gemini-pro",
    "google/gemini-pro-vision",
    "google/gemini-flash-1.5",
    "google/gemini-pro-1.5",
    "openai/gpt-3.5-turbo",
    "openai/gpt-4",
    "openai/gpt-4-turbo",
    "anthropic/claude-3-haiku",
    "anthropic/claude-3-sonnet",
    "meta-llama/llama-3-70b-instruct",
    "mistralai/mistral-7b-instruct",
]

# Initialize session state
if 'ticket' not in st.session_state:
    st.session_state.ticket = None
if 'validation' not in st.session_state:
    st.session_state.validation = None
if 'agent_response' not in st.session_state:
    st.session_state.agent_response = ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "google/gemini-flash-1.5"  # Default model
if 'solution_effective' not in st.session_state:
    st.session_state.solution_effective = None

def call_openrouter_api(model, messages, max_tokens=300, temperature=0.7):
    """Make API call to OpenRouter."""
    try:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        response = requests.post(
            OPENROUTER_API_URL,
            headers=OPENROUTER_HEADERS,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"], None
        else:
            error_msg = response.text
            if response.status_code == 401:
                return None, "Invalid API key. Please check your OpenRouter API key."
            elif response.status_code == 429:
                return None, "Rate limit exceeded. Please try again later."
            elif response.status_code == 403:
                return None, "API key doesn't have permission for this model."
            else:
                return None, f"API Error {response.status_code}: {error_msg[:100]}"
                
    except requests.exceptions.Timeout:
        return None, "Request timeout. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check your internet connection."
    except Exception as e:
        return None, f"Error: {str(e)[:100]}"

def parse_json_from_text(text):
    """Extract and parse JSON from text."""
    try:
        # Clean the text - remove markdown code blocks
        cleaned_text = text.strip()
        cleaned_text = cleaned_text.replace('```json', '').replace('```', '').strip()
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        # If no complete JSON found, try to build it manually
        ticket_data = {
            "user": "IT User",
            "issue": "Technical issue requiring assistance",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Try to extract user
        user_match = re.search(r'"user":\s*"([^"]+)"', cleaned_text)
        if user_match:
            ticket_data["user"] = user_match.group(1)
        
        # Try to extract issue
        issue_match = re.search(r'"issue":\s*"([^"]+)"', cleaned_text)
        if issue_match:
            ticket_data["issue"] = issue_match.group(1)
        
        return ticket_data
        
    except Exception as e:
        st.error(f"JSON parsing error: {str(e)[:100]}")
        return None

def get_hint_prompt(ticket_issue, proposed_solution, difficulty_level):
    """Create a hint prompt based on difficulty level."""
    
    if difficulty_level == "simple":
        return f"""
You are a helpful IT mentor. The user has proposed this solution:

**Issue:** {ticket_issue}

**User's Solution:** {proposed_solution}

Provide 2-3 gentle hints that would help improve their solution WITHOUT giving away the full answer.

Format your response as helpful hints, not a full evaluation.

Example format:
💡 **Helpful Hints:**
- Consider checking [general area]
- You might want to look at [common troubleshooting step]
- A good next step would be [suggestion]

Keep it encouraging and focused on guiding thinking.
"""
    
    elif difficulty_level == "medium":
        return f"""
You are an IT trainer. The user has proposed this solution:

**Issue:** {ticket_issue}

**User's Solution:** {proposed_solution}

Provide targeted guidance that helps them improve their approach. Focus on:
- One specific area that needs more detail
- One common oversight in this type of problem
- One technical concept to consider

Format your response as constructive guidance.

Example format:
🎯 **Targeted Guidance:**
• **Add more detail to:** [specific area]
• **Don't forget to check:** [common oversight]  
• **Consider this concept:** [technical concept]

Be specific but don't solve it for them.
"""
    
    else:  # complex
        return f"""
You are a senior IT expert. The user has proposed this solution:

**Issue:** {ticket_issue}

**User's Solution:** {proposed_solution}

Provide expert insights that challenge their thinking. Focus on:
- Strategic approach considerations
- Deeper investigation paths
- Alternative methodologies

Format your response as expert-level insights.

Example format:
🧠 **Expert Insights:**
• **Strategic consideration:** [high-level approach]
• **Investigate further:** [deeper analysis area]
• **Alternative method:** [different approach]

Challenge assumptions without giving direct answers.
"""

def get_validation_prompt(ticket_issue, proposed_solution):
    """Create a validation prompt to check if solution would work."""
    return f"""
Based on this IT issue and proposed solution, evaluate if the solution would effectively fix the issue.

**Issue:** {ticket_issue}

**Proposed Solution:** {proposed_solution}

Evaluate the solution and answer with one of these exact phrases:
- "✅ YES - This solution would likely fix the issue."
- "⚠️ PARTIALLY - This solution might help but needs improvements."
- "❌ NO - This solution would not fix the issue."

After your answer, provide ONE brief reason (max 1 sentence) explaining your evaluation.

Example responses:
✅ YES - This solution would likely fix the issue. It addresses the root cause effectively.
⚠️ PARTIALLY - This solution might help but needs improvements. It misses a key troubleshooting step.
❌ NO - This solution would not fix the issue. It doesn't address the actual problem.

IMPORTANT: Start your response with exactly one of the three options above.
"""

def get_ticket_prompt(difficulty_level):
    """Generate appropriate ticket based on difficulty."""
    if difficulty_level == "simple":
        return """
Create a simple, common IT support ticket. Provide ONLY a valid JSON object with these exact fields:
- "user": Name and department
- "issue": Clear description of a basic IT problem

Make the issue simple and common. Good for beginners.

Example format:
{
  "user": "Sarah from Marketing",
  "issue": "Computer won't turn on. No lights or sounds when power button is pressed."
}

Return ONLY the JSON object, no other text.
"""
    
    elif difficulty_level == "medium":
        return """
Create a medium-difficulty IT support ticket. Provide ONLY a valid JSON object with these exact fields:
- "user": Name and department
- "issue": IT problem requiring some technical knowledge

Make the issue realistic with some technical details. Good for intermediate users.

Example format:
{
  "user": "Alex from Engineering",
  "issue": "Outlook emails are going to Junk folder instead of Inbox. This happens with emails from specific domains only."
}

Return ONLY the JSON object, no other text.
"""
    
    else:  # complex
        return """
Create a complex IT support ticket. Provide ONLY a valid JSON object with these exact fields:
- "user": Name and department
- "issue": Challenging IT problem requiring investigation

Make the issue complex with technical details and specific scenarios. Good for advanced users.

Example format:
{
  "user": "Network Admin from IT Department",
  "issue": "Intermittent packet loss between main office and cloud servers. Issue occurs randomly between 2-4 PM daily."
}

Return ONLY the JSON object, no other text.
"""

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.success("✅ OpenRouter API Configured")
    st.caption(f"Using key: {OPENROUTER_API_KEY[:10]}...")
    
    # Model selection
    st.markdown(f"### 🤖 Available Models")
    
    selected = st.selectbox(
        "Select AI Model",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state.selected_model) 
        if st.session_state.selected_model in AVAILABLE_MODELS else 0,
        key="model_selector"
    )
    st.session_state.selected_model = selected
    
    with st.expander("ℹ️ Model Details"):
        st.markdown(f"**Selected:** `{selected}`")
        if "gemini" in selected.lower():
            st.caption("🤖 Google Gemini model")
        elif "gpt" in selected.lower():
            st.caption("⚡ OpenAI GPT model")
        elif "claude" in selected.lower():
            st.caption("🧠 Anthropic Claude model")
        elif "llama" in selected.lower():
            st.caption("🦙 Meta Llama model")
        elif "mistral" in selected.lower():
            st.caption("🌪️ Mistral AI model")
    
    # Difficulty slider
    st.markdown("---")
    st.markdown("### 🎯 Difficulty Level")
    
    difficulty = st.select_slider(
        "Choose challenge level",
        options=["simple", "medium", "complex"],
        value="medium",
        help="Simple: Easy common issues | Medium: Standard IT problems | Complex: Advanced technical challenges"
    )
    
    # Show difficulty descriptions
    if difficulty == "simple":
        st.caption("🟢 **Simple:** Basic issues, great for beginners")
    elif difficulty == "medium":
        st.caption("🟡 **Medium:** Standard IT problems, good practice")
    else:
        st.caption("🔴 **Complex:** Advanced challenges, test your expertise")

    st.markdown("---")
    if st.button("🔄 Refresh App", use_container_width=True):
        st.rerun()

# Main centered content area
st.markdown("<br>", unsafe_allow_html=True)

# Create a centered container
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    # Main container
    with st.container():
        # Check if ready
        can_generate = st.session_state.selected_model is not None
        
        # Header section
        if not st.session_state.ticket:
            st.markdown("### 🎯 Ready to Practice")
            if can_generate:
                st.markdown(f"Current difficulty: **{difficulty.upper()}**")
                st.markdown("Click 'Generate Practice Ticket' to start.")
            else:
                st.warning("Please select a model in the sidebar.")
        
        # Generate button
        if not st.session_state.ticket:
            if st.button("✨ Generate Practice Ticket", 
                         type="primary", 
                         use_container_width=True,
                         disabled=not can_generate):
                
                with st.spinner(f"Creating {difficulty} ticket..."):
                    try:
                        prompt = get_ticket_prompt(difficulty)
                        
                        messages = [
                            {
                                "role": "system",
                                "content": "You are an IT support ticket generator. Always return valid JSON."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ]
                        
                        response_text, error = call_openrouter_api(
                            st.session_state.selected_model,
                            messages,
                            max_tokens=300,
                            temperature=0.3
                        )
                        
                        if error:
                            st.error(f"API Error: {error}")
                        elif response_text:
                            ticket_json = parse_json_from_text(response_text)
                            
                            if not ticket_json:
                                st.error("Failed to generate ticket. The AI response was not valid JSON. Please try again.")
                            else:
                                ticket_json["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                ticket_json["model"] = st.session_state.selected_model
                                ticket_json["difficulty"] = difficulty
                                st.session_state.ticket = ticket_json
                                
                                st.session_state.agent_response = ""
                                st.session_state.validation = None
                                st.session_state.solution_effective = None
                                
                                st.rerun()
                        else:
                            st.error("No response from AI. Please try again.")
                            
                    except Exception as e:
                        st.error(f"Error generating ticket: {str(e)[:100]}")
        
        # Show ticket if exists
        if st.session_state.ticket:
            ticket = st.session_state.ticket
            
            # Difficulty badge
            difficulty_badge = ticket.get("difficulty", "medium")
            badge_color = {
                "simple": "🟢",
                "medium": "🟡", 
                "complex": "🔴"
            }.get(difficulty_badge, "⚪")
            
            # Ticket display section
            st.markdown(f"### 📋 Practice Ticket {badge_color}")
            st.caption(f"**Level:** {difficulty_badge.upper()}")
            
            with st.container():
                st.markdown(f"**👤 From:** {ticket.get('user', 'User')}")
                st.markdown(f"**🕒 Submitted:** {ticket.get('timestamp', 'Just now')}")
                
                st.markdown("---")
                st.markdown("**📝 Issue Description:**")
                st.info(ticket.get('issue', 'No description available'))
            
            # Response section
            st.markdown("---")
            st.markdown("### 💭 Your Proposed Solution")
            
            placeholders = {
                "simple": "Example: First, I would check if the computer is plugged in...",
                "medium": "Example: Start by checking network settings, then verify firewall rules...",
                "complex": "Example: Begin with packet capture analysis, check QoS settings, review network topology..."
            }
            
            response = st.text_area(
                "How would you solve this?",
                height=150,
                placeholder=placeholders.get(difficulty_badge, "Describe your solution approach..."),
                value=st.session_state.agent_response,
                key="response_area",
                help=f"Think through the {difficulty_badge} level problem and propose your solution steps."
            )
            
            if response != st.session_state.agent_response:
                st.session_state.agent_response = response
            
            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                hint_text = {
                    "simple": "💡 Get Hints",
                    "medium": "🎯 Get Guidance", 
                    "complex": "🧠 Get Insights"
                }.get(difficulty_badge, "💡 Get Hints")
                
                if st.button(hint_text,
                            use_container_width=True,
                            disabled=not response.strip()):
                    if response.strip():
                        with st.spinner(f"Generating {difficulty_badge} hints..."):
                            try:
                                hint_prompt = get_hint_prompt(
                                    ticket.get('issue', ''),
                                    response,
                                    difficulty_badge
                                )
                                
                                messages = [
                                    {
                                        "role": "system",
                                        "content": "You are an IT mentor providing helpful hints."
                                    },
                                    {
                                        "role": "user", 
                                        "content": hint_prompt
                                    }
                                ]
                                
                                response_text, error = call_openrouter_api(
                                    st.session_state.selected_model,
                                    messages,
                                    max_tokens=400,
                                    temperature=0.2
                                )
                                
                                if error:
                                    st.error(f"API Error: {error}")
                                elif response_text:
                                    st.session_state.validation = response_text
                                    st.rerun()
                                else:
                                    st.error("No response from AI. Please try again.")
                                
                            except Exception as e:
                                st.error(f"Failed to generate hints: {str(e)[:100]}")
            
            with col_btn2:
                if st.button("✅ Check Solution", 
                            use_container_width=True,
                            disabled=not response.strip()):
                    if response.strip():
                        with st.spinner("Evaluating solution..."):
                            try:
                                validation_prompt = get_validation_prompt(
                                    ticket.get('issue', ''),
                                    response
                                )
                                
                                messages = [
                                    {
                                        "role": "system",
                                        "content": "You are an IT solution evaluator."
                                    },
                                    {
                                        "role": "user", 
                                        "content": validation_prompt
                                    }
                                ]
                                
                                response_text, error = call_openrouter_api(
                                    st.session_state.selected_model,
                                    messages,
                                    max_tokens=200,
                                    temperature=0.1
                                )
                                
                                if error:
                                    st.error(f"API Error: {error}")
                                elif response_text:
                                    st.session_state.solution_effective = response_text
                                    st.rerun()
                                else:
                                    st.error("No response from AI. Please try again.")
                                
                            except Exception as e:
                                st.error(f"Failed to evaluate solution: {str(e)[:100]}")
            
            with col_btn3:
                if st.button("🔄 New Ticket", 
                            use_container_width=True):
                    st.session_state.ticket = None
                    st.session_state.validation = None
                    st.session_state.solution_effective = None
                    st.session_state.agent_response = ""
                    st.rerun()
            
            # Show validation result
            if st.session_state.solution_effective:
                st.markdown("---")
                st.markdown("### 📊 Solution Evaluation")
                
                result_text = st.session_state.solution_effective
                
                if result_text.startswith("✅ YES"):
                    st.success(result_text)
                elif result_text.startswith("⚠️ PARTIALLY"):
                    st.warning(result_text)
                elif result_text.startswith("❌ NO"):
                    st.error(result_text)
                else:
                    st.info(result_text)
                
                if result_text.startswith("⚠️ PARTIALLY") or result_text.startswith("❌ NO"):
                    st.markdown("**💡 Try getting hints to improve your solution!**")
            
            # Show hints
            if st.session_state.validation:
                st.markdown("---")
                
                hint_title = {
                    "simple": "### 💡 Helpful Hints",
                    "medium": "### 🎯 Targeted Guidance", 
                    "complex": "### 🧠 Expert Insights"
                }.get(difficulty_badge, "### 💭 Guidance")
                
                st.markdown(hint_title)
                st.info(st.session_state.validation)
                
                if not st.session_state.solution_effective:
                    st.markdown("**Now check if your improved solution would work!** → Use the ✅ Check Solution button")
            
            # Show both
            if (st.session_state.validation and 
                st.session_state.solution_effective):
                
                st.markdown("---")
                st.markdown("#### 🤔 Learning Summary")
                st.markdown("You've received both **hints** to improve your thinking and **evaluation** of your solution's effectiveness!")
                
                if st.session_state.solution_effective.startswith(("⚠️ PARTIALLY", "❌ NO")):
                    st.markdown("**🎯 Try revising your solution using the hints, then check again!**")
        
        # Instructions when no ticket
        else:
            with st.expander("📚 How It Works"):
                st.markdown("""
                ### **Two-Step Learning Process**
                
                **1. 💡 Get Hints First**
                - Get guidance tailored to difficulty level
                - Improve your thinking
                - Learn without being told the answer
                
                **2. ✅ Check Your Solution**
                - See if your solution would actually work
                - Get clear evaluation (✅ YES / ⚠️ PARTIALLY / ❌ NO)
                - Understand why it would/wouldn't work
                
                **Learning Path:**
                Try solution → Get hints → Improve → Check again → Learn!
                """)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)