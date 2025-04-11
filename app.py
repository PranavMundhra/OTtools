import streamlit as st
import pandas as pd
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pathlib import Path

# Configure the page
st.set_page_config(
    page_title="OTTools - Optimization Solutions",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Combined CSS styling from both versions
st.markdown("""
    <style>
    /* Dark theme colors - enhanced palette */
    :root {
        --background-color: #0F1216;
        --secondary-bg: #161B22;
        --text-color: #E6EDF3;
        --header-color: #58A6FF;
        --card-bg: #21262D;
        --card-hover: #30363D;
        --accent-color: #1F6FEB;
        --feature-card-bg: #1D2230;
        --button-color: #238636;
        --button-hover: #2EA043;
        --card-border: #30363D;
        --section-shadow: 0 8px 24px rgba(0,0,0,0.25);
        --card-shadow: 0 4px 12px rgba(0,0,0,0.15);
        --highlight-color: #FFA28B;
    }
    
    /* Typography improvements */
    body {
        font-family: 'Inter', 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        letter-spacing: 0.01em;
        line-height: 1.6;
    }
    
    .main-header {
        font-size: 48px;
        font-weight: 800;
        color: var(--header-color);
        text-align: center;
        margin-bottom: 30px;
        line-height: 1.2;
        text-shadow: 0 2px 10px rgba(88, 166, 255, 0.2);
    }
    
    .sub-header {
        font-size: 32px;
        font-weight: 700;
        color: var(--header-color);
        margin-top: 40px;
        margin-bottom: 20px;
        position: relative;
        padding-bottom: 8px;
    }
    
    .sub-header:after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: var(--accent-color);
        border-radius: 3px;
    }
    
    /* Feature cards */
    .feature-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px;
        margin: 30px 0;
    }
    
    .feature-card {
        background-color: var(--feature-card-bg);
        border-radius: 12px;
        padding: 24px;
        height: 100%;
        border: 1px solid var(--card-border);
        box-shadow: var(--card-shadow);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: var(--accent-color);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.25);
    }
    
    .feature-card:hover::before {
        width: 7px;
        background: var(--highlight-color);
    }
    
    .feature-card h3 {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 14px;
        color: white;
    }
    
    .feature-card ul {
        padding-left: 20px;
        margin-top: 12px;
    }
    
    .feature-card li {
        margin-bottom: 8px;
    }
    
    /* Action buttons */
    .action-button {
        background-color: var(--button-color);
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        width: 100%;
    }
    
    .action-button:hover {
        background-color: var(--button-hover);
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.25);
    }
    
    /* Hero section */
    .hero-container {
        display: flex;
        align-items: center;
        gap: 40px;
        margin-bottom: 40px;
    }
    
    .hero-content {
        flex: 2;
    }
    
    .hero-image {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .hero-logo {
        max-width: 100%;
        border-radius: 12px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .hero-logo:hover {
        transform: scale(1.02) rotate(1deg);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    
    /* Testimonials and content sections */
    .content-section {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 40px;
        border: 1px solid var(--card-border);
        box-shadow: var(--section-shadow);
    }
    
    /* Team cards - improved image handling */
    .team-card-container {
        background-color: var(--card-bg);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid var(--card-border);
        transition: all 0.3s ease;
        box-shadow: var(--card-shadow);
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 24px;
    }
    
    .team-card-container:hover {
        transform: translateY(-5px);
        background-color: var(--card-hover);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        border-color: var(--accent-color);
    }
    
    .profile-image-wrapper {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        overflow: hidden;
        margin: 0 auto 16px;
        border: 4px solid var(--accent-color);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .profile-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    .team-member-name {
        font-size: 22px;
        font-weight: 600;
        color: white;
        margin: 8px 0;
    }
    
    .team-member-title {
        font-size: 16px;
        color: var(--highlight-color);
        margin-bottom: 12px;
        font-weight: 500;
    }
    
    .team-member-links {
        display: flex;
        gap: 12px;
        margin-top: 12px;
        justify-content: center;
    }
    
    .social-link {
        padding: 8px 14px;
        background-color: var(--secondary-bg);
        border-radius: 20px;
        transition: all 0.2s ease;
        font-size: 14px;
        font-weight: 500;
        color: var(--header-color);
        text-decoration: none;
    }
    
    .social-link:hover {
        background-color: var(--accent-color);
        color: white;
        transform: translateY(-3px);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 40px 0 20px;
        color: #8B949E;
        font-size: 14px;
    }
    
    .footer-links {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 15px 0;
    }
    
    /* Sidebar override */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-bg);
        border-right: 1px solid var(--card-border);
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    /* Responsive improvements */
    @media (max-width: 768px) {
        .main-header { font-size: 36px; }
        .sub-header { font-size: 26px; }
        .hero-container { flex-direction: column; }
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------
# Helper functions for image handling
# ----------------------
def get_placeholder_image(text="User", size=140):
    """Generate a placeholder image with the first letter of the provided text."""
    img = Image.new('RGB', (size, size), color=(45, 55, 72))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    text_width, text_height = d.textsize(text[0].upper(), font=font)
    position = ((size - text_width) / 2, (size - text_height) / 2 - 5)
    d.text(position, text[0].upper(), font=font, fill=(255, 255, 255))
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_image_as_base64(image_path, member_name):
    """Return a base64 string for an image file. If not found, return a placeholder image."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded_string}"
    except (FileNotFoundError, IOError):
        placeholder = get_placeholder_image(member_name)
        return f"data:image/png;base64,{placeholder}"

# ----------------------
# Sidebar Navigation
# ----------------------
with st.sidebar:
    st.title("OTTools")
    page = 'Home'
    st.header("Quick Links")
    st.markdown("""
    - [🔗 GitHub Repository](https://github.com/Strangehumaan/OT)
    - [📚 Documentation](https://pypi.org/project/OTTools/)
    - [🐛 Report an Issue](https://github.com/Strangehumaan/OT/issues)
    """)
    st.markdown("---")
    st.caption("© 2025 OTTools Team")

# ----------------------
# Main Page Content
# ----------------------
if page == "Home":
    # Header and Hero section
    st.markdown("<h1 class='main-header animate-in'>OTTools</h1>", unsafe_allow_html=True)
    st.markdown("<p class='text-center' style='font-size: 24px; text-align: center; margin-top: -20px; margin-bottom: 30px;'>Operations Research Optimization Suite</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='hero-container animate-in'>
            <div class='hero-content'>
                <div class='content-section'>
                    <h2>Powerful Optimization Tools for Complex Problems</h2>
                    <p style='font-size: 18px; line-height: 1.6;'>
                        OTTools provides intuitive interfaces to solve complex optimization problems in operations research, supply chain management, and resource allocation.
                        Our suite simplifies workflow and enhances decision-making with visual solutions.
                    </p>
                    <br>
                    <div style="display: flex; gap: 16px;">
                        <a href="#features" style="text-decoration: none; flex: 1;">
                            <div class="action-button">
                                <span>Explore Features</span>
                            </div>
                        </a>
                        <a href="#team" style="text-decoration: none; flex: 1;">
                            <div class="action-button" style="background-color: var(--accent-color);">
                                <span>Meet Our Team</span>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Features section using a single HTML block for all cards
    st.markdown('<a id="features"></a>', unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header animate-in'>Our Features</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div class='feature-cards-container animate-in'>
        <div class='feature-card'>
            <h3>🚚 Transportation Problem Solver</h3>
            <p>Efficiently allocate resources from multiple origins to multiple destinations while minimizing total transportation costs.</p>
            <ul>
                <li>Support for balanced and unbalanced problems</li>
                <li>Multiple solving methods (Northwest Corner, Least Cost, VAM)</li>
                <li>Step-by-step solution visualization</li>
                <li>Export results to various formats</li>
            </ul>
        </div>
        <div class='feature-card'>
            <h3>📈 Linear Programming Problem Solver</h3>
            <p>Solve complex resource allocation problems with multiple constraints and objectives.</p>
            <ul>
                <li>Intuitive constraint and objective function builder</li>
                <li>Graphical solution for 2D problems</li>
                <li>Sensitivity analysis and shadow pricing</li>
                <li>Interactive solution exploration</li>
            </ul>
        </div>
        <div class='feature-card'>
            <h3>📊 Data Visualization Tools</h3>
            <p>Visualize your optimization results with powerful charting capabilities.</p>
            <ul>
                <li>Dynamic constraint visualization</li>
                <li>Interactive solution space exploration</li>
                <li>Customizable charts and graphs</li>
                <li>Export visualizations for presentations</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Call-to-Action buttons for problem solvers
    st.markdown("<h2 class='sub-header animate-in'>Try It Out!</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚚 Transportation Problem", use_container_width=True):
            st.switch_page("pages/TransportationProblem.py")
    with col2:
        if st.button("📈 Linear Programming Problem", use_container_width=True):
            st.switch_page("pages/LinearProgramingProblem.py")
    
    # Team section with improved image handling
    st.markdown('<a id="team"></a>', unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header animate-in'>Meet Our Team</h2>", unsafe_allow_html=True)
    
    team_tab = st.radio(
        "",
        ["Development Team", "Graphics Team"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if team_tab == "Development Team":
        st.markdown("<h3>Development Team</h3>", unsafe_allow_html=True)
        dev_team = [
            {
                "name": "Pranav Mundhra",
                "title": "Frontend Developer",
                "image_path": "image/pranav.jpeg",
                "description": "Specializes in React and Streamlit interfaces with a focus on user experience and interaction design.",
                "github": "https://github.com/PranavMundhra",
                "email": "pranavmundhra2005@gmail.com"
            },
            {
                "name": "Saad Nathani",
                "title": "Backend Developer",
                "image_path": "image/saad.jpeg", 
                "description": "Expert in optimization algorithms and mathematical modeling with Python and operations research libraries.",
                "github": "https://github.com/Strangehumaan",
                "email": "saadnathani2005@gmail.com"
            }
        ]
        dev_cols = st.columns(2)
        for i, member in enumerate(dev_team):
            with dev_cols[i]:
                image_data = get_image_as_base64(member["image_path"], member["name"])
                st.markdown(f"""
                <div class="team-card-container animate-in">
                    <div class="profile-image-wrapper">
                        <img src="{image_data}" class="profile-image" alt="{member['name']}">  
                    </div>
                    <h3 class="team-member-name">{member['name']}</h3>
                    <p class="team-member-title">{member['title']}</p>
                    <p>{member['description']}</p>
                    <div class="team-member-links">
                        <a href="{member['github']}" class="social-link" target="_blank">GitHub</a>
                        <a href="mailto:{member['email']}" class="social-link">Email</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    else:  # Graphics Team
        st.markdown("<h3>Graphics Team</h3>", unsafe_allow_html=True)
        graphics_team = [
            {
                "name": "Abhishek Patil",
                "title": "Documentation Head",
                "image_path": "image/Abhishek.png",
                "description": "Creates comprehensive guides and documentation for all OTTools features.",
                "github": "https://github.com/AbhishekkPatilll",
                "email": "abhishekpatil0729@gmail.com"
            },
            {
                "name": "Devesh Poojary",
                "title": "Presentation Head", 
                "image_path": "image/devesh.jpeg",
                "description": "Specializes in creating visual presentations and demos of optimization solutions.",
                "github": "https://github.com/Devesh1105",
                "email": "poojarydevesh11@gmail.com"
            },
            {
                "name": "Navya Singh",
                "title": "Graphics Designer",
                "image_path": "image/navya.jpeg",
                "description": "Creates user interface designs, graphics, and visual elements for the OTTools suite.",
                "github": "https://github.com/Navya895",
                "email": "rnavya2005@gmail.com"
            },
            {
                "name": "Reshma Patil",
                "title": "Visualization Specialist",
                "image_path": "image/reshma.jpeg",
                "description": "Develops data visualization components and creates interactive charts.",
                "github": "https://github.com/ReshmaPatil-02",
                "email": "reshmakp1616@gmail.com"
            }
        ]
        graphics_cols = st.columns(3)
        for i, member in enumerate(graphics_team):
            with graphics_cols[i % 3]:
                image_data = get_image_as_base64(member["image_path"], member["name"])
                st.markdown(f"""
                <div class="team-card-container animate-in">
                    <div class="profile-image-wrapper">
                        <img src="{image_data}" class="profile-image" alt="{member['name']}">
                    </div>
                    <h3 class="team-member-name">{member['name']}</h3>
                    <p class="team-member-title">{member['title']}</p>
                    <p>{member['description']}</p>
                    <div class="team-member-links">
                        <a href="{member['github']}" class="social-link" target="_blank">GitHub</a>
                        <a href="mailto:{member['email']}" class="social-link">Email</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Testimonials section
    st.markdown("<h2 class='sub-header animate-in'>What Users Say</h2>", unsafe_allow_html=True)
    testimonials_col1, testimonials_col2 = st.columns(2)
    with testimonials_col1:
        st.markdown("""
        <div class='content-section animate-in'>
            <p style="font-style: italic; font-size: 16px;">
                "OTTools has dramatically improved our logistics planning process. The transportation problem solver saved us 15% on shipping costs in just the first month of use."
            </p>
            <p style="text-align: right; font-weight: 500;">— Supply Chain Manager, Global Logistics Corp</p>
        </div>
        """, unsafe_allow_html=True)
    with testimonials_col2:
        st.markdown("""
        <div class='content-section animate-in'>
            <p style="font-style: italic; font-size: 16px;">
                "The visualization capabilities in OTTools make complex optimization problems understandable for everyone in our team. It's become an essential part of our decision-making process."
            </p>
            <p style="text-align: right; font-weight: 500;">— Professor of Operations Research, Tech University</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer animate-in">
        <h3>OTTools - Operations Research Optimization Suite</h3>
        <div class="footer-links">
            <a href="https://github.com/Strangehumaan/OT">GitHub</a>
            <a href="https://pypi.org/project/OTTools/#description">Documentation</a>
            <a href="#">Contact Us</a>
            <a href="#">Privacy Policy</a>
        </div>
        <p>© 2025 OTTools Team. All rights reserved.</p>
        <p>For inquiries, please contact <a href="mailto:info@ottools.example.com">info@ottools.example.com</a></p>
    </div>
    """, unsafe_allow_html=True)

elif page == "Transportation Problem":
    st.switch_page("pages/TransportationProblem.py")

elif page == "Linear Programming Problem":
    st.switch_page("pages/LinearProgramingProblem.py")
