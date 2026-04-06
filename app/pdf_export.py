"""
PDF Export Module for GLP1Companion
Generates professional medical reports for doctor visits
"""

from datetime import datetime, timedelta
from fpdf import FPDF
import pandas as pd
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _latin1_safe(text):
    """Strip characters that Helvetica/latin-1 can't render in fpdf2."""
    if not text:
        return text
    return text.encode('latin-1', errors='replace').decode('latin-1')


# =============================================================================
# CHART RENDERING
# =============================================================================

def render_weight_chart(weight_logs, goal_weight=None):
    """Line chart with fill showing weight trend. Returns BytesIO PNG or None."""
    if not weight_logs or len(weight_logs) < 2:
        return None

    sorted_logs = sorted(weight_logs, key=lambda x: x.timestamp)
    dates = [w.timestamp for w in sorted_logs]
    values = [w.value for w in sorted_logs]

    fig, ax = plt.subplots(figsize=(7, 2.5), dpi=150)
    ax.plot(dates, values, color='#10B981', linewidth=2, marker='o', markersize=4)
    ax.fill_between(dates, values, alpha=0.15, color='#10B981')

    if goal_weight:
        ax.axhline(y=goal_weight, color='#F59E0B', linestyle='--', linewidth=1.5, label=f'Goal: {goal_weight} lbs')
        ax.legend(loc='upper right', fontsize=8)

    ax.set_ylabel('Weight (lbs)', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.tick_params(axis='both', labelsize=8)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def render_glucose_chart(glucose_logs, target_min=80, target_max=130):
    """Line chart with target range shading. Returns BytesIO PNG or None."""
    if not glucose_logs or len(glucose_logs) < 2:
        return None

    sorted_logs = sorted(glucose_logs, key=lambda x: x.timestamp)
    dates = [g.timestamp for g in sorted_logs]
    values = [g.value for g in sorted_logs]

    fig, ax = plt.subplots(figsize=(7, 2.5), dpi=150)

    # Target range shading
    ax.axhspan(target_min, target_max, alpha=0.12, color='#10B981', label=f'Target ({target_min}-{target_max})')

    ax.plot(dates, values, color='#1C83E1', linewidth=1.5, marker='o', markersize=3)

    # Color dots by range
    for d, v in zip(dates, values):
        if v < target_min:
            ax.plot(d, v, 'o', color='#EF4444', markersize=5, zorder=5)
        elif v > target_max:
            ax.plot(d, v, 'o', color='#F59E0B', markersize=5, zorder=5)

    ax.set_ylabel('mg/dL', fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.tick_params(axis='both', labelsize=8)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def render_dose_timeline(dose_changes):
    """Horizontal scatter timeline of dose changes. Returns BytesIO PNG or None."""
    if not dose_changes:
        return None

    fig, ax = plt.subplots(figsize=(7, 2), dpi=150)

    dates = [c['date'] for c in dose_changes]
    colors = ['#10B981' if c['direction'] == 'increase' else '#EF4444' for c in dose_changes]
    labels = [f"{c['medication'].split(' (')[0]}\n{c['old_dose_str']}→{c['new_dose_str']}" for c in dose_changes]

    ax.scatter(dates, [0.5] * len(dates), c=colors, s=80, zorder=5)
    for i, (d, label) in enumerate(zip(dates, labels)):
        y_offset = 0.15 if i % 2 == 0 else -0.25
        ax.annotate(label, (d, 0.5), textcoords="offset points",
                    xytext=(0, 20 if i % 2 == 0 else -25), ha='center', fontsize=7,
                    arrowprops=dict(arrowstyle='-', color='gray', lw=0.5))

    ax.set_ylim(-0.5, 1.5)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.tick_params(axis='x', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.set_title('Dose Changes', fontsize=10, fontweight='bold', loc='left')
    fig.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# =============================================================================
# PDF CLASS
# =============================================================================

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
        self.cell(60, 8, _latin1_safe(label), 0, 0)
        self.set_font('Helvetica', '', 11)
        self.cell(0, 8, _latin1_safe(f"{value} {unit}".strip()), 0, 1)

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
        self.cell(35, 7, _latin1_safe(timestamp), 1, 0, 'C')
        self.cell(30, 7, _latin1_safe(str(value)), 1, 0, 'C')
        self.cell(40, 7, _latin1_safe(context), 1, 0, 'L')
        # Truncate notes if too long
        notes = (notes[:40] + '...') if len(notes) > 40 else notes
        self.cell(85, 7, _latin1_safe(notes), 1, 1, 'L')

    def check_page_break(self, h=60):
        """Add a page break if we're near the bottom."""
        if self.get_y() + h > 265:
            self.add_page()


# =============================================================================
# SECTION BUILDERS
# =============================================================================

def add_pattern_insights_section(pdf, pattern_insights):
    """Add pattern insights as a hero section, grouped by category."""
    if not pattern_insights:
        return

    pdf.add_page()
    pdf.section_title("Pattern Insights")

    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, 'AI-detected correlations from your health data', 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Group by category
    categories = {
        'weight_dose': {'label': 'Weight & Dose', 'color': (16, 185, 129)},
        'side_effect_dose': {'label': 'Side Effects & Dose', 'color': (239, 68, 68)},
        'food_protein': {'label': 'Nutrition & Weight', 'color': (28, 131, 225)},
    }

    grouped = {}
    for insight in pattern_insights:
        cat = insight.get('category', 'other')
        grouped.setdefault(cat, []).append(insight)

    for cat_key, cat_info in categories.items():
        insights = grouped.get(cat_key, [])
        if not insights:
            continue

        pdf.check_page_break(30)

        # Category header
        r, g, b = cat_info['color']
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 8, cat_info['label'], 0, 1)
        pdf.set_text_color(0, 0, 0)

        for insight in insights:
            pdf.check_page_break(15)

            # Color-coded dot
            itype = insight.get('type', 'neutral')
            if itype == 'positive':
                dot_r, dot_g, dot_b = 16, 185, 129
            elif itype == 'warning':
                dot_r, dot_g, dot_b = 245, 158, 11
            else:
                dot_r, dot_g, dot_b = 100, 116, 139

            x = pdf.get_x()
            y = pdf.get_y()
            pdf.set_fill_color(dot_r, dot_g, dot_b)
            pdf.ellipse(x + 2, y + 2, 4, 4, 'F')

            pdf.set_x(x + 10)
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(180, 6, _latin1_safe(insight['text']))
            pdf.ln(2)

        pdf.ln(3)

    # Handle any uncategorized insights
    other = grouped.get('other', [])
    if other:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Other Insights', 0, 1)
        for insight in other:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(5, 6, '', 0, 0)
            pdf.multi_cell(185, 6, _latin1_safe(f"- {insight['text']}"))
            pdf.ln(1)


def add_food_summary_section(pdf, food_logs, target_protein=None):
    """Add nutrition summary with daily averages."""
    if not food_logs:
        return

    pdf.check_page_break(60)
    pdf.section_title("Nutrition Summary")

    # Calculate daily averages
    daily = {}
    for f in food_logs:
        day = f.timestamp.date()
        if day not in daily:
            daily[day] = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meals': 0}
        daily[day]['calories'] += f.calories or 0
        daily[day]['protein'] += f.protein or 0
        daily[day]['carbs'] += f.carbs or 0
        daily[day]['fat'] += f.fat or 0
        daily[day]['meals'] += 1

    num_days = len(daily) or 1
    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'meals': 0}
    for d in daily.values():
        for k in totals:
            totals[k] += d[k]

    pdf.add_metric_row("Days Tracked:", str(num_days))
    pdf.add_metric_row("Avg Daily Calories:", f"{totals['calories'] / num_days:.0f}", "kcal")
    pdf.add_metric_row("Avg Daily Protein:", f"{totals['protein'] / num_days:.0f}", "g")
    pdf.add_metric_row("Avg Daily Carbs:", f"{totals['carbs'] / num_days:.0f}", "g")
    pdf.add_metric_row("Avg Daily Fat:", f"{totals['fat'] / num_days:.0f}", "g")
    pdf.add_metric_row("Avg Meals/Day:", f"{totals['meals'] / num_days:.1f}")

    if target_protein:
        avg_protein = totals['protein'] / num_days
        pct = (avg_protein / target_protein) * 100
        status = "On track" if pct >= 90 else "Below target" if pct >= 60 else "Needs attention"
        pdf.ln(2)
        pdf.add_metric_row("Protein Target:", f"{target_protein:.0f} g/day")
        pdf.add_metric_row("Protein Status:", f"{status} ({pct:.0f}% of target)")

    pdf.ln(3)


# =============================================================================
# MAIN REPORT GENERATOR
# =============================================================================

def generate_health_report(user, glucose_logs, weight_logs, medication_logs, side_effects,
                           date_range_days=30, food_logs=None, pattern_insights=None,
                           dose_changes=None):
    """
    Generate a PDF health report for the user

    Args:
        user: User object from database
        glucose_logs: List of GlucoseLog objects
        weight_logs: List of WeightLog objects
        medication_logs: List of MedicationLog objects
        side_effects: List of SideEffect objects
        date_range_days: Number of days to include in report
        food_logs: List of FoodLog objects (optional)
        pattern_insights: List of pattern insight dicts (optional)
        dose_changes: List of dose change dicts (optional)

    Returns:
        BytesIO: PDF file as bytes
    """

    pdf = MedicalReportPDF()
    pdf.add_page()

    # ========== PAGE 1: PATIENT INFO + MEDICATIONS ==========
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

        for med in medication_logs[:10]:
            med_date = med.timestamp.strftime("%Y-%m-%d %H:%M")
            status = "Taken" if med.taken else "Not taken"
            pdf.cell(0, 7, _latin1_safe(f"  {med_date} - {med.medication} ({med.dosage or 'N/A'}) - {status}"), 0, 1)
    else:
        pdf.cell(0, 8, "No recent medication logs", 0, 1)

    pdf.ln(5)

    # ========== PAGE 2: PATTERN INSIGHTS (hero section) ==========
    if pattern_insights:
        add_pattern_insights_section(pdf, pattern_insights)

    # ========== GLUCOSE SECTION ==========
    pdf.check_page_break(80)
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

        # In-range percentage
        in_range = len([v for v in glucose_values if target_min <= v <= target_max])
        pct_in_range = (in_range / len(glucose_values)) * 100
        pdf.add_metric_row("Time in Range:", f"{pct_in_range:.0f}%")

        pdf.ln(3)

        # Embedded chart
        chart_buf = render_glucose_chart(glucose_logs, target_min, target_max)
        if chart_buf:
            pdf.check_page_break(50)
            pdf.image(chart_buf, x=10, w=190)
            pdf.ln(3)

        # Compact table (10 rows)
        pdf.check_page_break(80)
        pdf.add_table_header()
        sorted_logs = sorted(glucose_logs, key=lambda x: x.timestamp, reverse=True)[:10]
        for log in sorted_logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M")
            context = log.context.replace("_", " ").title() if log.context else "N/A"
            pdf.add_table_row(timestamp, f"{log.value} mg/dL", context, log.notes or "")

        if len(glucose_logs) > 10:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 6, f"Showing 10 of {len(glucose_logs)} readings", 0, 1, 'R')
            pdf.set_text_color(0, 0, 0)
    else:
        pdf.cell(0, 8, "No glucose readings in the selected period", 0, 1)

    pdf.ln(5)

    # ========== WEIGHT SECTION ==========
    pdf.check_page_break(80)
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

        # Embedded chart
        chart_buf = render_weight_chart(weight_logs, goal_weight)
        if chart_buf:
            pdf.check_page_break(50)
            pdf.image(chart_buf, x=10, w=190)
            pdf.ln(3)

        # Compact weight table (10 rows)
        pdf.check_page_break(80)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(60, 8, 'Date', 1, 0, 'C', fill=True)
        pdf.cell(40, 8, 'Weight (lbs)', 1, 0, 'C', fill=True)
        pdf.cell(90, 8, 'Change from Previous', 1, 1, 'C', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', '', 9)

        display_weights = sorted_weights[-10:]  # Last 10 readings
        for i, w in enumerate(display_weights):
            date_str = w.timestamp.strftime("%Y-%m-%d")
            change_str = ""
            if i > 0:
                prev = display_weights[i - 1].value
                change_str = f"{w.value - prev:+.1f}"

            pdf.cell(60, 7, date_str, 1, 0, 'C')
            pdf.cell(40, 7, f"{w.value:.1f}", 1, 0, 'C')
            pdf.cell(90, 7, change_str, 1, 1, 'C')

        if len(weight_logs) > 10:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 6, f"Showing 10 of {len(weight_logs)} readings", 0, 1, 'R')
            pdf.set_text_color(0, 0, 0)
    else:
        pdf.cell(0, 8, "No weight readings in the selected period", 0, 1)

    pdf.ln(5)

    # ========== DOSE CHANGE TIMELINE ==========
    if dose_changes:
        pdf.check_page_break(60)
        pdf.section_title("Dose Change Timeline")

        # Embedded chart
        chart_buf = render_dose_timeline(dose_changes)
        if chart_buf:
            pdf.image(chart_buf, x=10, w=190)
            pdf.ln(3)

        # Text list
        pdf.set_font('Helvetica', '', 10)
        for c in dose_changes:
            date_str = c['date'].strftime("%Y-%m-%d")
            med_short = c['medication'].split(' (')[0]
            arrow = "+" if c['direction'] == 'increase' else "-"
            pdf.cell(0, 7, _latin1_safe(f"  {date_str}  {med_short}: {c['old_dose_str']} -> {c['new_dose_str']} ({arrow})"), 0, 1)
        pdf.ln(3)

    # ========== NUTRITION SUMMARY ==========
    target_protein = getattr(user, 'target_protein', None)
    add_food_summary_section(pdf, food_logs, target_protein)

    # ========== SIDE EFFECTS SECTION ==========
    pdf.check_page_break(60)
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
            severity_marker = {"mild": "o", "moderate": "*", "severe": "!"}.get(s.severity, "-")
            pdf.cell(0, 7, _latin1_safe(f"  {date_str} [{severity_marker}] {s.symptom.title()} ({s.severity})"), 0, 1)
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
