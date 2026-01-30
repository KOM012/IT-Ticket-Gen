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

# Curated list of FREE models that work on OpenRouter
FREE_MODELS = [
    "tngtech/deepseek-r1t-chimera:free",           # DeepSeek R1 - reasoning model
    "google/gemini-2.0-flash-exp:free",           # Google Gemini 2.0 Flash
    "meta-llama/llama-3.2-3b-instruct:free",      # Llama 3.2 3B - fast and capable
    "meta-llama/llama-3.1-8b-instruct:free",      # Llama 3.1 8B - more powerful
    "qwen/qwen-2.5-32b-instruct:free",            # Qwen 2.5 32B - Alibaba's model
    "microsoft/phi-3.5-mini-instruct:free",       # Microsoft Phi 3.5 Mini
    "deepseek/deepseek-r1:free",                  # DeepSeek R1 base model
    "deepseek/deepseek-coder-v2-lite-instruct:free", # DeepSeek Coder for technical tasks
    "openchat/openchat-7b:free",                  # OpenChat 7B
    "cognitivecomputations/dolphin-2.9.2-llama-3.1-8b:free", # Dolphin fine-tune
    "nvidia/llama-3.1-nemotron-70b-instruct:free", # NVIDIA's 70B model
    "mistralai/mistral-7b-instruct:free",         # Mistral 7B
]

# Initialize session state
if 'ticket' not in st.session_state:
    st.session_state.ticket = None
if 'validation' not in st.session_state:
    st.session_state.validation = None
if 'agent_response' not in st.session_state:
    st.session_state.agent_response = ""
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = "tngtech/deepseek-r1t-chimera:free"  # Default to DeepSeek R1
if 'solution_effective' not in st.session_state:
    st.session_state.solution_effective = None
if 'available_models_working' not in st.session_state:
    st.session_state.available_models_working = []

def get_available_models_from_api():
    """Get available models from OpenRouter API with focus on free models."""
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            timeout=10
        )
        
        if response.status_code == 200:
            models_data = response.json()
            free_models = []
            paid_models = []
            
            # Extract model IDs and filter
            for model in models_data.get("data", []):
                model_id = model.get("id", "")
                if model_id:
                    # Skip vision and embedding models
                    if "vision" not in model_id.lower() and "embed" not in model_id.lower():
                        # Prioritize free models
                        if ":free" in model_id:
                            # Put our preferred models first
                            if "deepseek-r1t-chimera" in model_id:
                                free_models.insert(0, model_id)
                            elif "gemini-2.0-flash-exp" in model_id:
                                free_models.insert(min(1, len(free_models)), model_id)
                            elif "llama-3.2" in model_id:
                                free_models.insert(min(2, len(free_models)), model_id)
                            else:
                                free_models.append(model_id)
                        else:
                            paid_models.append(model_id)
            
            # Combine free models first, then paid
            all_models = free_models + paid_models[:5]  # Limit paid models to top 5
            
            # If we got models from API, use them (but ensure our curated free models are included)
            if all_models:
                # Add any missing curated free models
                for model in FREE_MODELS:
                    if model not in all_models and model in free_models:
                        all_models.insert(0, model)
                
                return all_models[:15]  # Return top 15 models
                
    except Exception as e:
        st.sidebar.warning(f"Could not fetch models from API: {str(e)[:50]}")
        st.sidebar.info("Using curated free models list")
    
    # Fallback to our curated free models list
    return FREE_MODELS

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
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
            
            if response.status_code == 401:
                return None, "Invalid API key. Please check your OpenRouter API key."
            elif response.status_code == 404:
                return None, f"Model '{model}' not found. Try a different model."
            elif response.status_code == 429:
                return None, "Rate limit exceeded. Please try again later."
            elif response.status_code == 403:
                return None, "API key doesn't have permission for this model."
            elif response.status_code == 400 and "context_length" in error_msg.lower():
                return None, "Response too long. Please try a shorter prompt."
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

# Initialize available models
if not st.session_state.available_models_working:
    with st.spinner("Loading free models..."):
        st.session_state.available_models_working = get_available_models_from_api()
        # Ensure our default model is in the list
        if not st.session_state.selected_model in st.session_state.available_models_working:
            st.session_state.selected_model = st.session_state.available_models_working[0] if st.session_state.available_models_working else FREE_MODELS[0]

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.success("✅ OpenRouter API Configured")
    st.caption(f"Key: {OPENROUTER_API_KEY[:8]}...")
    
    # Model selection
    if st.session_state.available_models_working:
        st.markdown(f"### 🤖 Free AI Models ({len(st.session_state.available_models_working)})")
        
        selected = st.selectbox(
            "Select AI Model",
            st.session_state.available_models_working,
            index=st.session_state.available_models_working.index(st.session_state.selected_model) 
            if st.session_state.selected_model in st.session_state.available_models_working else 0,
            key="model_selector"
        )
        st.session_state.selected_model = selected
        
        with st.expander("ℹ️ Model Info"):
            st.markdown(f"**Selected:** `{selected}`")
            
            # Model descriptions
            model_desc = {
                "deepseek-r1t-chimera": "🧠 **DeepSeek R1 Reasoning** - Excellent for step-by-step thinking",
                "gemini-2.0-flash-exp": "🤖 **Google Gemini 2.0** - Fast and reliable",
                "llama-3.2": "🦙 **Meta Llama 3.2** - Fast 3B model, good for simple tasks",
                "llama-3.1": "🦙 **Meta Llama 3.1** - More capable 8B model",
                "qwen-2.5": "🔷 **Qwen 2.5** - Powerful 32B model by Alibaba",
                "phi-3.5": "💠 **Microsoft Phi 3.5** - Small but capable",
                "deepseek-coder": "💻 **DeepSeek Coder** - Specialized for technical tasks",
                "openchat": "💬 **OpenChat** - Conversational model",
                "dolphin": "🐬 **Dolphin** - Fine-tuned for helpfulness",
                "nemotron": "🎮 **NVIDIA Nemotron** - Powerful 70B model",
                "mistral": "🌪️ **Mistral** - French AI model"
            }
            
            for key, desc in model_desc.items():
                if key in selected.lower():
                    st.caption(desc)
                    break
            
            if ":free" in selected:
                st.success("🆓 **Free Model** - No credits needed")
            else:
                st.warning("💳 **Paid Model** - May consume credits")
    
    # Refresh models button
    if st.button("🔄 Refresh Models List", use_container_width=True):
        with st.spinner("Fetching latest free models..."):
            st.session_state.available_models_working = get_available_models_from_api()
            st.rerun()
    
    # Model recommendations
    st.markdown("---")
    st.markdown("### 🎯 Recommended Models")
    
    rec_models = [
        ("🧠 DeepSeek R1 Chimera", "tngtech/deepseek-r1t-chimera:free", "Best for reasoning"),
        ("🤖 Gemini 2.0 Flash", "google/gemini-2.0-flash-exp:free", "Fast & reliable"),
        ("🦙 Llama 3.2 3B", "meta-llama/llama-3.2-3b-instruct:free", "Quick responses"),
    ]
    
    for name, model_id, desc in rec_models:
        if model_id in st.session_state.available_models_working:
            if st.button(f"Use {name}", key=f"btn_{model_id}", use_container_width=True):
                st.session_state.selected_model = model_id
                st.rerun()
            st.caption(f"*{desc}*")
    
    # Difficulty slider
    st.markdown("---")
    st.markdown("### 📊 Difficulty Level")
    
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
                model_name = st.session_state.selected_model.split('/')[-1].split(':')[0]
                st.markdown(f"**Model:** {model_name}")
                st.markdown(f"**Difficulty:** {difficulty.upper()}")
                st.markdown("Click 'Generate Practice Ticket' to start.")
                
                # Show free model indicator
                if ":free" in st.session_state.selected_model:
                    st.success("🆓 Using free model - no credits required")
            else:
                st.warning("No models available. Please check your API key.")
        
        # Generate button
        if not st.session_state.ticket:
            if st.button("✨ Generate Practice Ticket", 
                         type="primary", 
                         use_container_width=True,
                         disabled=not can_generate):
                
                with st.spinner(f"Creating {difficulty} ticket with {st.session_state.selected_model.split('/')[-1].split(':')[0]}..."):
                    try:
                        prompt = get_ticket_prompt(difficulty)
                        
                        messages = [
                            {
                                "role": "system",
                                "content": "You are an IT support ticket generator. Return ONLY valid JSON with 'user' and 'issue' fields. No explanations, just JSON."
                            },
                            {
                                "role": "user", 
                                "content": prompt
                            }
                        ]
                        
                        response_text, error = call_openrouter_api(
                            st.session_state.selected_model,
                            messages,
                            max_tokens=250,  # Reduced for free models
                            temperature=0.3
                        )
                        
                        if error:
                            st.error(f"API Error: {error}")
                            # Try a fallback free model
                            if "not found" in error.lower() or "404" in error:
                                st.info("Trying alternative free model...")
                                for fallback in ["google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.2-3b-instruct:free"]:
                                    if fallback in st.session_state.available_models_working:
                                        st.session_state.selected_model = fallback
                                        st.rerun()
                                        break
                        elif response_text:
                            ticket_json = parse_json_from_text(response_text)
                            
                            if not ticket_json:
                                st.error("Failed to parse JSON. The AI might not have followed instructions. Please try again.")
                                # Show the raw response for debugging
                                with st.expander("View raw AI response"):
                                    st.code(response_text[:500])
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
                            st.error("No response from AI. Please try a different model.")
                            
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
            
            # Model info
            model_name = ticket.get('model', 'Unknown').split('/')[-1].split(':')[0]
            is_free = ":free" in ticket.get('model', '')
            
            # Ticket display section
            st.markdown(f"### 📋 Practice Ticket {badge_color}")
            st.caption(f"**Level:** {difficulty_badge.upper()} | **Model:** {model_name}")
            if is_free:
                st.caption("🆓 **Free Model**")
            
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
                                        "content": "You are an IT mentor providing helpful hints. Be concise and guiding."
                                    },
                                    {
                                        "role": "user", 
                                        "content": hint_prompt
                                    }
                                ]
                                
                                response_text, error = call_openrouter_api(
                                    st.session_state.selected_model,
                                    messages,
                                    max_tokens=300,  # Reduced for free models
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
                                        "content": "You are an IT solution evaluator. Always start with ✅ YES, ⚠️ PARTIALLY, or ❌ NO followed by one sentence."
                                    },
                                    {
                                        "role": "user", 
                                        "content": validation_prompt
                                    }
                                ]
                                
                                response_text, error = call_openrouter_api(
                                    st.session_state.selected_model,
                                    messages,
                                    max_tokens=150,  # Reduced for free models
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
                ### **🎯 Two-Step Learning Process**
                
                **1. 💡 Get Helpful Hints**
                - Get guidance tailored to difficulty level
                - Improve your thinking without full answers
                - Learn systematic troubleshooting
                
                **2. ✅ Validate Your Solution**
                - See if your solution would actually work
                - Get clear evaluation (✅/⚠️/❌)
                - Understand why solutions succeed or fail
                
                **🚀 Learning Path:**
                Try solution → Get hints → Improve → Check again → Learn!
                """)

# Footer with tips
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("💡 Tips for Best Results"):
    st.markdown("""
    ### **🎯 Using Free Models Effectively:**
    
    **Recommended Models:**
    1. **🧠 DeepSeek R1 Chimera** - Best for reasoning and step-by-step thinking
    2. **🤖 Gemini 2.0 Flash** - Fast and reliable for most tasks
    3. **🦙 Llama 3.2 3B** - Quick responses for simple issues
    
    **Best Practices:**
    - Start with **Simple** difficulty if models are slow
    - Keep your solution descriptions **concise**
    - If a model fails, try another free model
    - Free models work best with shorter prompts
    
    **Troubleshooting:**
    - **Model not found**: Click "🔄 Refresh Models List"
    - **No response**: Try a different free model
    - **JSON errors**: The model might need clearer instructions
    - **Slow responses**: Try Llama 3.2 3B (fastest free model)
    
    **All models listed are FREE and require no credits!**
    """)