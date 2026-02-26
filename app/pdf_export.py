"""
PDF Export Module for GLP1Companion
Generates professional medical reports for doctor visits
"""

from datetime import datetime, timedelta
from fpdf import FPDF
import pandas as pd
from io import BytesIO


class MedicalReportPDF(FPDF):
    """Custom PDF class for medical reports"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        # Title bar
        self.set_fill_color(16, 185, 129)  # Emerald green
        self.rect(0, 0, 210, 25, 'F')
        
        # Title
        self.set_font('Helvetica', 'B', 18)
        self.set_text_color(255, 255, 255)
        self.cell(0, 15, 'GLP1Companion Health Report', 0, 1, 'C')
        
        # Reset text color
        self.set_text_color(0, 0, 0)
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d at %I:%M %p")} by GLP1Companion', 0, 0, 'C')
    
    def section_title(self, title):
        """Add a section title with underline"""
        self.set_font('Helvetica', 'B', 14)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, title, 0, 1, 'L', fill=True)
        self.ln(3)
    
    def add_metric_row(self, label, value, unit=""):
        """Add a metric row with label and value"""
        self.set_font('Helvetica', 'B', 11)
        self.cell(60, 8, label, 0, 0)
        self.set_font('Helvetica', '', 11)
        self.cell(0, 8, f"{value} {unit}".strip(), 0, 1)
    
    def add_table_header(self):
        """Add table header row"""
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(16, 185, 129)
        self.set_text_color(255, 255, 255)
        self.cell(35, 8, 'Date/Time', 1, 0, 'C', fill=True)
        self.cell(30, 8, 'Value', 1, 0, 'C', fill=True)
        self.cell(40, 8, 'Context', 1, 0, 'C', fill=True)
        self.cell(85, 8, 'Notes', 1, 1, 'C', fill=True)
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 9)
    
    def add_table_row(self, timestamp, value, context, notes=""):
        """Add a data row to table"""
        self.cell(35, 7, timestamp, 1, 0, 'C')
        self.cell(30, 7, str(value), 1, 0, 'C')
        self.cell(40, 7, context, 1, 0, 'L')
        # Truncate notes if too long
        notes = (notes[:40] + '...') if len(notes) > 40 else notes
        self.cell(85, 7, notes, 1, 1, 'L')


def generate_health_report(user, glucose_logs, weight_logs, medication_logs, side_effects, 
                           date_range_days=30):
    """
    Generate a PDF health report for the user
    
    Args:
        user: User object from database
        glucose_logs: List of GlucoseLog objects
        weight_logs: List of WeightLog objects  
        medication_logs: List of MedicationLog objects
        side_effects: List of SideEffect objects
        date_range_days: Number of days to include in report
    
    Returns:
        BytesIO: PDF file as bytes
    """
    
    pdf = MedicalReportPDF()
    pdf.add_page()
    
    # ========== PATIENT INFO SECTION ==========
    pdf.section_title("Patient Information")
    
    # Name and date range
    report_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=date_range_days)).strftime("%Y-%m-%d")
    
    # Safely handle user fields that might be missing or None
    try:
        patient_name = getattr(user, 'name', None) or "Not provided"
    except:
        patient_name = "Not provided"
    
    try:
        diabetes_type = getattr(user, 'diabetes_type', None) or "Type 2"
    except:
        diabetes_type = "Type 2"
    
    pdf.add_metric_row("Patient Name:", patient_name)
    pdf.add_metric_row("Report Date:", report_date)
    pdf.add_metric_row("Date Range:", f"{start_date} to {report_date}")
    pdf.add_metric_row("Diabetes Type:", diabetes_type)
    pdf.ln(5)
    
    # ========== MEDICATIONS SECTION ==========
    pdf.section_title("Current Medications")
    
    # Safely get medication fields
    glp1_med = getattr(user, 'glp1_medication', None)
    glp1_dosage = getattr(user, 'glp1_dosage', None)
    other_diabetes_med = getattr(user, 'other_diabetes_med', None)
    
    if glp1_med:
        pdf.add_metric_row("GLP-1 Medication:", glp1_med)
        pdf.add_metric_row("GLP-1 Dosage:", glp1_dosage or "Not specified")
    else:
        pdf.cell(0, 8, "No GLP-1 medication on file", 0, 1)
    
    if other_diabetes_med:
        pdf.add_metric_row("Other Diabetes Meds:", other_diabetes_med)
    
    # Recent medication logs (last 10)
    if medication_logs:
        pdf.ln(3)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 8, "Recent Medication Activity:", 0, 1)
        pdf.set_fill_color(245, 245, 245)
        
        for med in medication_logs[:10]:
            med_date = med.timestamp.strftime("%Y-%m-%d %H:%M")
            status = "✓ Taken" if med.taken else "○ Not taken"
            pdf.cell(0, 7, f"  {med_date} - {med.medication} ({med.dosage or 'N/A'}) - {status}", 0, 1)
    else:
        pdf.cell(0, 8, "No recent medication logs", 0, 1)
    
    pdf.ln(5)
    
    # ========== GLUCOSE SECTION ==========
    pdf.section_title("Glucose Readings")
    
    if glucose_logs:
        # Calculate statistics
        glucose_values = [g.value for g in glucose_logs]
        avg_glucose = sum(glucose_values) / len(glucose_values)
        min_glucose = min(glucose_values)
        max_glucose = max(glucose_values)
        
        # Summary stats
        pdf.add_metric_row("Total Readings:", str(len(glucose_logs)))
        pdf.add_metric_row("Average:", f"{avg_glucose:.1f} mg/dL")
        pdf.add_metric_row("Range:", f"{min_glucose} - {max_glucose} mg/dL")
        
        # Safely handle target glucose range
        target_min = getattr(user, 'target_glucose_min', None) or 80
        target_max = getattr(user, 'target_glucose_max', None) or 130
        pdf.add_metric_row("Target Range:", f"{target_min} - {target_max} mg/dL")
        
        pdf.ln(3)
        
        # Detailed readings table
        pdf.add_table_header()
        
        # Sort by timestamp descending and take last 20
        sorted_logs = sorted(glucose_logs, key=lambda x: x.timestamp, reverse=True)[:20]
        
        for log in sorted_logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M")
            context = log.context.replace("_", " ").title() if log.context else "N/A"
            pdf.add_table_row(timestamp, f"{log.value} mg/dL", context, log.notes or "")
    else:
        pdf.cell(0, 8, "No glucose readings in the selected period", 0, 1)
    
    pdf.ln(5)
    
    # ========== WEIGHT SECTION ==========
    pdf.section_title("Weight Trend")
    
    if weight_logs:
        weight_values = [w.value for w in weight_logs]
        avg_weight = sum(weight_values) / len(weight_values)
        
        # Sort by timestamp
        sorted_weights = sorted(weight_logs, key=lambda x: x.timestamp)
        
        first_weight = sorted_weights[0].value
        last_weight = sorted_weights[-1].value
        change = last_weight - first_weight
        
        pdf.add_metric_row("Total Readings:", str(len(weight_logs)))
        pdf.add_metric_row("Current:", f"{last_weight:.1f} lbs")
        pdf.add_metric_row("Average:", f"{avg_weight:.1f} lbs")
        pdf.add_metric_row("Change:", f"{change:+.1f} lbs")
        
        # Safely handle goal weight
        goal_weight = getattr(user, 'goal_weight', None)
        if goal_weight:
            to_goal = last_weight - goal_weight
            pdf.add_metric_row("Goal:", f"{goal_weight} lbs")
            pdf.add_metric_row("To Goal:", f"{to_goal:+.1f} lbs")
        
        pdf.ln(3)
        
        # Weight table
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(60, 8, 'Date', 1, 0, 'C', fill=True)
        pdf.cell(40, 8, 'Weight (lbs)', 1, 0, 'C', fill=True)
        pdf.cell(90, 8, 'Change from Previous', 1, 1, 'C', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        
        for i, w in enumerate(sorted_weights[-15:]):  # Last 15 readings
            date_str = w.timestamp.strftime("%Y-%m-%d")
            change_str = ""
            if i > 0:
                prev = sorted_weights[len(sorted_weights) - 15 + i - 1].value
                change_str = f"{w.value - prev:+.1f}"
            
            pdf.cell(60, 7, date_str, 1, 0, 'C')
            pdf.cell(40, 7, f"{w.value:.1f}", 1, 0, 'C')
            pdf.cell(90, 7, change_str, 1, 1, 'C')
    else:
        pdf.cell(0, 8, "No weight readings in the selected period", 0, 1)
    
    pdf.ln(5)
    
    # ========== SIDE EFFECTS SECTION ==========
    pdf.section_title("Side Effects Summary")
    
    if side_effects:
        # Group by severity
        mild = [s for s in side_effects if s.severity == 'mild']
        moderate = [s for s in side_effects if s.severity == 'moderate']
        severe = [s for s in side_effects if s.severity == 'severe']
        
        pdf.add_metric_row("Total Reports:", str(len(side_effects)))
        
        if mild:
            pdf.add_metric_row("Mild:", f"{len(mild)} occurrence(s)")
        if moderate:
            pdf.add_metric_row("Moderate:", f"{len(moderate)} occurrence(s)")
        if severe:
            pdf.set_text_color(220, 53, 69)  # Red for severe
            pdf.add_metric_row("Severe:", f"{len(severe)} occurrence(s)")
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(3)
        
        # List recent side effects
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 8, "Recent Side Effects:", 0, 1)
        pdf.set_font('Helvetica', '', 9)
        
        for s in side_effects[:10]:
            date_str = s.timestamp.strftime("%Y-%m-%d")
            severity_emoji = {"mild": "○", "moderate": "◐", "severe": "●"}.get(s.severity, "•")
            pdf.cell(0, 7, f"  {date_str} {severity_emoji} {s.symptom.title()} ({s.severity})", 0, 1)
    else:
        pdf.cell(0, 8, "No side effects reported", 0, 1)
    
    pdf.ln(5)
    
    # ========== NOTES SECTION ==========
    pdf.section_title("Notes")
    
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 7, "This report was generated by GLP1Companion for informational purposes. "
                         "Please discuss any concerns with your healthcare provider. "
                         "This report does not constitute medical advice.")
    
    # ========== OUTPUT ==========
    # Return as bytes
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    
    return output
