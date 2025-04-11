import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from OTTools import graphical_method, simplex_method, big_m_method, integer_simplex

# Page configuration
st.set_page_config(page_title="Linear Programming Solver", layout="wide")
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

st.title("Linear Programming Problem Solver")
st.markdown("""
This app demonstrates several solution methods for linear programming problems.  
Use the tabs below to select a method and input your problem parameters.
""")

# Create a mini navigation bar using tabs
tabs = st.tabs(["Graphical Method", "Simplex Method", "Big M Method", "Integer Simplex Method"])

# Helper function to display solution in a consistent and appealing way
def display_solution(method_name, optimal_value, solution, obj_type, coeffs=None, additional_info=None):
    with st.expander("Solution Details", expanded=True):
        st.subheader(f"{method_name} Solution")
        
        # Create columns for key metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Optimal Value", f"{optimal_value:.4f}")
        with col2:
            status = "Optimal solution found" if optimal_value is not None else "No feasible solution"
            st.metric("Status", status)
        
        # Display solution variables
        st.markdown("#### Decision Variables")
        
        # Create a clean display of decision variables
        var_cols = st.columns(min(len(solution), 4))  # Up to 4 columns for variables
        for i, (var_col, value) in enumerate(zip(var_cols, solution)):
            with var_col:
                st.metric(f"x{i+1}", f"{value:.4f}")
        
        # If there are more variables than columns
        remaining_vars = solution[len(var_cols):]
        if remaining_vars:
            st.write("Additional variables:")
            for i, value in enumerate(remaining_vars, start=len(var_cols)):
                st.write(f"x{i+1} = {value:.4f}")
        
        # Display objective function evaluation
        if coeffs:
            st.markdown("#### Objective Function")
            obj_terms = [f"{c:.2f}×{value:.4f}" for c, value in zip(coeffs, solution)]
            obj_expression = " + ".join(obj_terms)
            st.markdown(f"Z = {obj_expression} = **{optimal_value:.4f}**")
        
        # Display any additional information
        if additional_info:
            st.markdown("#### Additional Information")
            st.write(additional_info)
        
        # Interpretation suggestion
        st.markdown("#### Interpretation")
        obj_verb = "maximized" if obj_type == "Maximize" else "minimized"
        st.info(f"The optimal solution {obj_verb} the objective function at Z = {optimal_value:.4f}. "
                f"This means you should produce the quantities shown above to achieve the best outcome.")

# ----------------------------------------------------------------------------
# Graphical Method Tab (2-variable problems only)
# ----------------------------------------------------------------------------
with tabs[0]:
    st.header("Graphical Method")
    st.markdown("#### Define Your Problem (2 variables only)")
    
    col1, col2 = st.columns(2)
    with col1:
        obj_type = st.selectbox("Objective", ["Maximize", "Minimize"], key="graph_obj")
    with col2:
        st.write("Objective: Z = c₁x₁ + c₂x₂")
    
    c1 = st.number_input("Coefficient for x₁", value=3.0, key="graph_c1")
    c2 = st.number_input("Coefficient for x₂", value=2.0, key="graph_c2")
    
    st.markdown("**Constraints**")
    num_constraints = st.number_input("Number of Constraints", min_value=1, value=2, step=1, key="graph_num_constr")
    constraints = []
    for i in range(int(num_constraints)):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            a = st.number_input(f"x₁ coeff in constraint {i+1}", value=2.0 if i == 0 else 1.0, key=f"graph_a{i}")
        with col2:
            b = st.number_input(f"x₂ coeff in constraint {i+1}", value=1.0 if i == 0 else 2.0, key=f"graph_b{i}")
        with col3:
            op = st.selectbox(f"Operator {i+1}", ["<=", ">="], key=f"graph_op{i}")
        with col4:
            rhs = st.number_input(f"RHS {i+1}", value=8.0 if i == 0 else 6.0, key=f"graph_rhs{i}")
        # For visualization, we assume constraints are in a form suitable for plotting (typically ≤)
        constraints.append([a, b, op, rhs])
    
    if st.button("Visualize Graphical Solution", key="graphical_solve"):
        # Build parameters for the graphical method
        c = [c1, c2]
        # For plotting, we take only the coefficients and RHS values.
        A = [[cons[0], cons[1]] for cons in constraints]
        b_vals = [cons[3] for cons in constraints]
        
        # The graphical_method function is assumed to return the solution
        try:
            optimal_value, solution = graphical_method(c, A, b_vals)
            
            # Display the optimization results
            display_solution("Graphical Method", 
                            optimal_value, 
                            solution, 
                            obj_type, 
                            coeffs=[c1, c2],
                            additional_info="The graphical solution is shown in the plot above.")
            
            # Add explanation of the feasible region
            st.markdown("#### Feasible Region")
            st.info("""
                The shaded area represents the feasible region defined by your constraints.
                The optimal solution occurs at the corner point shown in the plot.
                Each line represents one constraint equation.
            """)
            
        except Exception as e:
            st.error(f"Error solving problem: {str(e)}")
            st.info("Make sure your problem has a feasible solution and is properly formulated.")

# ----------------------------------------------------------------------------
# Simplex Method Tab
# ----------------------------------------------------------------------------
with tabs[1]:
    st.header("Simplex Method")
    st.markdown("#### Define Your Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        obj_type_simplex = st.selectbox("Objective", ["Maximize", "Minimize"], key="simplex_obj")
    with col2:
        st.write("Objective: Z = c₁x₁ + c₂x₂ + ...")
    
    num_vars_simplex = st.number_input("Number of Variables", min_value=1, value=2, step=1, key="simplex_num_vars")
    coeffs_simplex = [
        st.number_input(f"Coefficient for x{i+1}", value=3.0 if i == 0 else 2.0, key=f"simplex_c{i}")
        for i in range(int(num_vars_simplex))
    ]
    
    st.markdown("**Constraints**")
    num_constr_simplex = st.number_input("Number of Constraints", min_value=1, value=2, step=1, key="simplex_num_constr")
    A_simplex = []
    b_simplex = []
    # For simplicity, assume all constraints are of type ≤.
    for i in range(int(num_constr_simplex)):
        constr_coeffs = [
            st.number_input(f"x{j+1} coeff in constraint {i+1}", value=2.0 if (i == 0 and j == 0) else (1.0), key=f"simplex_a{i}{j}")
            for j in range(int(num_vars_simplex))
        ]
        rhs = st.number_input(f"RHS for constraint {i+1}", value=8.0 if i == 0 else 6.0, key=f"simplex_rhs{i}")
        A_simplex.append(constr_coeffs)
        b_simplex.append(rhs)
    
    if st.button("Solve with Simplex Method", key="simplex_solve"):
        try:
            # Call the simplex_method with syntax: simplex_method(c, A, b)
            optimal_value, solution = simplex_method(coeffs_simplex, A_simplex, b_simplex)
            
            # Enhanced display of solution
            additional_info = """
            The Simplex Method works by moving from one corner point of the feasible region to another
            until the optimal solution is found. This method is especially efficient for problems with
            many variables and constraints.
            """
            display_solution("Simplex Method", 
                            optimal_value, 
                            solution, 
                            obj_type_simplex, 
                            coeffs=coeffs_simplex,
                            additional_info=additional_info)
            
        except Exception as e:
            st.error(f"Error solving problem: {str(e)}")
            st.info("Make sure your problem has a feasible solution and is properly formulated.")

# ----------------------------------------------------------------------------
# Big M Method Tab
# ----------------------------------------------------------------------------
with tabs[2]:
    st.header("Big M Method")
    st.markdown("#### Define Your Problem")
    
    col1, col2 = st.columns(2)
    with col1:
        obj_type_bigm = st.selectbox("Objective", ["Maximize", "Minimize"], key="bigm_obj")
    with col2:
        st.write("Objective: Z = c₁x₁ + c₂x₂ + ...")
    
    num_vars_bigm = st.number_input("Number of Variables", min_value=1, value=2, step=1, key="bigm_num_vars")
    coeffs_bigm = [
        st.number_input(f"Coefficient for x{i+1}", value=2.0 if i == 0 else 3.0, key=f"bigm_c{i}")
        for i in range(int(num_vars_bigm))
    ]
    
    st.markdown("**Constraints**")
    num_constr_bigm = st.number_input("Number of Constraints", min_value=1, value=3, step=1, key="bigm_num_constr")
    A_bigm = []
    b_bigm = []
    constraint_types = []
    for i in range(int(num_constr_bigm)):
        constr_coeffs = [
            st.number_input(f"x{j+1} coeff in constraint {i+1}", value=1.0, key=f"bigm_a{i}{j}")
            for j in range(int(num_vars_bigm))
        ]
        op = st.selectbox(f"Operator for constraint {i+1}", ["<=", ">=", "="], key=f"bigm_op{i}")
        rhs = st.number_input(f"RHS for constraint {i+1}", 
                                value=6.0 if i == 0 else (8.0 if i == 1 else 5.0), key=f"bigm_rhs{i}")
        A_bigm.append(constr_coeffs)
        b_bigm.append(rhs)
        constraint_types.append(op)
    
    if st.button("Solve with Big M Method", key="bigm_solve"):
        try:
            # For maximization, we set Min=False as per the sample syntax.
            optimal_value, solution = big_m_method(
                coeffs_bigm, A_bigm, b_bigm, constraint_types, Min=False if obj_type_bigm == "Maximize" else True
            )
            
            # Enhanced display of solution
            additional_info = """
            The Big M Method is an extension of the Simplex Method that can handle problems with equality 
            constraints or "≥" constraints. It introduces artificial variables with very high penalties 
            to find a feasible solution.
            """
            display_solution("Big M Method", 
                            optimal_value, 
                            solution, 
                            obj_type_bigm, 
                            coeffs=coeffs_bigm,
                            additional_info=additional_info)
            
        except Exception as e:
            st.error(f"Error solving problem: {str(e)}")
            st.info("Check if your problem has a feasible solution and is properly formulated.")

# ----------------------------------------------------------------------------
# Integer Simplex Method Tab
# ----------------------------------------------------------------------------
with tabs[3]:
    st.header("Integer Simplex Method")
    st.markdown("#### Define Your Problem (with integer constraints)")
    
    col1, col2 = st.columns(2)
    with col1:
        obj_type_int = st.selectbox("Objective", ["Maximize", "Minimize"], key="int_obj")
    with col2:
        st.write("Objective: Z = c₁x₁ + c₂x₂ + ... (x must be integers)")
    
    num_vars_int = st.number_input("Number of Variables", min_value=1, value=2, step=1, key="int_num_vars")
    coeffs_int = [
        st.number_input(f"Coefficient for x{i+1}", value=3.0 if i == 0 else 2.0, key=f"int_c{i}")
        for i in range(int(num_vars_int))
    ]
    
    st.markdown("**Constraints**")
    num_constr_int = st.number_input("Number of Constraints", min_value=1, value=2, step=1, key="int_num_constr")
    A_int = []
    b_int = []
    for i in range(int(num_constr_int)):
        constr_coeffs = [
            st.number_input(f"x{j+1} coeff in constraint {i+1}", value=1.0, key=f"int_a{i}{j}")
            for j in range(int(num_vars_int))
        ]
        rhs = st.number_input(f"RHS for constraint {i+1}", value=8.0 if i == 0 else 6.0, key=f"int_rhs{i}")
        A_int.append(constr_coeffs)
        b_int.append(rhs)
    
    if st.button("Solve with Integer Simplex Method", key="int_solve"):
        try:
            optimal_value, solution = integer_simplex(coeffs_int, A_int, b_int)
            
            # Check if solution values are (approximately) integers
            is_integer_solution = all(abs(x - round(x)) < 1e-6 for x in solution)
            
            # Enhanced display of solution
            additional_info = """
            The Integer Simplex Method (Branch and Bound) finds solutions where all variables must be integers.
            This is important for problems where fractional solutions don't make practical sense,
            such as production of indivisible items.
            """
            
            if not is_integer_solution:
                additional_info += "\n\n**Warning:** The solution contains non-integer values, which may indicate issues with problem formulation or solver limitations."
                
            display_solution("Integer Simplex Method", 
                            optimal_value, 
                            solution, 
                            obj_type_int, 
                            coeffs=coeffs_int,
                            additional_info=additional_info)
            
            # Round solution for display
            rounded_solution = [round(x) for x in solution]
            if rounded_solution != solution:
                st.info(f"Rounded integer solution: {rounded_solution}")
                
        except Exception as e:
            st.error(f"Error solving problem: {str(e)}")
            st.info("Integer programming problems may be infeasible or unbounded. Check your constraints.")

st.markdown("---")
st.write("Switch between the tabs above to explore each method.")