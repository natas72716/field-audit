import streamlit as st
import json
import csv
import io
from PIL import Image
from datetime import datetime

# ReportLab Imports
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)

# Set page configuration
st.set_page_config(
    page_title="Direct Line & Mercury Field Audit Portal",
    page_icon="📋",
    layout="wide"
)

# Colors matching the corporate styling DNA
COLORS = {
    'heading': HexColor('#1A365D'),  # Dark Navy
    'body': HexColor('#2D3748'),     # Charcoal
    'accent': HexColor('#D69E2E'),   # Gold/Amber
    'muted': HexColor('#718096'),    # Muted Slate
    'bg_alt': HexColor('#F7FAFC'),   # Light Tint
    'border': HexColor('#E2E8F0'),   # Light Gray
    'white': HexColor('#FFFFFF')
}

st.title("📋 Direct Line & Mercury Fiber Build Field Audit Portal")
st.markdown("""
This interactive web portal allows field inspectors to conduct **Overhead, Underground, and General Site Compliance Audits**. 
Complete the checklist, **upload on-site photos**, and instantly export a publication-quality **PDF Audit Report** with embedded images, or download the raw data as a **CSV/JSON** file.
""")

# Establish session state for audits
if "deficiencies" not in st.session_state:
    st.session_state["deficiencies"] = []

# Tabs for easy layout
tab1, tab2, tab3, tab4 = st.tabs([
    "📍 1. Audit Metadata", 
    "🛡️ 2. Quality Checklists", 
    "📸 3. Photos & Deficiencies", 
    "💾 4. Sign-Off & Export"
])

# --- TAB 1: METADATA ---
with tab1:
    st.header("Site Audit Metadata")
    col1, col2 = st.columns(2)
    
    with col1:
        audit_date = st.date_input("Audit Date", datetime.now())
        inspector = st.text_input("Lead Inspector (Direct Line)", placeholder="e.g., Josh / Jim")
        project_name = st.selectbox("Project Name", ["Magnolia Creek", "Upland (BC30)", "Shallowbrook", "Chestnut Hills"])
        structure_id = st.text_input("Structure / Location ID", placeholder="e.g., DC04-HH-12 or 11502 Mirabella Court")
        
    with col2:
        gps_coords = st.text_input("GPS Coordinates", placeholder="e.g., 41.1124° N, -85.1384° W")
        contractor_crew = st.text_input("Contractor / Subcontractor Crew", placeholder="e.g., Rodriguez (Cesar)")
        weather = st.selectbox("Weather Conditions", ["Sunny / Clear", "Overcast", "Rainy / Wet", "Humid / Extreme Heat"])
        ground_cond = st.selectbox("Ground / Soil Conditions", ["Dry / Firm", "Moist / Soft", "Saturated / Muddy / Standing Water"])

    st.subheader("Audit Scope & Classification")
    scope_col1, scope_col2, scope_col3 = st.columns(3)
    with scope_col1:
        is_overhead = st.checkbox("Overhead Inspection", value=True)
    with scope_col2:
        is_underground = st.checkbox("Underground Inspection", value=True)
    with scope_col3:
        is_general_safety = st.checkbox("General Safety & Compliance Audit", value=True)

# --- TAB 2: CHECKLISTS ---
with tab2:
    checklist_results = {}
    
    # Custom widget for checklist item
    def checklist_item(label, key):
        st.markdown(f"**{label}**")
        r_col1, r_col2 = st.columns([1, 3])
        with r_col1:
            status = st.radio("Status", ["Pass", "Fail", "N/A"], key=f"status_{key}", horizontal=True)
        with r_col2:
            comment = st.text_input("Notes / Corrective Action Needed", key=f"comment_{key}", placeholder="Add details if failed...")
        st.markdown("---")
        return {"status": status, "comment": comment}

    if is_overhead:
        st.header("⚡ Overhead Quality Checklist")
        st.markdown("Verify structural, clearance, and hardware rules for aerial paths.")
        checklist_results["OH_pole_integrity"] = checklist_item("1. Pole & Attachment Structural Integrity (no lean, rot, splits, or loose hardware)", "oh_pole")
        checklist_results["OH_clearance"] = checklist_item("2. Vertical Clearance & Aerial Separation (min 18ft over roads, safe separation from high-voltage lines)", "oh_clearance")
        checklist_results["OH_splicing_bonding"] = checklist_item("3. Splicing, Bonding & Slack Loop Quality (neat loops, loop sizing, proper hardware)", "oh_splicing")
        checklist_results["OH_tagging"] = checklist_item("4. Fiber Tagging & Proper Labeling (fiber tails labeled at both ends; no unlabeled aerial tags)", "oh_tagging")
        checklist_results["OH_guy_wires"] = checklist_item("5. Guy Wires, Anchoring & Guards (proper tension, yellow safety guard presence)", "oh_guy")

    if is_underground:
        st.header("🕳️ Underground Quality Checklist")
        st.markdown("Verify ground structures, conduit, grounding, and restoration.")
        checklist_results["UG_hh_grade"] = checklist_item("1. Handhole Integrity & Grade Alignment (no sinking, cracks, or missing gravel padding)", "ug_hh_grade")
        checklist_results["UG_conduit_entry"] = checklist_item("2. Conduit Placement & Duct Entry (pipes pulled up fully, trimmed properly, sealed with plugs/tape)", "ug_conduit")
        checklist_results["UG_grounding"] = checklist_item("3. Splice Case Grounding & Armor Bonding (cabinet grounded, splice cases bonded to cabinet, MSTs grounded to rods)", "ug_grounding")
        checklist_results["UG_tracer_wire"] = checklist_item("4. Tracer Wire & Locator Tone Check (wire termination, continuity, locator tone strength)", "ug_tracer")
        checklist_results["UG_mule_tape"] = checklist_item("5. Mule Tape & Pull String Verification (locatable mule tape present in all completed conduits)", "ug_mule")
        checklist_results["UG_restoration"] = checklist_item("6. Restoration, Sod/Seed & Backfill Safety (soil leveled, sod/seed quality, no sidewalk or driveway cracks)", "ug_resto")

    if is_general_safety:
        st.header("🦺 General Site Safety & Compliance Checklist")
        st.markdown("Verify compliance with subcontractor standards and public safety rules.")
        checklist_results["SF_staging"] = checklist_item("1. Staging Cleanliness & Laydown Safety (no street staging in neighborhood, clean yards, no hazards)", "sf_staging")
        checklist_results["SF_pre_field_photos"] = checklist_item("2. Pre-Field Photo Capture (pre-excavation photographs taken to shield team from pre-existing liability)", "sf_photos")
        checklist_results["SF_traffic_controls"] = checklist_item("3. Traffic Controls & Safety Cones (cones/signs active around active rigs, open cabinets, or roadways)", "sf_traffic")
        checklist_results["SF_lids_closed"] = checklist_item("4. Handhole Lid Safety & Protection (lids closed immediately after locates to protect local children)", "sf_lids")
        checklist_results["SF_branding"] = checklist_item("5. Subcontractor Truck Branding & Vests (distinct vehicle magnets, high-visibility vests worn by crew)", "sf_branding")

# --- TAB 3: PHOTOS & DEFICIENCIES ---
with tab3:
    st.header("Photo Attachment & Deficiency Log")
    st.markdown("Upload pictures taken in the field (max 10MB per photo). Attach comments to document damage, pre-existing issues, or completed fixes.")

    uploaded_files = st.file_uploader("Upload Field Photos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    # Display and manage uploaded photos
    photo_attachments = []
    if uploaded_files:
        st.subheader("Photo Grid")
        p_cols = st.columns(3)
        for i, file in enumerate(uploaded_files):
            col_idx = i % 3
            with p_cols[col_idx]:
                image = Image.open(file)
                st.image(image, caption=file.name, use_container_width=True)
                photo_desc = st.text_input(f"Photo Description / Caption ({file.name})", key=f"desc_{i}", placeholder="e.g., Pre-existing driveway crack at Fazio Rd.")
                photo_attachments.append({
                    "file": file,
                    "name": file.name,
                    "description": photo_desc
                })

    st.markdown("---")
    st.header("Deficiency Log & Remediation Plan")
    st.markdown("Use this section to outline serious failures that require a formal contractor backcharge or rapid field correction.")
    
    with st.form("deficiency_form", clear_on_submit=True):
        st.write("Add New Deficiency Entry")
        def_item = st.text_input("Deficient Item / System", placeholder="e.g., Sump Pump Drain Breakage at Lanark Place")
        def_desc = st.text_area("Detailed Notes / Location / Proof", placeholder="Describe the failure, references, or contractor fault details...")
        def_remedy = st.text_input("Remediation / Corrective Action Required", placeholder="e.g., Contractor to bore new 144ft shot at their cost")
        submitted = st.form_submit_button("Add to Log")
        if submitted and def_item:
            st.session_state["deficiencies"].append({
                "item": def_item,
                "description": def_desc,
                "remedy": def_remedy
            })
            st.success(f"Added: {def_item}")

    if st.session_state["deficiencies"]:
        st.subheader("Active Deficiency Log")
        for idx, d in enumerate(st.session_state["deficiencies"]):
            st.markdown(f"**{idx+1}. {d['item']}**")
            st.markdown(f"*Description:* {d['description']}")
            st.markdown(f"*Remediation Needed:* {d['remedy']}")
            if st.button("Remove Entry", key=f"remove_def_{idx}"):
                st.session_state["deficiencies"].pop(idx)
                st.rerun()

# --- TAB 4: SIGN-OFF & EXPORT ---
with tab4:
    st.header("Formal Sign-Off & Verification")
    st.markdown("Complete the field audit with official signatures and titles.")
    
    sign_col1, sign_col2 = st.columns(2)
    with sign_col1:
        st.markdown("**Auditor / Inspector (Direct Line)**")
        auditor_name = st.text_input("Auditor Printed Name")
        auditor_title = st.text_input("Auditor Title", value="Lead Field Inspector")
        auditor_sign = st.checkbox("Sign Electronically (Auditor)")
        
    with sign_col2:
        st.markdown("**Contractor Representative**")
        contractor_name = st.text_input("Contractor Representative Name")
        contractor_title = st.text_input("Contractor Title", value="Foreman / Supervisor")
        contractor_sign = st.checkbox("Sign Electronically (Contractor)")

    st.markdown("---")
    st.header("Save, Publish, and Export Report")
    st.markdown("Generate your customized, professional Audit Report instantly.")

    # --- COMPILING THE PDF USING REPORTLAB ---
    def generate_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=54, leftMargin=54,
            topMargin=54, bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # Define styles matching design standards
        title_style = ParagraphStyle(
            'DocTitle', fontName='Helvetica-Bold', fontSize=20,
            textColor=COLORS['heading'], leading=24, spaceAfter=8, alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle', fontName='Helvetica', fontSize=10,
            textColor=COLORS['muted'], leading=13, spaceAfter=20, alignment=TA_CENTER
        )
        h1_style = ParagraphStyle(
            'H1', fontName='Helvetica-Bold', fontSize=14,
            textColor=COLORS['heading'], leading=18, spaceBefore=15, spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body', fontName='Helvetica', fontSize=10,
            textColor=COLORS['body'], leading=14, spaceAfter=6
        )
        body_bold = ParagraphStyle(
            'BodyBold', fontName='Helvetica-Bold', fontSize=10,
            textColor=COLORS['body'], leading=14, spaceAfter=6
        )
        table_head_style = ParagraphStyle(
            'TableHead', fontName='Helvetica-Bold', fontSize=9,
            textColor=COLORS['white'], leading=12
        )
        table_body_style = ParagraphStyle(
            'TableBody', fontName='Helvetica', fontSize=9,
            textColor=COLORS['body'], leading=12
        )
        table_body_bold = ParagraphStyle(
            'TableBodyBold', fontName='Helvetica-Bold', fontSize=9,
            textColor=COLORS['body'], leading=12
        )

        story = []

        # Document Header
        story.append(Paragraph("FIBER BUILD QUALITY FIELD AUDIT REPORT", title_style))
        story.append(Paragraph(f"Direct Line Communications & Mercury Partners | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
        
        # Section 1: Site Metadata
        story.append(Paragraph("1. Site Audit Metadata", h1_style))
        metadata_data = [
            [Paragraph("<b>Audit Date:</b>", body_style), Paragraph(str(audit_date), body_style), Paragraph("<b>GPS Coordinates:</b>", body_style), Paragraph(str(gps_coords), body_style)],
            [Paragraph("<b>Inspector:</b>", body_style), Paragraph(inspector, body_style), Paragraph("<b>Contractor Crew:</b>", body_style), Paragraph(contractor_crew, body_style)],
            [Paragraph("<b>Project Name:</b>", body_style), Paragraph(project_name, body_style), Paragraph("<b>Weather Conditions:</b>", body_style), Paragraph(weather, body_style)],
            [Paragraph("<b>Structure / Loc ID:</b>", body_style), Paragraph(structure_id, body_style), Paragraph("<b>Ground / Soil:</b>", body_style), Paragraph(ground_cond, body_style)],
        ]
        
        meta_table = Table(metadata_data, colWidths=[100, 150, 100, 154])
        meta_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, COLORS['border']),
            ('BACKGROUND', (0,0), (-1,-1), COLORS['bg_alt']),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # Section 2: Checklist Table
        story.append(Paragraph("2. Quality & Compliance Checklist Results", h1_style))
        
        checklist_rows = [[
            Paragraph("Inspection Category / Quality Gate", table_head_style),
            Paragraph("Status", table_head_style),
            Paragraph("Inspector Comments / Corrective Action", table_head_style)
        ]]
        
        for name, data in checklist_results.items():
            formatted_name = name.replace("OH_", "Overhead: ").replace("UG_", "Underground: ").replace("SF_", "Safety: ").replace("_", " ").title()
            status_text = data['status']
            notes_text = data['comment'] if data['comment'] else "Compliant / N/A"
            
            # Highlight Fail status
            status_style = table_body_bold if status_text == "Fail" else table_body_style
            
            checklist_rows.append([
                Paragraph(formatted_name, table_body_bold),
                Paragraph(status_text, status_style),
                Paragraph(notes_text, table_body_style)
            ])
            
        check_table = Table(checklist_rows, colWidths=[180, 60, 264], repeatRows=1)
        check_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), COLORS['heading']),
            ('GRID', (0,0), (-1,-1), 0.5, COLORS['border']),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [COLORS['white'], COLORS['bg_alt']]),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(check_table)
        story.append(Spacer(1, 15))

        # Section 3: Deficiency Log
        if st.session_state["deficiencies"]:
            story.append(Paragraph("3. System Deficiency Log & Remediation Plans", h1_style))
            for idx, d in enumerate(st.session_state["deficiencies"]):
                story.append(Paragraph(f"<b>Deficiency #{idx+1}: {d['item']}</b>", body_bold))
                story.append(Paragraph(f"<i>Description / Proof:</i> {d['description']}", body_style))
                story.append(Paragraph(f"<i>Required Corrective Action:</i> {d['remedy']}", body_style))
                story.append(Spacer(1, 8))
            story.append(Spacer(1, 10))

        # Section 4: Attached Field Photos
        if photo_attachments:
            story.append(Paragraph("4. On-Site Attached Photo Documentation", h1_style))
            for idx, photo in enumerate(photo_attachments):
                # Resize image for PDF using PIL safely
                orig_img = Image.open(photo['file'])
                # Calculate aspect ratio
                w, h = orig_img.size
                max_w = 400.0
                ratio = max_w / float(w)
                new_h = float(h) * ratio
                
                # Convert back to ReportLab compatible image bytes
                img_byte_arr = io.BytesIO()
                orig_img.save(img_byte_arr, format='JPEG')
                img_byte_arr.seek(0)
                
                rl_img = RLImage(img_byte_arr, width=4*inch, height=(new_h / 72.0)*inch)
                
                photo_elements = [
                    rl_img,
                    Spacer(1, 4),
                    Paragraph(f"<b>Figure {idx+1}:</b> {photo['description'] if photo['description'] else photo['name']}", body_style),
                    Spacer(1, 15)
                ]
                story.append(KeepTogether(photo_elements))

        # Section 5: Signatures
        story.append(Spacer(1, 15))
        sig_data = [
            [
                Paragraph(f"<b>Direct Line Auditor:</b><br/>{auditor_name}<br/><i>{auditor_title}</i><br/>Signed: {'[ELECTRONIC]' if auditor_sign else '[PENDING]'} ({datetime.now().strftime('%Y-%m-%d') if auditor_sign else ''})", body_style),
                Paragraph(f"<b>Contractor Representative:</b><br/>{contractor_name}<br/><i>{contractor_title}</i><br/>Signed: {'[ELECTRONIC]' if contractor_sign else '[PENDING]'} ({datetime.now().strftime('%Y-%m-%d') if contractor_sign else ''})", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[252, 252])
        sig_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, COLORS['border']),
            ('BACKGROUND', (0,0), (-1,-1), COLORS['bg_alt']),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(KeepTogether([
            Paragraph("5. Authorizations & Verification Sign-Off", h1_style),
            sig_table
        ]))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    # --- COMPILING THE CSV DATA ---
    def generate_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Direct Line Fiber Build Quality Audit Report"])
        writer.writerow(["Generated Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow([])
        
        # Write Metadata
        writer.writerow(["SECTION 1: SITE AUDIT METADATA"])
        writer.writerow(["Audit Date", audit_date])
        writer.writerow(["Inspector", inspector])
        writer.writerow(["Project Name", project_name])
        writer.writerow(["Structure / Loc ID", structure_id])
        writer.writerow(["GPS Coordinates", gps_coords])
        writer.writerow(["Contractor Crew", contractor_crew])
        writer.writerow(["Weather", weather])
        writer.writerow(["Ground Conditions", ground_cond])
        writer.writerow([])
        
        # Write Checklist Results
        writer.writerow(["SECTION 2: COMPLIANCE CHECKLIST RESULTS"])
        writer.writerow(["Inspection Item", "Status", "Notes/Comments"])
        for name, data in checklist_results.items():
            formatted_name = name.replace("OH_", "Overhead: ").replace("UG_", "Underground: ").replace("SF_", "Safety: ").replace("_", " ").title()
            writer.writerow([formatted_name, data['status'], data['comment']])
        writer.writerow([])
        
        # Write Deficiency Log
        writer.writerow(["SECTION 3: SYSTEM DEFICIENCY LOG"])
        writer.writerow(["Item", "Description / Proof", "Required Correction"])
        for idx, d in enumerate(st.session_state["deficiencies"]):
            writer.writerow([f"Deficiency #{idx+1}: {d['item']}", d['description'], d['remedy']])
        writer.writerow([])
        
        # Write Authorizations
        writer.writerow(["SECTION 4: SIGN-OFF"])
        writer.writerow(["DL Auditor Name", auditor_name, "Title", auditor_title, "Signed", "Yes" if auditor_sign else "No"])
        writer.writerow(["Contractor Representative", contractor_name, "Title", contractor_title, "Signed", "Yes" if contractor_sign else "No"])
        
        return output.getvalue()

    # Action layout
    st.subheader("Generate & Download Options")
    act_col1, act_col2 = st.columns(2)
    
    with act_col1:
        pdf_data = generate_pdf()
        st.download_button(
            label="📄 Export Completed Audit as PDF Report",
            data=pdf_data,
            file_name=f"fiber-audit-report-{structure_id.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    with act_col2:
        csv_data = generate_csv()
        st.download_button(
            label="📊 Export Raw Audit Data to CSV Spreadsheet",
            data=csv_data,
            file_name=f"fiber-audit-data-{structure_id.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("---")
    st.info("💡 **Field Execution Hint:** If using this app on a phone, you can utilize your mobile device's camera to snap photos directly within the 'Upload Field Photos' upload widget!")
