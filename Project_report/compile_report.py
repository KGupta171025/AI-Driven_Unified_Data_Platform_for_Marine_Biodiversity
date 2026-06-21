import os
import re
import sys
import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Preformatted, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

# Global dictionary to store page numbers of headings across runs
heading_pages = {}
is_second_pass = False

class HeadingMarker(Flowable):
    """Marker to record the page number of a heading during document build."""
    def __init__(self, key):
        super().__init__()
        self.key = key

    def draw(self):
        # Record page number in the global registry
        page_num = self.canv._pageNumber
        heading_pages[self.key] = page_num

    def wrap(self, availWidth, availHeight):
        return 0, 0

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for two-pass page numbering and running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        # Save state for the second pass
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        # Cover page (page 1) has no header or footer
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Times-Roman", 10)
        self.setFillColor(colors.HexColor("#333333"))

        # Running Header (on all pages except cover)
        self.drawString(108, 770, "AI-Driven Unified Data Platform for Marine Biodiversity")
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.setLineWidth(0.5)
        self.line(108, 762, 523, 762)

        # Footer Page Number
        page_num = self._pageNumber
        ch1_page = heading_pages.get("CHAPTER 1", 8)  # Fallback to page 8

        if page_num < ch1_page:
            # Roman numerals for front matter (starting from page 2 as II)
            roman_nums = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]
            if page_num < len(roman_nums):
                num_str = roman_nums[page_num]
            else:
                num_str = str(page_num)
        else:
            # Arabic numerals starting from Chapter 1 (page ch1_page becomes page 1)
            num_str = str(page_num - ch1_page + 1)

        self.drawCentredString(306, 40, num_str)
        self.restoreState()

def parse_inline_markdown(text):
    """Convert basic markdown bold/italic/code tags to ReportLab paragraph XML tags."""
    # Convert <br> to <br/>
    text = text.replace("<br>", "<br/>")
    # Convert bold-italic
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", text)
    # Convert bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Convert italic
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    # Convert inline code
    text = re.sub(r"`(.*?)`", r'<font name="Courier">\1</font>', text)
    # Convert math LaTeX brackets (e.g. \(B/B_{MSY}\)) to plain text since we don't have LaTeX engine in reportlab
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    text = re.sub(r"\$(.*?)\$", r"\1", text)
    return text

def parse_markdown_table(lines, table_style, cell_style, header_style):
    """Parse a markdown table block and return a ReportLab Table flowable."""
    data = []
    # Identify column alignment or separator details
    raw_rows = []
    for line in lines:
        clean_l = line.strip()
        if not clean_l:
            continue
        # Skip separator rows like |:---| or | :--- | :--- |
        if re.match(r"^\|[\s\-\:\#\|]+$", clean_l):
            continue
        # Split cells
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if cells:
            raw_rows.append(cells)

    if not raw_rows:
        return None

    # Parse formatting in each cell
    is_lof = False
    if raw_rows and len(raw_rows[0]) >= 3 and "figure" in raw_rows[0][0].lower():
        is_lof = True

    for r_idx, row in enumerate(raw_rows):
        formatted_row = []
        for c_idx, cell in enumerate(row):
            cell_txt = parse_inline_markdown(cell)
            if r_idx > 0 and is_lof and c_idx == 2 and is_second_pass:
                fig_num = raw_rows[r_idx][0].strip()
                key_map = {
                    "4.1": "4.1",
                    "4.2": "4.1",  # Level 1 is in 4.1 section
                    "4.3": "4.2",  # ERD is 4.2
                    "4.4": "4.3",  # Flowchart is 4.3
                    "4.5": "4.5",  # Sequence is 4.5
                    "4.6": "4.6",  # Activity is 4.6
                    "4.7": "4.7",  # Class is 4.7
                }
                h_key = key_map.get(fig_num)
                p_num = heading_pages.get(h_key) if h_key else None
                if p_num:
                    ch1_page = heading_pages.get("CHAPTER 1", 10)
                    cell_txt = str(p_num - ch1_page + 1)
            
            if r_idx == 0:
                # Header row
                formatted_row.append(Paragraph(f"<b>{cell_txt}</b>", header_style))
            else:
                # Data row
                formatted_row.append(Paragraph(cell_txt, cell_style))
        data.append(formatted_row)

    col_count = len(data[0])
    # Define column widths based on column count to fit within page width (415 pt)
    if col_count == 2:
        col_widths = [120, 295]
    elif col_count == 3:
        # Check if first column represents figure number
        if "fig" in raw_rows[0][0].lower() or "no" in raw_rows[0][0].lower():
            col_widths = [80, 275, 60]
        else:
            col_widths = [120, 145, 150]
    elif col_count == 4:
        col_widths = [100, 105, 105, 105]
    else:
        col_widths = [415.0 / col_count] * col_count

    t = Table(data, colWidths=col_widths)
    # Apply beautiful TableStyle
    t_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")), # Slate-800 header
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")), # Light slate border
    ])
    # Alternating row background colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor("#f8fafc"))
    t.setStyle(t_style)
    return t

def build_pdf(md_path, pdf_path):
    global is_second_pass
    print(f"Reading markdown file: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split report by pagebreaks
    sections = content.split("\\pagebreak")
    
    # Setup document template
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=108,  # 1.5 inch for binding
        rightMargin=72,  # 1.0 inch
        topMargin=72,    # 1.0 inch
        bottomMargin=72  # 1.0 inch
    )

    # Setup styles
    styles = getSampleStyleSheet()
    
    # Custom academic styles using Times-Roman (standard)
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    institution_style = ParagraphStyle(
        'InstitutionStyle',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        spaceAfter=8
    )

    chapter_style = ParagraphStyle(
        'ChapterHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceBefore=15,
        spaceAfter=15
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=15,
        spaceAfter=8
    )

    subsection_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Normal'],
        fontName='Times-BoldItalic',
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,  # 1.5 line spacing
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )

    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        leftIndent=24,
        spaceAfter=6
    )

    code_body_style = ParagraphStyle(
        'CodeBody',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=11,
        leftIndent=12,
        spaceAfter=10
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=13
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.white
    )

    story = []

    # Iterate through page break sections
    for sec_idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # Add page break between sections (except the first page)
        if sec_idx > 0:
            story.append(PageBreak())

        # If it is the Cover Page (first section)
        if sec_idx == 0:
            # Render cover page layout with exact centering and custom spacers
            lines = [l.strip() for l in section.split("\n")]
            story.append(Spacer(1, 20))
            
            i = 0
            while i < len(lines):
                line = lines[i]
                if not line:
                    i += 1
                    continue
                if line.startswith("# "):
                    title_text = line[2:].strip("“\"”")
                    story.append(Paragraph(f"<b>“{title_text}”</b>", title_style))
                    story.append(Spacer(1, 25))
                elif line == "---":
                    story.append(Spacer(1, 15))
                elif line.startswith("- "):
                    # submitted by list item
                    bullet_txt = parse_inline_markdown(line[2:])
                    story.append(Paragraph(bullet_txt, subtitle_style))
                else:
                    para_txt = parse_inline_markdown(line)
                    # Custom formatting for specific section labels
                    if "submitted by" in line.lower() or "under the guidance" in line.lower():
                        story.append(Spacer(1, 15))
                        story.append(Paragraph(f"<b>{para_txt}</b>", subtitle_style))
                    elif "department of" in line.lower() or "oriental institute" in line.lower() or "bhopal" in line.lower() or "aug-dec" in line.lower():
                        # institutional footer at bottom
                        story.append(Paragraph(para_txt.strip("#* "), institution_style))
                    else:
                        # Clean up submission note format
                        if "in partial fulfillment" in para_txt.lower() or "b.tech in" in para_txt.lower():
                            para_txt = para_txt.replace("in partial fulfillment of the requirements for the award of the degree of B.TECH IN CSE-DATA SCIENCE", "A Minor Project Report submitted to the<br/><b>RAJIV GANDHI PROUDYOGIKI VISHWAVIDYALAYA, BHOPAL</b><br/><br/>in partial fulfillment of the requirements for the award of the degree of<br/><b>BACHELOR OF TECHNOLOGY</b><br/>in<br/><b>CSE-DATA SCIENCE</b>")
                        story.append(Paragraph(para_txt, subtitle_style))
                        story.append(Spacer(1, 10))
                i += 1
            continue

        # Parse Certificate, Table of Contents, Chapters, etc.
        if "TABLE OF CONTENTS" in section.upper():
            toc_lines = section.split("\n")
            toc_data = []
            
            # Custom styles for TOC
            toc_page_style = ParagraphStyle(
                'TOCPageNum',
                parent=styles['Normal'],
                fontName='Times-Bold',
                fontSize=11,
                alignment=TA_RIGHT
            )
            toc_chapter_style = ParagraphStyle(
                'TOCChapter',
                parent=styles['Normal'],
                fontName='Times-Bold',
                fontSize=11,
                leading=15,
                leftIndent=0
            )
            toc_section_style = ParagraphStyle(
                'TOCSection',
                parent=styles['Normal'],
                fontName='Times-Roman',
                fontSize=11,
                leading=15,
                leftIndent=15
            )

            story.append(HeadingMarker("TABLE OF CONTENTS"))
            story.append(Paragraph("TABLE OF CONTENTS", chapter_style))
            story.append(Spacer(1, 15))

            for line in toc_lines:
                cleaned_line = line.strip()
                if not cleaned_line or cleaned_line.startswith("#") or "TABLE OF CONTENTS" in cleaned_line.upper():
                    continue
                
                # Check if it is a list item
                if cleaned_line.startswith("- ") or cleaned_line.startswith("* "):
                    # Extract list text
                    raw_text = cleaned_line.split("- ", 1)[1].strip() if "- " in cleaned_line else cleaned_line.split("* ", 1)[1].strip()
                    is_sub = line.startswith("  ") or line.startswith("\t")
                    
                    page_val = ""
                    # Clean up raw_text to extract lookup key
                    key_text = raw_text.replace("**", "").replace("*", "").strip()
                    
                    # Match chapters: "01 INTRODUCTION" -> "CHAPTER 1"
                    chap_match = re.match(r"^0?([1-9]|10)\s+(.*)$", key_text)
                    if chap_match:
                        chap_num = int(chap_match.group(1))
                        page_num = heading_pages.get(f"CHAPTER {chap_num}")
                    else:
                        # Match sections: "1.1 Objective" -> "1.1"
                        sec_match = re.match(r"^([0-9]+\.[0-9]+)\b", key_text)
                        if sec_match:
                            page_num = heading_pages.get(sec_match.group(1))
                        else:
                            page_num = heading_pages.get(key_text.upper())
                            
                    if page_num:
                        ch1_page = heading_pages.get("CHAPTER 1", 10)
                        if page_num < ch1_page:
                            roman_nums = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]
                            if page_num < len(roman_nums):
                                page_val = roman_nums[page_num]
                            else:
                                page_val = str(page_num)
                        else:
                            page_val = str(page_num - ch1_page + 1)
                    else:
                        page_val = ""
                        
                    # Build cell paragraphs
                    cell_text = parse_inline_markdown(raw_text)
                    if is_sub:
                        p_title = Paragraph(cell_text, toc_section_style)
                        p_page = Paragraph(page_val, toc_section_style)
                    else:
                        p_title = Paragraph(cell_text, toc_chapter_style)
                        p_page = Paragraph(f"<b>{page_val}</b>", toc_page_style)
                        
                    toc_data.append([p_title, p_page])
            
            if toc_data:
                t_toc = Table(toc_data, colWidths=[360, 55])
                t_toc.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(t_toc)
            continue

        lines = section.split("\n")
        in_code_block = False
        code_block_lines = []
        in_table = False
        table_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Handle Code Blocks
            if line.strip().startswith("```"):
                if in_code_block:
                    in_code_block = False
                    code_text = "\n".join(code_block_lines)
                    story.append(Preformatted(code_text, code_body_style))
                    code_block_lines = []
                else:
                    in_code_block = True
                i += 1
                continue

            if in_code_block:
                code_block_lines.append(line)
                i += 1
                continue

            # Handle Tables
            if line.strip().startswith("|") and not in_table:
                # Peek to check if it represents separator row
                if i + 1 < len(lines) and "|" in lines[i+1] and ("---" in lines[i+1] or ":" in lines[i+1]):
                    in_table = True
                    table_lines = [line, lines[i+1]]
                    i += 2
                    continue
                else:
                    # Not a structured table, parse as normal paragraph
                    pass

            if in_table:
                if line.strip().startswith("|"):
                    table_lines.append(line)
                    i += 1
                    continue
                else:
                    in_table = False
                    # Parse and append the table flowable
                    t_flowable = parse_markdown_table(table_lines, styles, table_cell_style, table_header_style)
                    if t_flowable:
                        story.append(t_flowable)
                        story.append(Spacer(1, 10))
                    table_lines = []
                    # Do not skip this line, fall through to process it as normal text

            # Clean line
            cleaned_line = line.strip()
            if not cleaned_line:
                i += 1
                continue

            # Handle headers
            if cleaned_line.startswith("# "):
                # Cover page elements are handled separately, so this is inside chapters
                title = cleaned_line[2:]
                key = title.strip("*# ")
                story.append(HeadingMarker(key))
                story.append(Paragraph(title, title_style))
                story.append(Spacer(1, 10))
            elif cleaned_line.startswith("## "):
                title = cleaned_line[3:]
                # Clean title for TOC matching
                key = title.strip("*# ").upper()
                if "CHAPTER" in key:
                    # Insert chapter start marker
                    chap_match = re.match(r"(CHAPTER\s+\d+)", key, re.IGNORECASE)
                    if chap_match:
                        story.append(HeadingMarker(chap_match.group(1).upper()))
                else:
                    story.append(HeadingMarker(key))
                
                story.append(Paragraph(title, chapter_style))
                story.append(Spacer(1, 12))
            elif cleaned_line.startswith("### "):
                title = cleaned_line[4:]
                key = title.strip("*# ")
                # Strip section number if exists (e.g. 1.1 Objective -> 1.1)
                sec_match = re.match(r"^([0-9]+\.[0-9]+)\b", key)
                if sec_match:
                    story.append(HeadingMarker(sec_match.group(1)))
                else:
                    story.append(HeadingMarker(key))
                
                story.append(Paragraph(title, section_style))
                story.append(Spacer(1, 8))
            elif cleaned_line.startswith("#### "):
                title = cleaned_line[5:]
                story.append(Paragraph(title, subsection_style))
                story.append(Spacer(1, 6))
            # Handle bullet items
            elif cleaned_line.startswith("- ") or cleaned_line.startswith("* "):
                bullet_txt = parse_inline_markdown(cleaned_line[2:])
                story.append(Paragraph(f"&bull; {bullet_txt}", bullet_style))
            # Handle numbered list items
            elif re.match(r"^\d+\.\s+", cleaned_line):
                num_txt = re.sub(r"^\d+\.\s+", "", cleaned_line)
                num_prefix = re.match(r"^(\d+\.)\s+", cleaned_line).group(1)
                formatted_txt = parse_inline_markdown(num_txt)
                story.append(Paragraph(f"{num_prefix} {formatted_txt}", bullet_style))
            # Horizontal rule divider
            elif cleaned_line == "---":
                pass
            # Standard paragraph body
            else:
                # Let's accumulate paragraphs until empty line or block ends
                paragraph_lines = [cleaned_line]
                while i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].strip().startswith("#") and not lines[i+1].strip().startswith("-") and not lines[i+1].strip().startswith("*") and not lines[i+1].strip().startswith("|") and not lines[i+1].strip().startswith("```") and not re.match(r"^\d+\.\s+", lines[i+1].strip()) and lines[i+1].strip() != "---":
                    i += 1
                    paragraph_lines.append(lines[i].strip())
                
                para_txt = " ".join(paragraph_lines)
                para_txt = parse_inline_markdown(para_txt)
                
                story.append(Paragraph(para_txt, body_style))
                story.append(Spacer(1, 6))
            i += 1

    # Compile the document using our custom canvas
    print(f"Building PDF to: {pdf_path} (Pass {'2' if is_second_pass else '1'})")
    doc.build(story, canvasmaker=NumberedCanvas)

def run_compilation_workflow():
    global is_second_pass
    md_path = r"d:\Code_Files\Projects\AI-Driven_Unified_Data_Platform_for_Marine_Biodiversity\Project_report\final_report.md"
    pdf_path = r"d:\Code_Files\Projects\AI-Driven_Unified_Data_Platform_for_Marine_Biodiversity\Project_report\minor_report_final.pdf"
    
    # Pass 1: Build the PDF to populate heading_pages
    is_second_pass = False
    build_pdf(md_path, pdf_path)
    
    # Print the resolved heading pages
    print("Resolved Heading Page Numbers:")
    print(json.dumps(heading_pages, indent=2))
    
    # Pass 2: Re-run compilation to get correct Roman/Arabic page numbering based on resolved Chapter 1 page
    is_second_pass = True
    build_pdf(md_path, pdf_path)
    print("PDF Generation Workflow completed successfully.")

if __name__ == "__main__":
    run_compilation_workflow()
