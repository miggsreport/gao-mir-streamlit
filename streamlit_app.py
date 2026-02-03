"""
GAO Month in Review - Topic Assignment Tool
Clean rewrite matching AFR Demo styling
"""
import streamlit as st
import pandas as pd
import re
import subprocess
import tempfile
import os
import json
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
# CUSTOM CSS - Clean AFR-style approach
# =============================================================================
st.markdown("""
<style>
    /* ===== MAIN CONTENT AREA ===== */
    
    /* Reduce default top padding */
    .main .block-container {
        padding-top: 0.75rem;
        padding-bottom: 0.5rem;
    }
    
    /* Header title - larger */
    .header-title {
        color: #002147;
        font-size: 2.25rem;
        font-weight: 700;
        margin: 0;
        margin-bottom: 4px;
    }
    
    /* Horizontal rule - tighter */
    hr {
        margin-top: 4px;
        margin-bottom: 6px;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #002147;
        margin-top: 8px;
        margin-bottom: 6px;
    }
    
    /* Publication card */
    .pub-card {
        background: #f8f9fa;
        border-left: 4px solid #3d6a99;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .pub-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #002147;
        margin-bottom: 4px;
        line-height: 1.35;
    }
    .pub-meta {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0;
    }
    
    /* Current topics display - pill-like sizing */
    .current-topics {
        font-size: 0.8rem;
        color: #856404;
        background: #fff3cd;
        padding: 6px 10px;
        border-radius: 4px;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    
    /* Button styling - smaller, pill-like */
    .stButton > button {
        background-color: #3d6a99;
        color: white;
        border: none;
        padding: 3px 10px;
        border-radius: 4px;
        font-weight: 500;
        font-size: 0.8rem;
        min-height: 0;
        line-height: 1.4;
    }
    .stButton > button:hover {
        background-color: #002147;
        color: white;
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #002147;
    }
    
    /* Link button styling - match regular buttons exactly */
    .stLinkButton a {
        background-color: #3d6a99 !important;
        color: white !important;
        border: none !important;
        padding: 3px 10px !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        text-decoration: none !important;
        line-height: 1.4;
    }
    .stLinkButton a:hover {
        background-color: #002147 !important;
        color: white !important;
    }
    
    /* Success message */
    .stSuccess {
        margin-bottom: 6px;
        padding: 8px 12px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        height: 6px;
    }
    
    /* Multiselect - tighter */
    .stMultiSelect {
        margin-bottom: 6px;
    }
    
    /* Text area - smaller */
    .stTextArea {
        margin-bottom: 6px;
    }
    .stTextArea textarea {
        min-height: 50px;
    }
    
    /* Hide header anchor links */
    h1 button, h2 button, h3 button {
        display: none;
    }
    
    /* ===== SIDEBAR ===== */
    
    [data-testid="stSidebar"] {
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        margin-top: 0;
    }
    [data-testid="stSidebar"] p {
        font-size: 0.85rem;
        margin-bottom: 0.25rem;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0;
    }
    [data-testid="stSidebar"] .stProgress {
        margin-bottom: 0.5rem;
    }
    
    /* Sidebar status box */
    .sidebar-status {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        color: #155724;
        padding: 6px 10px;
        margin-bottom: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        text-align: center;
    }
    
    /* Sidebar download button */
    [data-testid="stSidebar"] .stDownloadButton button {
        width: 100%;
        font-size: 0.8rem;
        padding: 3px 10px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONFIGURATION - Topics
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

# Mapping from PoolParty format to official GAO names
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
    upper = topic.upper().strip()
    if upper in TOPIC_MAP:
        return TOPIC_MAP[upper]
    # Try partial match
    for key, val in TOPIC_MAP.items():
        if upper == key or topic == val:
            return val
    return topic

def extract_clean_url(text):
    """Extract clean GAO URL from urldefense-wrapped or plain URLs."""
    # Look for GAO product URL inside urldefense wrapper
    urldefense_match = re.search(r'https:?\*2F\*2Fwww\.gao\.gov\*2Fproducts\*2F(GAO-\d+-\d+)', text)
    if urldefense_match:
        return f"https://www.gao.gov/products/{urldefense_match.group(1)}"
    
    # Look for plain GAO URL
    plain_match = re.search(r'https://www\.gao\.gov/products/(GAO-\d+-\d+)', text)
    if plain_match:
        return f"https://www.gao.gov/products/{plain_match.group(1)}"
    
    return None

def clean_date(date_str):
    """Extract just the date portion, removing any URL or markdown artifacts."""
    if not date_str:
        return ""
    
    # Remove markdown link syntax and everything after
    date_str = re.sub(r'\s*\[.*', '', date_str)
    date_str = re.sub(r'\s*\(http.*', '', date_str)
    date_str = re.sub(r'\s*http.*', '', date_str)
    date_str = re.sub(r'\s*\].*', '', date_str)
    
    # Clean up any remaining artifacts
    date_str = date_str.strip().rstrip(',').rstrip('\\').strip()
    
    return date_str

def parse_markdown(content):
    """Parse markdown and extract publications. Deduplicates by GAO number."""
    lines = content.split('\n')
    current_topic = None
    pubs_dict = {}
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for topic header (ALL CAPS in bold)
        if re.match(r'^\*\*[A-Z][A-Z\s&]+\*\*\\?$', line):
            raw_topic = line.replace('**', '').replace('\\', '').strip()
            current_topic = normalize_topic_name(raw_topic)
            i += 1
            continue
        
        # Check for publication title (bold, not a topic header)
        if (line.startswith('**') and 
            not re.match(r'^\*\*[A-Z][A-Z\s&]+\*\*\\?$', line) and
            'Month in Review' not in line and
            'LEGAL PRODUCTS' not in line):
            
            # Collect multi-line title
            title_parts = []
            while i < len(lines):
                title_line = lines[i].strip()
                if not title_line:
                    break
                
                # Check if this is the GAO metadata line
                if re.match(r'GAO-\d+-\d+', title_line):
                    break
                
                # Remove markdown formatting
                clean = title_line.replace('**', '').replace('\\', '').strip()
                if clean:
                    title_parts.append(clean)
                
                i += 1
                
                # Check if title block ended
                if title_line.endswith('**\\') or title_line.endswith('**'):
                    break
            
            title = ' '.join(title_parts)
            
            # Find GAO number, date, and URL
            gao_num = None
            date = None
            report_url = None
            
            # Search next few lines for metadata
            search_limit = min(i + 5, len(lines))
            while i < search_limit:
                next_line = lines[i].strip()
                if next_line:
                    # Try to extract URL from this line (handles urldefense)
                    if not report_url:
                        report_url = extract_clean_url(next_line)
                    
                    # Look for GAO number and date
                    if not gao_num:
                        gao_match = re.search(r'(GAO-\d+-\d+),?\s*(.+)?', next_line)
                        if gao_match:
                            gao_num = gao_match.group(1)
                            raw_date = gao_match.group(2) if gao_match.group(2) else ""
                            date = clean_date(raw_date)
                    
                    # Stop if we found both GAO number and URL
                    if gao_num and report_url:
                        i += 1
                        break
                
                i += 1
            
            if gao_num and title:
                if gao_num in pubs_dict:
                    # Add topic to existing publication
                    if current_topic and current_topic not in pubs_dict[gao_num]['current_topics']:
                        pubs_dict[gao_num]['current_topics'].append(current_topic)
                        pubs_dict[gao_num]['assigned_topics'].append(current_topic)
                else:
                    # New publication
                    pubs_dict[gao_num] = {
                        'gao_number': gao_num,
                        'title': title,
                        'date': date if date else "",
                        'current_topics': [current_topic] if current_topic else [],
                        'report_url': report_url or f"https://www.gao.gov/products/{gao_num}",
                        'assigned_topics': [current_topic] if current_topic else [],
                        'notes': ''
                    }
            continue
        
        i += 1
    
    # Convert to sorted list
    publications = [pubs_dict[gao] for gao in sorted(pubs_dict.keys())]
    return publications

def create_markdown_output(publications, topics):
    """Create markdown output organized by topic."""
    output_lines = ["# GAO Month in Review - Updated Topic Assignments\n"]
    
    # Group publications by assigned topic
    topic_pubs = {topic: [] for topic in topics}
    
    for pub in publications:
        for topic in pub.get('assigned_topics', []):
            if topic in topic_pubs:
                topic_pubs[topic].append(pub)
    
    # Output each topic section
    for topic in topics:
        pubs = topic_pubs[topic]
        if pubs:
            output_lines.append(f"\n## {topic}\n")
            for pub in pubs:
                output_lines.append(f"**{pub['title']}**\\")
                output_lines.append(f"{pub['gao_number']}, {pub['date']}")
                output_lines.append(f"<{pub['report_url']}>\n")
    
    return '\n'.join(output_lines)

def get_progress_csv():
    """Generate CSV of current progress."""
    if not st.session_state.publications:
        return ""
    
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
    return df.to_csv(index=False)

# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.header("Document")
    
    uploaded_file = st.file_uploader(
        "Upload Month in Review",
        type=['docx', 'md'],
        help="Upload .docx or .md file",
        label_visibility="collapsed"
    )
    
    if st.session_state.publications:
        st.markdown(f'<div class="sidebar-status">✓ Document Loaded</div>', unsafe_allow_html=True)
        st.markdown(f"**File:** {st.session_state.loaded_file}")
        st.markdown(f"**Publications:** {len(st.session_state.publications)}")
        
        # Progress
        progress_pct = int((st.session_state.current_index / len(st.session_state.publications)) * 100)
        st.markdown(f"**Progress:** {st.session_state.current_index} / {len(st.session_state.publications)} ({progress_pct}%)")
        st.progress(st.session_state.current_index / len(st.session_state.publications))
        
        st.markdown("---")
        st.markdown("**Backup**")
        
        csv = get_progress_csv()
        st.download_button(
            "⬇ Download Progress",
            csv,
            f"progress_{st.session_state.current_index}_of_{len(st.session_state.publications)}.csv",
            "text/csv",
            use_container_width=True
        )

# =============================================================================
# FILE PROCESSING
# =============================================================================
if uploaded_file and (not st.session_state.loaded_file or st.session_state.loaded_file != uploaded_file.name):
    with st.spinner("Processing document..."):
        markdown_content = None
        
        if uploaded_file.name.endswith('.docx'):
            # Convert Word to Markdown using Pandoc
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
                st.error("Pandoc not found. Ensure packages.txt contains 'pandoc'")
                st.stop()
        else:
            # Already markdown
            markdown_content = uploaded_file.read().decode('utf-8')
        
        if markdown_content:
            pubs = parse_markdown(markdown_content)
            st.session_state.publications = pubs
            st.session_state.current_index = 0
            st.session_state.loaded_file = uploaded_file.name
            st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================

# Header
st.markdown('<p class="header-title">Month in Review: Topic Assignment</p>', unsafe_allow_html=True)
st.markdown("---")

# State: No document loaded
if st.session_state.publications is None:
    st.info("No document loaded. Upload a file using the sidebar.")
    
    st.markdown('<p class="section-header">Getting Started</p>', unsafe_allow_html=True)
    st.markdown("""
    **What this tool does:**
    - Review publications one at a time
    - Assign to GAO topic areas
    - Auto-saves progress to browser
    - Download results as CSV or Markdown
    
    **Supported formats:** .docx, .md
    
    **To begin:** Upload your Month in Review document in the sidebar.
    """)

# State: Review complete
elif st.session_state.current_index >= len(st.session_state.publications):
    st.success(f"✓ Review Complete! {len(st.session_state.publications)} publications reviewed.")
    
    st.markdown('<p class="section-header">Download Results</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = get_progress_csv()
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
    
    # Show changes summary
    st.markdown('<p class="section-header">Changes Summary</p>', unsafe_allow_html=True)
    
    changes = []
    for pub in st.session_state.publications:
        orig = set(pub['current_topics'])
        assigned = set(pub.get('assigned_topics', pub['current_topics']))
        
        added = assigned - orig
        removed = orig - assigned
        
        for topic in added:
            changes.append(f"➕ {pub['gao_number']} → {topic}")
        for topic in removed:
            changes.append(f"➖ {pub['gao_number']} removed from {topic}")
    
    if changes:
        st.markdown(f"**{len(changes)} changes made:**")
        for change in changes:
            st.text(change)
    else:
        st.info("No changes made to topic assignments.")

# State: Reviewing publications
else:
    pub = st.session_state.publications[st.session_state.current_index]
    idx = st.session_state.current_index
    total = len(st.session_state.publications)
    
    # Publication card
    st.markdown(f'''
    <div class="pub-card">
        <div class="pub-title">{pub["title"]}</div>
        <div class="pub-meta">{pub["gao_number"]} • {pub["date"]}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Open report button
    st.link_button("Open Report in Browser", pub['report_url'])
    
    # Current topics info
    if pub['current_topics']:
        topics_str = ", ".join(pub['current_topics'])
        st.markdown(f'<div class="current-topics"><strong>Original topics:</strong> {topics_str}</div>', unsafe_allow_html=True)
    
    # Topic selection
    st.markdown('<p class="section-header">Assign Topics</p>', unsafe_allow_html=True)
    
    current_assigned = pub.get('assigned_topics', pub['current_topics'])
    
    selected_topics = st.multiselect(
        "Select all applicable topics",
        options=ALL_TOPICS,
        default=current_assigned,
        label_visibility="collapsed"
    )
    
    # Notes
    notes = st.text_area(
        "Notes (optional)",
        value=pub.get('notes', ''),
        height=60,
        placeholder="Add comments or questions..."
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅ Previous", disabled=(idx == 0), use_container_width=True):
            # Save current before moving
            st.session_state.publications[idx]['assigned_topics'] = selected_topics
            st.session_state.publications[idx]['notes'] = notes
            st.session_state.current_index -= 1
            st.rerun()
    
    with col2:
        if st.button("No Changes →", use_container_width=True):
            # Save current and move next
            st.session_state.publications[idx]['assigned_topics'] = selected_topics
            st.session_state.publications[idx]['notes'] = notes
            st.session_state.current_index += 1
            st.rerun()
    
    with col3:
        if st.button("✓ Save & Next", type="primary", use_container_width=True):
            # Save current and move next
            st.session_state.publications[idx]['assigned_topics'] = selected_topics
            st.session_state.publications[idx]['notes'] = notes
            st.session_state.current_index += 1
            st.rerun()
    
    # Auto-save to localStorage
    publications_json = json.dumps(st.session_state.publications)
    st.components.v1.html(f"""
    <script>
    (function() {{
        const saveData = {{
            publications: {publications_json},
            currentIndex: {st.session_state.current_index},
            timestamp: new Date().toISOString()
        }};
        localStorage.setItem('gao_mir_autosave', JSON.stringify(saveData));
    }})();
    </script>
    """, height=0)
