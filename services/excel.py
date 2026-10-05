import os
import pandas as pd

from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


# ==================================================
# EXCEL EXPORT
# ==================================================

def save_excel(leads, keyword):

    # --------------------------------------------------
    # Create output folder
    # --------------------------------------------------

    output_folder = "output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # --------------------------------------------------
    # Create filename
    # --------------------------------------------------

    filename = (
        keyword
        .replace(" ", "_")
        .lower()
    )

    file_path = os.path.join(
        output_folder,
        f"{filename}.xlsx"
    )

    # --------------------------------------------------
    # Convert leads to DataFrame
    # --------------------------------------------------

    df = pd.DataFrame(leads)

    # --------------------------------------------------
    # Export basic Excel
    # --------------------------------------------------

    df.to_excel(
        file_path,
        index=False
    )

    # ==================================================
    # OPEN EXCEL FOR FORMATTING
    # ==================================================

    workbook = load_workbook(file_path)

    worksheet = workbook.active

    # ==================================================
    # HEADER STYLE
    # ==================================================

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF"
    )

    for cell in worksheet[1]:

        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    # ==================================================
    # FIND COLUMN POSITIONS
    # ==================================================

    columns = {}

    for cell in worksheet[1]:

        columns[cell.value] = cell.column

    # ==================================================
    # HIGHLIGHT MISSING DATA
    # ==================================================

    missing_fill = PatternFill(
        fill_type="solid",
        fgColor="FFF2CC"
    )

    # Strong warning fill for incomplete data
    incomplete_fill = PatternFill(
        fill_type="solid",
        fgColor="FCE4D6"
    )

    # ==================================================
    # PROCESS EACH LEAD
    # ==================================================

    for row in range(2, worksheet.max_row + 1):

        # ----------------------------------------------
        # Get data status
        # ----------------------------------------------

        data_status_column = columns.get(
            "data_status"
        )

        data_status = ""

        if data_status_column:

            data_status = worksheet.cell(
                row=row,
                column=data_status_column
            ).value

        # ----------------------------------------------
        # Highlight incomplete row status
        # ----------------------------------------------

        if data_status == "INCOMPLETE":

            if data_status_column:

                worksheet.cell(
                    row=row,
                    column=data_status_column
                ).fill = incomplete_fill

                worksheet.cell(
                    row=row,
                    column=data_status_column
                ).font = Font(
                    bold=True
                )

        # ----------------------------------------------
        # Highlight missing fields
        # ----------------------------------------------

        missing_columns = [
            "phone",
            "website",
            "address"
        ]

        for field in missing_columns:

            column_number = columns.get(
                field
            )

            if not column_number:
                continue

            cell = worksheet.cell(
                row=row,
                column=column_number
            )

            value = cell.value

            # Empty / missing value
            if value is None or str(value).strip() == "":

                cell.fill = missing_fill

                cell.value = "MISSING"

                cell.font = Font(
                    bold=True
                )

    # ==================================================
    # AUTO COLUMN WIDTH
    # ==================================================

    for column_cells in worksheet.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            try:

                if cell.value is not None:

                    length = len(
                        str(cell.value)
                    )

                    if length > max_length:
                        max_length = length

            except Exception:
                pass

        # Limit width
        worksheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 2,
            50
        )

    # ==================================================
    # FREEZE HEADER
    # ==================================================

    worksheet.freeze_panes = "A2"

    # ==================================================
    # FILTER
    # ==================================================

    worksheet.auto_filter.ref = (
        worksheet.dimensions
    )

    # ==================================================
    # SAVE
    # ==================================================

    workbook.save(file_path)

    print(
        f"Excel saved: {file_path}"
    )