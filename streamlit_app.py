import streamlit as st
import pandas as pd
import re
import subprocess
import tempfile
import os
from io import BytesIO

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="GAO Month in Review",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS - EXACT AFR COPY
# =============================================================================
st.markdown("""
<style>
    /* Header styling - title and badge inline */
    .header-row {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 10px;
    }
    .header-title {
        color: #002147;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }
    
    /* Section header styling */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #002147;
        margin-bottom: 8px;
    }
    
    /* Button styling to match AFR */
    .stButton > button {
        background-color: #3d6a99;
        color: white;
        border: none;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .stButton > button:hover {
        background-color: #002147;
        color: white;
    }
    
    /* Success message styling */
    .stSuccess {
        margin-bottom: 8px;
    }
    
    /* Sidebar - compressed */
    [data-testid="stSidebar"] {
        padding-top: 1rem !important;
    }
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.1rem !important;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem !important;
        margin-bottom: 0.25rem !important;
        margin-top: 0 !important;
    }
    [data-testid="stSidebar"] p {
        margin-bottom: 0.15rem !important;
        margin-top: 0 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.3rem 0 !important;
    }
    
    /* File uploader */
    [data-testid="stSidebar"] .stFileUploader {
        margin-bottom: 0.15rem !important;
    }
    [data-testid="stSidebar"] .stFileUploader label {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.2rem !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] .stFileUploader section {
        text-align: center !important;
        display: block !important;
    }
    [data-testid="stSidebar"] .stFileUploader section button {
        width: 100% !important;
        display: block !important;
    }
    [data-testid="stSidebar"] .stFileUploader [data-testid="stFileUploaderFileName"] {
        font-size: 0.85rem !important;
        padding-top: 0.4rem !important;
        padding-bottom: 0.4rem !important;
    }
    [data-testid="stSidebar"] .stFileUploader button {
        padding: 0.35rem 0.5rem !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        text-align: center !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        min-height: 2.5rem !important;
    }
    
    /* Custom status box */
    [data-testid="stSidebar"] .custom-status-box {
        background-color: #d4edda !important;
        border: 1px solid #c3e6cb !important;
        border-radius: 0.25rem !important;
        color: #155724 !important;
        padding: 0.35rem 0.5rem !important;
        margin-bottom: 0.2rem !important;
        margin-top: 0.15rem !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-align: center !important;
        line-height: 1.5 !important;
        min-height: 2.5rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Download button */
    [data-testid="stSidebar"] .stDownloadButton {
        margin-top: 0.15rem !important;
        margin-bottom: 0.15rem !important;
    }
    [data-testid="stSidebar"] .stDownloadButton button {
        padding: 0.35rem 0.5rem !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        text-align: center !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
        min-height: 2.5rem !important;
    }
    [data-testid="stSidebar"] .stDownloadButton button svg {
        display: none !important;
    }
</style>

<script>
// Auto-save to localStorage after each publication
function autoSaveToLocalStorage(publications, currentIndex) {
    const saveData = {
        publications: publications,
        currentIndex: currentIndex,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('gao_mir_autosave', JSON.stringify(saveData));
    console.log('Auto-saved to localStorage:', currentIndex);
}

// Load from localStorage on page load
function loadFromLocalStorage() {
    const saved = localStorage.getItem('gao_mir_autosave');
    if (saved) {
        return JSON.parse(saved);
    }
    return null;
}

// Clear localStorage
function clearAutoSave() {
    localStorage.removeItem('gao_mir_autosave');
    console.log('Auto-save cleared from localStorage');
}
</script>
""", unsafe_allow_html=True)

# =============================================================================
# CONFIGURATION
# =============================================================================
ALL_TOPICS = [
    "Agriculture and Food",
    "Auditing & Financial Mgmt",
    "Budget & Spending",
    "Business Regulation & Consumer Protection",
    "CORONAVIRUS OVERSIGHT",
    "Economic Development",
    "Education",
    "Employment",
    "Energy",
    "Equal Opportunity",
    "Financial Markets & Institutions",
    "GAO Mission & Operations",
    "Government Operations",
    "Health Care",
    "Homeland Security",
    "Housing",
    "Human Capital",
    "Information Management",
    "Information Security",
    "Information Technology",
    "International Affairs",
    "Justice & Law Enforcement",
    "National Defense",
    "Natural Resources & Environment",
    "Retirement Security",
    "Science & Technology",
    "Space",
    "Tax Policy & Administration",
    "Technology Assessment Products",
    "Telecommunications",
    "Transportation",
    "Veterans",
    "Worker & Family Assistance"
]

TOPIC_MAP = {
    "AGRICULTURE AND FOOD": "Agriculture and Food",
    "AUDITING AND FINANCIAL MANAGEMENT": "Auditing & Financial Mgmt",
    "BUDGET AND SPENDING": "Budget & Spending",
    "BUSINESS REGULATION AND CONSUMER PROTECTION": "Business Regulation & Consumer Protection",
    "ECONOMIC DEVELOPMENT": "Economic Development",
    "EDUCATION": "Education",
    "EMPLOYMENT": "Employment",
    "ENERGY": "Energy",
    "EQUAL OPPORTUNITY": "Equal Opportunity",
    "FINANCIAL MARKETS AND INSTITUTIONS": "Financial Markets & Institutions",
    "GOVERNMENT OPERATIONS": "Government Operations",
    "HEALTH CARE": "Health Care",
    "HOMELAND SECURITY": "Homeland Security",
    "HOUSING": "Housing",
    "HUMAN CAPITAL": "Human Capital",
    "INFORMATION MANAGEMENT": "Information Management",
    "INFORMATION SECURITY": "Information Security",
    "INFORMATION TECHNOLOGY": "Information Technology",
    "INTERNATIONAL AFFAIRS": "International Affairs",
    "JUSTICE AND LAW ENFORCEMENT": "Justice & Law Enforcement",
    "NATIONAL DEFENSE": "National Defense",
    "NATURAL RESOURCES AND ENVIRONMENT": "Natural Resources & Environment",
    "RETIREMENT SECURITY": "Retirement Security",
    "SCIENCE AND TECHNOLOGY": "Science & Technology",
    "SPACE": "Space",
    "TAX POLICY AND ADMINISTRATION": "Tax Policy & Administration",
    "TELECOMMUNICATIONS": "Telecommunications",
    "TRANSPORTATION": "Transportation",
    "VETERANS": "Veterans",
    "WORKER AND FAMILY ASSISTANCE": "Worker & Family Assistance"
}

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'publications' not in st.session_state:
    st.session_state.publications = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'loaded_file' not in st.session_state:
    st.session_state.loaded_file = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def normalize_topic_name(topic):
    """Normalize topic name from markdown to official GAO format."""
    if not topic:
        return topic
    return TOPIC_MAP.get(topic, topic)

def parse_markdown(content):
    """Parse markdown content and extract publications."""
    lines = content.split('\n')
    
    current_topic = None
    pubs_dict = {}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if re.match(r'^\*\*[A-Z][A-Z\s&]+\*\*\\$', line):
            raw_topic = line.replace('**', '').replace('\\', '').strip()
            current_topic = normalize_topic_name(raw_topic)
            i += 1
            continue
        
        if (line.startswith('**') and 
            not re.match(r'^\*\*[A-Z][A-Z\s&]+\*\*\\$', line) and
            'Month in Review' not in line and
            'LEGAL PRODUCTS' not in line):
            
            # Collect title - may span multiple lines
            # First line starts with **, subsequent lines may not
            title_parts = []
            in_title = True
            
            while i < len(lines) and in_title:
                title_line = lines[i].strip()
                
                if not title_line:
                    break
                
                # Check if this is the GAO metadata line (don't include in title)
                if re.match(r'GAO-\d+-\d+', title_line):
                    break
                
                # Remove markdown formatting
                clean = title_line.replace('**', '').replace('\\', '').strip()
                
                if clean:  # Only add non-empty parts
                    title_parts.append(clean)
                
                # Check if this line ends the title
                if title_line.endswith('**\\'):
                    i += 1
                    break
                
                i += 1
            
            title = ' '.join(title_parts)
            
            gao_num = None
            date = None
            report_url = None
            
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line:
                    gao_match = re.search(r'(GAO-\d+-\d+),\s*(.+)', next_line)
                    if gao_match:
                        gao_num = gao_match.group(1)
                        date = gao_match.group(2)
                    
                    url_match = re.search(r'https://www\.gao\.gov/products/(GAO-\d+-\d+)', next_line)
                    if url_match:
                        report_url = f"https://www.gao.gov/products/{url_match.group(1)}"
                        break
                i += 1
            
            if gao_num:
                if gao_num in pubs_dict:
                    if current_topic and current_topic not in pubs_dict[gao_num]['current_topics']:
                        pubs_dict[gao_num]['current_topics'].append(current_topic)
                else:
                    pubs_dict[gao_num] = {
                        'gao_number': gao_num,
                        'title': title,
                        'date': date,
                        'current_topics': [current_topic] if current_topic else [],
                        'report_url': report_url or f"https://www.gao.gov/products/{gao_num}",
                        'notes': ''
                    }
        
        i += 1
    
    publications = [pubs_dict[gao] for gao in sorted(pubs_dict.keys())]
    return publications

def create_markdown_output(publications, all_topics):
    """Create markdown document from reviewed publications."""
    md_lines = []
    md_lines.append("**GAO Month in Review**\n")
    md_lines.append("Month YYYY\\\n\\")
    md_lines.append("")
    
    topics_dict = {}
    for pub in publications:
        assigned = pub.get('assigned_topics', pub['current_topics'])
        for topic in assigned:
            if topic not in topics_dict:
                topics_dict[topic] = []
            topics_dict[topic].append(pub)
    
    for topic in all_topics:
        if topic not in topics_dict or not topics_dict[topic]:
            continue
        
        md_lines.append(f"**{topic.upper()}**\\\n\\")
        
        pubs = sorted(topics_dict[topic], key=lambda x: x['title'])
        
        for pub in pubs:
            md_lines.append(f"**{pub['title']}**\\")
            md_lines.append(f"{pub['gao_number']}, {pub['date']}\n")
            md_lines.append(f"-   Report: [https://www.gao.gov/products/{pub['gao_number']}](https://www.gao.gov/products/{pub['gao_number']})\n")
    
    return '\n'.join(md_lines)

# =============================================================================
# SIDEBAR - File Upload
# =============================================================================
with st.sidebar:
    st.header("Document Management")
    
    uploaded_file = st.file_uploader(
        "Upload Month in Review", 
        type=['docx', 'md'],
        help="Upload document (.docx or .md)",
    )
    
    if st.session_state.publications:
        st.markdown("---")
        
        # Combined section header - use custom styled div instead of st.success
        st.markdown(
            '<div class="custom-status-box">Document Loaded</div>',
            unsafe_allow_html=True
        )
        st.markdown("**Backup Options**")
        st.caption("✓ Auto-saved to browser after each publication")
        
        st.markdown(f"**File:** {st.session_state.loaded_file}")
        
        # Create CSV with current state
        df_data = []
        for pub in st.session_state.publications:
            df_data.append({
                'gao_number': pub['gao_number'],
                'title': pub['title'],
                'date': pub['date'],
                'original_topics': ' | '.join(pub['current_topics']),
                'assigned_topics': ' | '.join(pub.get('assigned_topics', pub['current_topics'])),
                'notes': pub.get('notes', '')
            })
        
        df = pd.DataFrame(df_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            "⬇ Download Current Progress",
            csv,
            f"progress_{st.session_state.current_index}_of_{len(st.session_state.publications)}.csv",
            "text/csv",
            help="Manual backup - download work to your computer",
            use_container_width=True
        )

# =============================================================================
# FILE PROCESSING
# =============================================================================
if uploaded_file and (not st.session_state.loaded_file or st.session_state.loaded_file != uploaded_file.name):
    with st.spinner("Processing document..."):
        markdown_content = None
        
        if uploaded_file.name.endswith('.docx'):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_docx:
                tmp_docx.write(uploaded_file.read())
                tmp_docx_path = tmp_docx.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp_md:
                tmp_md_path = tmp_md.name
            
            try:
                subprocess.run([
                    'pandoc',
                    '--track-changes=all',
                    tmp_docx_path,
                    '-o', tmp_md_path
                ], check=True, capture_output=True)
                
                with open(tmp_md_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                
                os.unlink(tmp_docx_path)
                os.unlink(tmp_md_path)
                
            except subprocess.CalledProcessError as e:
                st.error(f"Error converting document: {e.stderr.decode()}")
                st.stop()
            except FileNotFoundError:
                st.error("Pandoc not found.")
                st.info("For Streamlit Cloud: Ensure packages.txt contains 'pandoc'")
                st.stop()
        else:
            markdown_content = uploaded_file.read().decode('utf-8')
        
        if markdown_content:
            pubs = parse_markdown(markdown_content)
            st.session_state.publications = pubs
            st.session_state.current_index = 0
            st.session_state.loaded_file = uploaded_file.name
            st.rerun()

# =============================================================================
# HEADER
# =============================================================================
st.markdown('<p class="header-title">Month in Review - Topic Assignment</p>', unsafe_allow_html=True)
st.markdown("---")

# =============================================================================
# MAIN CONTENT
# =============================================================================
if st.session_state.publications is None:
    st.info("No document loaded. Please upload a file using the sidebar.")
    
    st.markdown('<p class="section-header">Getting Started</p>', unsafe_allow_html=True)
    st.markdown("""
    **What this tool does:**
    
    - Review publications one at a time
    - Assign to topic areas
    - Auto-save after each publication
    - Download results as CSV or Markdown
    
    **Supported formats**: .docx, .md
    
    **To begin**: Open the sidebar and upload your document.
    """)

elif st.session_state.current_index >= len(st.session_state.publications):
    st.success(f"✓ Review Complete! {len(st.session_state.publications)} publications reviewed.")
    
    st.markdown('<p class="section-header">Download Results</p>', unsafe_allow_html=True)
    
    df_data = []
    for pub in st.session_state.publications:
        df_data.append({
            'gao_number': pub['gao_number'],
            'title': pub['title'],
            'date': pub['date'],
            'original_topics': ' | '.join(pub['current_topics']),
            'assigned_topics': ' | '.join(pub.get('assigned_topics', pub['current_topics'])),
            'notes': pub.get('notes', '')
        })
    
    df = pd.DataFrame(df_data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            "publications_reviewed.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        md_output = create_markdown_output(st.session_state.publications, ALL_TOPICS)
        st.download_button(
            "Download Markdown",
            md_output,
            "month_review_updated.md",
            "text/markdown",
            use_container_width=True
        )
    
    with col3:
        if st.button("Start New Review", use_container_width=True):
            st.session_state.publications = None
            st.session_state.current_index = 0
            st.session_state.loaded_file = None
            st.rerun()
    
    with st.expander("📊 View Changes"):
        changes = []
        for pub in st.session_state.publications:
            orig = set(pub['current_topics'])
            assigned = set(pub.get('assigned_topics', pub['current_topics']))
            
            added = assigned - orig
            removed = orig - assigned
            
            for topic in added:
                changes.append(f"➕ ADDED: {pub['gao_number']} → {topic}")
            for topic in removed:
                changes.append(f"➖ REMOVED: {pub['gao_number']} from {topic}")
        
        if changes:
            st.write(f"**{len(changes)} changes:**")
            for change in changes:
                st.text(change)
        else:
            st.info("No changes made")

else:
    pub = st.session_state.publications[st.session_state.current_index]
    
    # Progress info above progress bar
    progress_pct = int((st.session_state.current_index / len(st.session_state.publications)) * 100)
    col_a, col_b = st.columns(2)
    with col_a:
        st.caption(f"**Publications:** {len(st.session_state.publications)}")
    with col_b:
        st.caption(f"**Progress:** {st.session_state.current_index} / {len(st.session_state.publications)} ({progress_pct}%)")
    
    # Progress bar
    progress = st.session_state.current_index / len(st.session_state.publications)
    st.progress(progress)
    
    st.markdown(f'<div class="pub-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="pub-title">{pub["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pub-meta">{pub["gao_number"]} • {pub["date"]}</div>', unsafe_allow_html=True)
    
    # Just the Open Report button
    st.link_button("Open Report in Browser", pub['report_url'], use_container_width=False)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">Select Topics</p>', unsafe_allow_html=True)
    
    current_assigned = pub.get('assigned_topics', pub['current_topics'])
    
    selected_topics = st.multiselect(
        "Select all applicable topics",
        options=ALL_TOPICS,
        default=current_assigned,
        label_visibility="collapsed"
    )
    
    notes = st.text_area(
        "Notes (optional)",
        value=pub.get('notes', ''),
        height=60,
        placeholder="Add comments or questions..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 1.5])
    
    with col1:
        if st.button("⬅ Previous", disabled=st.session_state.current_index == 0, use_container_width=True):
            st.session_state.publications[st.session_state.current_index]['assigned_topics'] = selected_topics
            st.session_state.publications[st.session_state.current_index]['notes'] = notes
            st.session_state.current_index -= 1
    
    with col2:
        if st.button("No Changes →", use_container_width=True):
            st.session_state.publications[st.session_state.current_index]['assigned_topics'] = selected_topics
            st.session_state.publications[st.session_state.current_index]['notes'] = notes
            st.session_state.current_index += 1
    
    with col3:
        if st.button("✓ Save & Next", type="primary", use_container_width=True):
            st.session_state.publications[st.session_state.current_index]['assigned_topics'] = selected_topics
            st.session_state.publications[st.session_state.current_index]['notes'] = notes
            st.session_state.current_index += 1
    
    # Auto-save to browser localStorage after any button click
    import json
    publications_json = json.dumps(st.session_state.publications)
    st.components.v1.html(
        f"""
        <script>
        autoSaveToLocalStorage({publications_json}, {st.session_state.current_index});
        </script>
        """,
        height=0
    )
