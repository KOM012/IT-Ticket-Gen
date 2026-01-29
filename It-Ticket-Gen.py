import streamlit as st
import json
import re
import google.generativeai as genai
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

# ⚠️ HARDCODE YOUR GOOGLE AI STUDIO API KEY HERE ⚠️
GOOGLE_API_KEY = "AIzaSyDu1aRBz0J4lAPJ4nkWGcgaF6t8UMwce3w"  # Replace with your actual Google AI Studio API key

# Initialize session state
if 'ticket' not in st.session_state:
    st.session_state.ticket = None
if 'validation' not in st.session_state:
    st.session_state.validation = None
if 'agent_response' not in st.session_state:
    st.session_state.agent_response = ""
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'model_list_error' not in st.session_state:
    st.session_state.model_list_error = None
if 'solution_effective' not in st.session_state:
    st.session_state.solution_effective = None

def get_available_models():
    """Get list of available models from Google AI."""
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "apikey":
        return [], "No API key configured"
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        models = genai.list_models()
        
        # Filter for models that support generateContent
        available = []
        for model in models:
            if "generateContent" in model.supported_generation_methods:
                available.append(model.name)
        
        return available, None
        
    except Exception as e:
        return [], f"Error fetching models: {str(e)[:100]}"

def parse_json_from_text(text):
    """Extract and parse JSON from text."""
    try:
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        # If no complete JSON found, build it manually
        ticket_data = {
            "user": "IT User",
            "issue": "Technical issue requiring assistance",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # Try to extract user
        user_match = re.search(r'"user":\s*"([^"]+)"', text)
        if user_match:
            ticket_data["user"] = user_match.group(1)
        
        # Try to extract issue
        issue_match = re.search(r'"issue":\s*"([^"]+)"', text)
        if issue_match:
            ticket_data["issue"] = issue_match.group(1)
        
        return ticket_data
        
    except Exception:
        # Return a minimal valid ticket
        return {
            "user": f"User from Department",
            "issue": f"Help needed with technical problem",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

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
- "issue": Basic IT problem that has straightforward solutions

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
- "issue": IT problem requiring some technical knowledge and multiple troubleshooting steps

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
- "issue": Challenging IT problem requiring deep technical knowledge, investigation, and possibly multiple systems

Make the issue complex with technical details, error messages, and specific scenarios. Good for advanced users.

Example format:
{
  "user": "Network Admin from IT Department",
  "issue": "Intermittent packet loss between main office and cloud servers. Issue occurs randomly between 2-4 PM daily. Speed tests show normal bandwidth but specific applications experience timeouts. Firewall logs show no blocked connections."
}

Return ONLY the JSON object, no other text.
"""

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key section
    st.markdown("### 🔑 API Key")
    api_key_input = st.text_input(
        "Enter your Google AI Studio API key:",
        value=GOOGLE_API_KEY if GOOGLE_API_KEY != "apikey" else "",
        type="password",
        help="Get a free API key from https://makersuite.google.com/app/apikey"
    )
    
    # Update API key if changed
    if api_key_input and api_key_input != GOOGLE_API_KEY:
        GOOGLE_API_KEY = api_key_input
        # Clear model list to force refresh
        st.session_state.available_models = []
        st.session_state.model_list_error = None
    
    # Load models button
    if st.button("🔄 Load Available Models", use_container_width=True):
        with st.spinner("Fetching available models..."):
            models, error = get_available_models()
            st.session_state.available_models = models
            st.session_state.model_list_error = error
    
    # Show available models
    if st.session_state.available_models:
        st.markdown(f"### 🤖 Available Models ({len(st.session_state.available_models)})")
        
        # Filter for text models (excluding vision models for simplicity)
        text_models = [m for m in st.session_state.available_models 
                      if "-vision" not in m.lower() and "embed" not in m.lower()]
        
        if text_models:
            model = st.selectbox(
                "Select AI Model",
                text_models,
                index=0
            )
            
            # Show model info
            with st.expander("ℹ️ Model Details"):
                st.markdown(f"**Selected:** `{model}`")
                st.markdown(f"**Total available:** {len(st.session_state.available_models)}")
        else:
            st.warning("No text generation models found")
            model = None
    elif st.session_state.model_list_error:
        st.error(st.session_state.model_list_error)
        model = None
    else:
        st.info("Click 'Load Available Models' to see available models")
        model = None
    
    # Difficulty slider
    if model:
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
    else:
        difficulty = "medium"

    st.markdown("---")
    if st.button("🔄 Refresh App", use_container_width=True):
        st.rerun()

# Main centered content area
st.markdown("<br>", unsafe_allow_html=True)  # Add some space

# Create a centered container
col_left, col_center, col_right = st.columns([1, 2, 1])

with col_center:
    # Main container
    with st.container():
        # Check if ready to generate
        can_generate = model and GOOGLE_API_KEY and GOOGLE_API_KEY != "apikey"
        
        # Header section
        if not st.session_state.ticket:
            st.markdown("### 🎯 Ready to Practice")
            st.markdown(f"Current difficulty: **{difficulty.upper()}**")
            st.markdown("Configure your API key and select a model to start.")
        
        # Generate button (only show when no ticket exists)
        if not st.session_state.ticket:
            if st.button("✨ Generate Practice Ticket", 
                         type="primary", 
                         use_container_width=True,
                         disabled=not can_generate):
                
                with st.spinner(f"Creating {difficulty} ticket..."):
                    try:
                        # Configure and initialize model
                        genai.configure(api_key=GOOGLE_API_KEY)
                        model_instance = genai.GenerativeModel(model)
                        
                        # Generate ticket based on difficulty
                        prompt = get_ticket_prompt(difficulty)
                        
                        response = model_instance.generate_content(
                            prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.3,
                                max_output_tokens=300,
                            )
                        )
                        
                        # Get and parse response
                        response_text = response.text.strip()
                        ticket_json = parse_json_from_text(response_text)
                        ticket_json["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        ticket_json["model"] = model
                        ticket_json["difficulty"] = difficulty
                        st.session_state.ticket = ticket_json
                        
                        # Clear previous responses
                        st.session_state.agent_response = ""
                        st.session_state.validation = None
                        st.session_state.solution_effective = None
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error generating ticket: {str(e)}")
                        # Create a fallback ticket
                        fallback_issues = {
                            "simple": "Computer won't turn on. No lights when power button is pressed.",
                            "medium": "Cannot connect to WiFi. Computer sees networks but fails to connect.",
                            "complex": "Intermittent network drops affecting VoIP calls. Issue occurs during peak hours only."
                        }
                        st.session_state.ticket = {
                            "user": f"Practice User ({difficulty} level)",
                            "issue": fallback_issues.get(difficulty, "Technical issue requiring investigation"),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "model": "Fallback",
                            "difficulty": difficulty
                        }
                        st.rerun()
        
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
            
            # Ticket info in a card-like format
            with st.container():
                st.markdown(f"**👤 From:** {ticket.get('user', 'User')}")
                st.markdown(f"**🕒 Submitted:** {ticket.get('timestamp', 'Just now')}")
                
                st.markdown("---")
                st.markdown("**📝 Issue Description:**")
                st.info(ticket.get('issue', 'No description available'))
            
            # Response section
            st.markdown("---")
            st.markdown("### 💭 Your Proposed Solution")
            
            # Text area for response with difficulty-based guidance
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
            
            # Store response in session state
            if response != st.session_state.agent_response:
                st.session_state.agent_response = response
            
            # Action buttons - now with TWO buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                hint_text = {
                    "simple": "💡 Get Hints",
                    "medium": "🎯 Get Guidance", 
                    "complex": "🧠 Get Insights"
                }.get(difficulty_badge, "💡 Get Hints")
                
                if st.button(hint_text,
                            use_container_width=True,
                            disabled=not (response.strip() and model),
                            help=f"Get {difficulty_badge}-level hints to improve your solution"):
                    if response.strip():
                        with st.spinner(f"Generating {difficulty_badge} hints..."):
                            try:
                                genai.configure(api_key=GOOGLE_API_KEY)
                                model_instance = genai.GenerativeModel(model)
                                
                                # Get hints based on difficulty
                                hint_prompt = get_hint_prompt(
                                    ticket.get('issue', ''),
                                    response,
                                    difficulty_badge
                                )
                                
                                validation_response = model_instance.generate_content(
                                    hint_prompt,
                                    generation_config=genai.types.GenerationConfig(
                                        temperature=0.2,
                                        max_output_tokens=400,
                                    )
                                )
                                
                                st.session_state.validation = validation_response.text.strip()
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Failed to generate hints: {str(e)}")
            
            with col_btn2:
                if st.button("✅ Check Solution", 
                            use_container_width=True,
                            disabled=not (response.strip() and model),
                            help="Check if your solution would actually fix the issue"):
                    if response.strip():
                        with st.spinner("Evaluating solution..."):
                            try:
                                genai.configure(api_key=GOOGLE_API_KEY)
                                model_instance = genai.GenerativeModel(model)
                                
                                # Get validation check
                                validation_prompt = get_validation_prompt(
                                    ticket.get('issue', ''),
                                    response
                                )
                                
                                validation_response = model_instance.generate_content(
                                    validation_prompt,
                                    generation_config=genai.types.GenerationConfig(
                                        temperature=0.1,
                                        max_output_tokens=200,
                                    )
                                )
                                
                                # Parse the validation response
                                result_text = validation_response.text.strip()
                                st.session_state.solution_effective = result_text
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Failed to evaluate solution: {str(e)}")
            
            with col_btn3:
                if st.button("🔄 New Ticket", 
                            use_container_width=True):
                    st.session_state.ticket = None
                    st.session_state.validation = None
                    st.session_state.solution_effective = None
                    st.session_state.agent_response = ""
                    st.rerun()
            
            # Show validation result if available
            if st.session_state.solution_effective:
                st.markdown("---")
                st.markdown("### 📊 Solution Evaluation")
                
                result_text = st.session_state.solution_effective
                
                # Parse and display the result with appropriate styling
                if result_text.startswith("✅ YES"):
                    st.success(result_text)
                elif result_text.startswith("⚠️ PARTIALLY"):
                    st.warning(result_text)
                elif result_text.startswith("❌ NO"):
                    st.error(result_text)
                else:
                    st.info(result_text)
                
                # Show improvement suggestion
                if result_text.startswith("⚠️ PARTIALLY") or result_text.startswith("❌ NO"):
                    st.markdown("**💡 Try getting hints to improve your solution!**")
            
            # Show hints/guidance if available
            if st.session_state.validation:
                st.markdown("---")
                
                # Title based on difficulty
                hint_title = {
                    "simple": "### 💡 Helpful Hints",
                    "medium": "### 🎯 Targeted Guidance", 
                    "complex": "### 🧠 Expert Insights"
                }.get(difficulty_badge, "### 💭 Guidance")
                
                st.markdown(hint_title)
                
                # Display the hints
                validation_text = st.session_state.validation
                st.info(validation_text)
                
                # Show check solution prompt if not already checked
                if not st.session_state.solution_effective:
                    st.markdown("**Now check if your improved solution would work!** → Use the ✅ Check Solution button")
            
            # Show both evaluation and hints if both exist
            if st.session_state.validation and st.session_state.solution_effective:
                st.markdown("---")
                st.markdown("#### 🤔 Learning Summary")
                st.markdown("You've received both **hints** to improve your thinking and **evaluation** of your solution's effectiveness!")
                
                # Check if user should try again
                if st.session_state.solution_effective.startswith(("⚠️ PARTIALLY", "❌ NO")):
                    st.markdown("**🎯 Try revising your solution using the hints, then check again!**")
        
        # Instructions when no ticket
        else:
            if not can_generate:
                st.warning("""
                **⚠️ Setup Required:**
                1. Enter your Google AI API key in the sidebar
                2. Click "Load Available Models"
                3. Select a model from the list
                """)
            
            with st.expander("📚 How It Works"):
                st.markdown(f"""
                ### **Two-Step Learning Process**
                
                **1. 💡 Get Hints First**
                - Get {difficulty}-level guidance
                - Improve your thinking
                - Learn without being told the answer
                
                **2. ✅ Check Your Solution**
                - See if your solution would actually work
                - Get clear evaluation (✅ YES / ⚠️ PARTIALLY / ❌ NO)
                - Understand why it would/wouldn't work
                
                **Learning Path:**
                Try solution → Get hints → Improve → Check again → Learn!
                """)

# Footer with learning info
st.markdown("<br><br>", unsafe_allow_html=True)  # Add space
with st.expander("🎯 Evaluation Criteria"):
    st.markdown("""
    ### **How Solutions Are Evaluated**
    
    **✅ YES - Solution would likely fix the issue:**
    - Addresses root cause effectively
    - Includes all necessary steps
    - Follows logical troubleshooting flow
    - Would resolve issue for most users
    
    **⚠️ PARTIALLY - Solution might help but needs improvements:**
    - Addresses some aspects but misses others
    - Missing key troubleshooting steps
    - Unclear or incomplete instructions
    - Might work for some cases but not all
    
    **❌ NO - Solution would not fix the issue:**
    - Doesn't address actual problem
    - Based on incorrect assumptions
    - Missing critical components
    - Would not resolve the reported issue
    
    **💡 Hint System:**
    - Simple level: General guidance
    - Medium level: Specific improvements  
    - Complex level: Strategic thinking
    """)