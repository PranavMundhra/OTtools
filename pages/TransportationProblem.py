import streamlit as st
import pandas as pd
import numpy as np
from OTTools import TransportationProblem

st.title("🚚 Transportation Problem Solver")
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
with st.sidebar:
    st.title("OTTools")
    page = "Home"
    st.header("Quick Links")
    st.markdown("""
    - [🔗 GitHub Repository](https://github.com/Strangehumaan/OT)
    - [📚 Documentation](https://pypi.org/project/OTTools/)
    - [🐛 Report an Issue](https://github.com/Strangehumaan/OT/issues)
    """)
    st.markdown("---")
    st.caption("© 2025 OTTools Team")

with st.expander("📌 How to Use"):
    st.markdown("""
    1. Set the number of sources and destinations
    2. Fill in the transportation costs, supply values, and demand values
    3. Select your preferred solution method
    4. Click "Solve" to see the optimal allocation and total cost
    """)

# Step 1: Matrix size inputs
col1, col2 = st.columns(2)
with col1:
    m = st.number_input("Number of Sources", min_value=1, value=3, step=1)
with col2:
    n = st.number_input("Number of Destinations", min_value=1, value=4, step=1)

# Initialize or update dataframe
if 'transport_df' not in st.session_state or st.session_state.get('m') != m or st.session_state.get('n') != n:
    # Create empty dataframe with proper dimensions
    data = np.zeros((m + 1, n + 1))
    columns = [f"D{i+1}" for i in range(n)] + ["Supply"]
    index = [f"S{i+1}" for i in range(m)] + ["Demand"]
    df = pd.DataFrame(data, columns=columns, index=index)
    
    st.session_state.transport_df = df
    st.session_state.m = m
    st.session_state.n = n

# Step 2: Editable dataframe
st.subheader("Transportation Table")
edited_df = st.data_editor(
    st.session_state.transport_df,
    use_container_width=True,
    key="transport_editor"
)

# Step 3: Method selection
method = st.selectbox(
    "Solution Method",
    options=["NWCR", "LCM", "VAM", "MODI"],
    index=0
)

# Step 4: Solve button
if st.button("🚀 Solve"):
    try:
        # Extract data
        cost_matrix = edited_df.iloc[:m, :n].astype(float).to_numpy()
        supply = edited_df.iloc[:m, n].astype(float).to_numpy()
        demand = edited_df.iloc[m, :n].astype(float).to_numpy()
        
        # Validate inputs
        if np.any(cost_matrix < 0) or np.any(supply < 0) or np.any(demand < 0):
            st.error("❌ All values must be non-negative")
            st.stop()
            
        total_supply = np.sum(supply)
        total_demand = np.sum(demand)
        
        if not np.isclose(total_supply, total_demand):
            st.warning(f"⚠️ Total Supply ({total_supply:.1f}) ≠ Total Demand ({total_demand:.1f}). The problem is unbalanced.")
        
        # Solve the problem
        tp = TransportationProblem(cost_matrix, supply, demand)
        solution = tp.solve(method)
        
        if solution is None:
            st.error("❌ No solution found. Please check your inputs.")
            st.stop()
        
        # Display solution - assuming solution is an allocation matrix
        st.subheader("Solution")
        
        # 1. Allocation Matrix
        st.write("📦 **Allocation Matrix** (Units to transport)")
        allocation_df = pd.DataFrame(
            solution, 
            index=[f"Source {i+1}" for i in range(m)], 
            columns=[f"Dest {i+1}" for i in range(n)]
        )
        st.dataframe(allocation_df, use_container_width=True)
        
        # 2. Cost Breakdown Matrix
        st.write("💰 **Cost Breakdown**")
        cost_breakdown = solution * cost_matrix
        cost_breakdown_df = pd.DataFrame(
            cost_breakdown,
            index=[f"Source {i+1}" for i in range(m)], 
            columns=[f"Dest {i+1}" for i in range(n)]
        )
        st.dataframe(cost_breakdown_df, use_container_width=True)
        
        # 3. Total Cost
        total_cost = np.sum(cost_breakdown)
        st.success(f"### Total Transportation Cost: {total_cost:.2f}")
        
        # 4. Route Details
        st.subheader("Transportation Routes")
        routes = []
        for i in range(m):
            for j in range(n):
                if solution[i, j] > 0:
                    routes.append({
                        "From": f"Source {i+1}",
                        "To": f"Dest {j+1}",
                        "Units": solution[i, j],
                        "Unit Cost": cost_matrix[i, j],
                        "Total Cost": cost_breakdown[i, j]
                    })
        
        if routes:
            st.table(pd.DataFrame(routes))
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")