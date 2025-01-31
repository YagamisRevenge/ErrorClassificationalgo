import sys
import os
import csv
from PyQt5 import QtCore, QtGui, QtWidgets


ERROR_COLUMNS = [
    "Grammar",
    "Factuality",
    "Hallucination",
    "Redundancy",
    "Repetition",
    "Missing Step",
    "Coherency",
    "Commonsense",
    "Arithmetic"
]

REQUIRED_COLUMNS = [
    "question",
    "true_answer",
    "predicted_answer_full",
    "is_correct"
] + ERROR_COLUMNS

ERROR_QUESTION_TEXTS = {
    "Grammar": """**Grammar Error**
**CSV Question**:
"Does this step contain faulty, unconventional, or controversial grammar usage? In other words, does the language in this step sound unnatural?"
""",
    "Factuality": """**Factuality Error**
**CSV Question**:
"Does this step contain information that contradicts the context? Note that the step should be relevant to the context in general (unlike hallucination), but information about objects (i.e. quantity, characteristics) or a personal named entity does not match information provided in the question. Note that if this step contradicts context/question BECAUSE of the errors in the previous step, it is NOT a factual error. Factual error is an error when the information provided in the context was explicitly changed."
""",
    "Hallucination": """**Hallucination Error**
**CSV Question**:
"Does this step build mostly on information that is not provided in the problem statement, and is irrelevant or wrong?"
""",
    "Redundancy": """**Redundancy**
**CSV Question**:
"Does this step contain factual (i.e. consistent with context) information, but the whole step is not required to answer the question asked?"
""",
    "Repetition": """**Repetition**
**CSV Question**:
"Does this step paraphrase information already mentioned in previous steps and can be dropped from the chain (i.e., the whole step is not required to answer the final question, because it does not bring any new information)? Note that the answer-step, that summarizes all previous steps (for ex., 'So the final answer is 3', or 'The answer is yes') does NOT count as repetition."
""",
    "Missing Step": """**Missing Step**
**CSV Question**:
"Is the content of the generated reasoning incomplete and lacks required information to produce the correct answer? If these missing steps are added, the model could produce the correct answer, meaning that the chain contains several relevant and mostly correct steps, and produced an answer based on those while it should have made an extra effort."
""",
    "Coherency": """**Coherency**
**CSV Question**:
"Do steps contradict each other or do not follow a cohesive story? I.e., you can explicitly show that from Steps i and k follows step not j (for example: A has 3 apples, B has 2. How much more apples does A have? Chain: A has 3 apples. So A has 3-2=1 apples more. The answer is 3. - Conclusion contradicts Step 2)."
""",
    "Commonsense": """**Commonsense Error**
**CSV Question**:
"Does this step produce an error in relations that should be known from general knowledge about the world (i.e., how to compute velocity, how many inches in one foot, all ducks are birds, etc.)? Note that this general knowledge should NOT be provided in the context or question."
""",
    "Arithmetic": """**Arithmetic Error**
**CSV Question**:
"Does this step contain an error in a math equation? Note that you should consider only the current step in isolation; if the error was produced in previous steps and the wrong number is carried over, that does not count."
"""
}

class CSVTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data=None, headers=None, parent=None):
        super().__init__(parent)
        self._data = data if data else []
        self._headers = headers if headers else []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            header_name = self._headers[col]
            return self._data[row].get(header_name, "")
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._headers[section]
            else:
                return str(section)
        return None


    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        # Read-only cells
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def getDataList(self):
        return self._data

    def getHeaders(self):
        return self._headers



class DetailedClassificationWindow(QtWidgets.QDialog):
    def __init__(self, initial_values=None, row_number=None, total_rows=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Classification Help - Row {row_number}/{total_rows}")
        self.setMinimumSize(600, 400)

        self.row_number = row_number
        self.total_rows = total_rows

        if initial_values is not None:
            self.responses = dict(initial_values)  
        else:
            self.responses = {col: "No" for col in ERROR_COLUMNS}

        self.error_keys = ERROR_COLUMNS[:]
        self.current_idx = 0

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        self.question_label = QtWidgets.QTextBrowser()
        self.question_label.setOpenExternalLinks(False)
        self.question_label.setOpenLinks(False)
        main_layout.addWidget(self.question_label, stretch=1)


        self.answer_combo = QtWidgets.QComboBox()
        self.answer_combo.addItems(["No", "Yes"])
        combo_layout = QtWidgets.QHBoxLayout()
        combo_layout.addWidget(QtWidgets.QLabel("Answer:"))
        combo_layout.addWidget(self.answer_combo)
        main_layout.addLayout(combo_layout)


        btn_layout = QtWidgets.QHBoxLayout()
        self.next_btn = QtWidgets.QPushButton("Next")
        self.next_btn.clicked.connect(self.next_question)
        btn_layout.addWidget(self.next_btn)

        self.finish_btn = QtWidgets.QPushButton("Finish")
        self.finish_btn.clicked.connect(self.finish)
        btn_layout.addWidget(self.finish_btn)

        main_layout.addLayout(btn_layout)


        self.load_current_question()

    def load_current_question(self):
        if 0 <= self.current_idx < len(self.error_keys):
            err_key = self.error_keys[self.current_idx]
            text = ERROR_QUESTION_TEXTS.get(err_key, f"{err_key} question not found.")
            self.question_label.setHtml(text)

            val = self.responses.get(err_key, "No")
            if val not in ["Yes", "No"]:
                val = "No"
            self.answer_combo.setCurrentText(val)
        else:
            self.close()

    def next_question(self):

        if 0 <= self.current_idx < len(self.error_keys):
            err_key = self.error_keys[self.current_idx]
            self.responses[err_key] = self.answer_combo.currentText()


        self.current_idx += 1
        if self.current_idx >= len(self.error_keys):
            QtWidgets.QMessageBox.information(self, "Done", "All 9 questions answered.")
            self.accept() 
        else:
            self.load_current_question()

    def finish(self):

        if 0 <= self.current_idx < len(self.error_keys):
            err_key = self.error_keys[self.current_idx]
            self.responses[err_key] = self.answer_combo.currentText()
        self.accept()  

    def get_responses(self):
        return self.responses



class RowOverviewWindow(QtWidgets.QDialog):
    def __init__(self, csv_data,row_number = 1, parent=None):
        super().__init__(parent)
        self.csv_data = csv_data
        self.current_index = row_number - 1

        self.row_label = QtWidgets.QLabel(f"Row {self.current_index + 1} of {len(self.csv_data)}")
        self.row_label.setAlignment(QtCore.Qt.AlignCenter)

        self.setWindowTitle(f"Row Overview - Row {self.current_index+1}/{len(self.csv_data)}")
        self.setMinimumSize(900, 600)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        main_layout.addWidget(self.row_label)

        # 3 text areas
        self.question_edit = QtWidgets.QPlainTextEdit()
        self.question_edit.setReadOnly(True)

        self.true_answer_edit = QtWidgets.QPlainTextEdit()
        self.true_answer_edit.setReadOnly(True)

        self.pred_answer_edit = QtWidgets.QPlainTextEdit()
        self.pred_answer_edit.setReadOnly(True)

        # Labels
        lbl_question = QtWidgets.QLabel("Question:")
        lbl_true = QtWidgets.QLabel("GSM8K (true_answer):")
        lbl_pred = QtWidgets.QLabel("Model's Answer (predicted_answer_full):")

        main_layout.addWidget(lbl_question)
        main_layout.addWidget(self.question_edit, stretch=1)

        main_layout.addWidget(lbl_true)
        main_layout.addWidget(self.true_answer_edit, stretch=1)

        main_layout.addWidget(lbl_pred)
        main_layout.addWidget(self.pred_answer_edit, stretch=1)

        # Comboboxes for 9 errors
        error_groupbox = QtWidgets.QGroupBox("Error Classifications (Yes/No)")
        form_layout = QtWidgets.QFormLayout()
        error_groupbox.setLayout(form_layout)
        self.error_combos = {}
        for col in ERROR_COLUMNS:
            combo = QtWidgets.QComboBox()
            combo.addItems(["No", "Yes"])
            form_layout.addRow(col + ":", combo)
            self.error_combos[col] = combo
        main_layout.addWidget(error_groupbox)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()

        self.detail_btn = QtWidgets.QPushButton("Open Detailed Classification")
        self.detail_btn.clicked.connect(self.open_detailed_classification)
        btn_layout.addWidget(self.detail_btn)

        self.prev_btn = QtWidgets.QPushButton("Previous Row")
        self.prev_btn.clicked.connect(self.save_and_previous_row)
        btn_layout.addWidget(self.prev_btn)

        self.next_btn = QtWidgets.QPushButton("Next Row")
        self.next_btn.clicked.connect(self.save_and_next_row)
        btn_layout.addWidget(self.next_btn)

        self.finish_btn = QtWidgets.QPushButton("Finish All")
        self.finish_btn.clicked.connect(self.finish_all)
        btn_layout.addWidget(self.finish_btn)

        main_layout.addLayout(btn_layout)

        # Load first row
        self.load_row_into_ui(self.current_index)

    def load_row_into_ui(self, index):
        if index < 0 or index >= len(self.csv_data):
            return
        
        self.current_index = index
        row = self.csv_data[index]
        question_text = row.get("question", "")
        true_text = row.get("true_answer", "")
        pred_text = row.get("predicted_answer_full", "")

        self.question_edit.setPlainText(question_text)
        self.true_answer_edit.setPlainText(true_text)
        self.pred_answer_edit.setPlainText(pred_text)

        self.setWindowTitle(f"Row Overview - Row {self.current_index + 1}/{len(self.csv_data)}")
        self.row_label.setText(f"Row {self.current_index + 1} of {len(self.csv_data)}")

        is_correct = row.get("is_correct", "").strip().lower()
        if is_correct == "true":
            # Lock combos to "No"
            for col in ERROR_COLUMNS:
                self.error_combos[col].setCurrentText("No")
                self.error_combos[col].setEnabled(False)
            self.detail_btn.setEnabled(False)
        else:
            self.detail_btn.setEnabled(True)
            for col in ERROR_COLUMNS:
                self.error_combos[col].setEnabled(True)
                val = row.get(col, "")
                if val not in ["Yes", "No"]:
                    val = "No"
                self.error_combos[col].setCurrentText(val)

    def open_detailed_classification(self):
        if self.current_index < 0 or self.current_index >= len(self.csv_data):
            return
        row = self.csv_data[self.current_index]
        is_correct = row.get("is_correct", "").strip().lower()
        if is_correct == "true":
            QtWidgets.QMessageBox.information(self, "Skipped", "This row is correct. No classification needed.")
            return

        current_answers = {}
        for col in ERROR_COLUMNS:
            current_answers[col] = self.error_combos[col].currentText()

        dialog = DetailedClassificationWindow(initial_values=current_answers,row_number=self.current_index+1, total_rows=len(self.csv_data), parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            final_responses = dialog.get_responses()
            for col in ERROR_COLUMNS:
                self.error_combos[col].setCurrentText(final_responses[col])

    def save_current_row(self):
        if 0 <= self.current_index < len(self.csv_data):
            row = self.csv_data[self.current_index]
            is_correct = row.get("is_correct", "").strip().lower()
            if is_correct == "true":
                for col in ERROR_COLUMNS:
                    row[col] = "No"
            else:
                for col in ERROR_COLUMNS:
                    row[col] = self.error_combos[col].currentText()

    def save_and_next_row(self):
        self.save_current_row()
        if self.current_index + 1 < len(self.csv_data):
            self.current_index += 1
            self.load_row_into_ui(self.current_index)
        else:
            QtWidgets.QMessageBox.information(self, "Done", "No more rows to annotate.")
            self.close()

    def save_and_previous_row(self):
        self.save_current_row()
        if self.current_index > 0:
            self.current_index -= 1
            self.load_row_into_ui(self.current_index)
        else:
            QtWidgets.QMessageBox.information(self, "At First Row", "No previous row available.")

    def finish_all(self):
        self.save_current_row()
        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Reviewer (Multi-Window) - Prev/Next")
        self.resize(1200, 700)

        # Central Widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Button bar
        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.load_btn = QtWidgets.QPushButton("Load CSV")
        self.load_btn.clicked.connect(self.load_csv)
        btn_layout.addWidget(self.load_btn)

        self.annotate_btn = QtWidgets.QPushButton("Annotate Rows")
        self.annotate_btn.clicked.connect(self.annotate_rows)
        self.annotate_btn.setEnabled(False)
        btn_layout.addWidget(self.annotate_btn)

        self.save_btn = QtWidgets.QPushButton("Save CSV")
        self.save_btn.clicked.connect(self.save_csv)
        self.save_btn.setEnabled(False)
        btn_layout.addWidget(self.save_btn)

        # TableView
        self.table_view = QtWidgets.QTableView()
        main_layout.addWidget(self.table_view, stretch=1)

        self.model = None
        self.csv_file_path = None

    def load_csv(self):
        dlg = QtWidgets.QFileDialog(self)
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        file_path, _ = dlg.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames

                for col in ERROR_COLUMNS:
                    if col not in headers:
                        headers.append(col)

                missing = [c for c in REQUIRED_COLUMNS if c not in headers]
                if missing:
                    QtWidgets.QMessageBox.warning(
                        self, "Missing Columns",
                        f"CSV is missing required columns:\n{missing}"
                    )
                    return

                data = list(reader)

                for row in data:
                    for col in ERROR_COLUMNS:
                        if col not in row:
                            row[col] = "No"


            self.model = CSVTableModel(data, headers)
            self.table_view.setModel(self.model)
            self.table_view.resizeColumnsToContents()

            self.csv_file_path = file_path
            self.annotate_btn.setEnabled(True)
            self.save_btn.setEnabled(True)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load CSV:\n{e}")

    def annotate_rows(self):
        if not self.model:
            return
        data = self.model.getDataList()
        if not data:
            QtWidgets.QMessageBox.information(self, "No Data", "No rows to annotate.")
            return

        dialog = RowOverviewWindow(data, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.table_view.reset()
        else:
            self.table_view.reset()

    def save_csv(self):
        if not self.model or not self.csv_file_path:
            QtWidgets.QMessageBox.information(self, "No Data", "No CSV loaded.")
            return

        os.makedirs("results", exist_ok=True)
        orig_name = os.path.basename(self.csv_file_path)
        out_name = f"annotated_{orig_name}"
        out_path = os.path.join("results", out_name)

        data = self.model.getDataList()
        headers = self.model.getHeaders()

        for col in ERROR_COLUMNS:
            if col not in headers:
                headers.append(col)

        try:
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in data:
                    for col in ERROR_COLUMNS:
                        if col not in row:
                            row[col] = "No"
                    writer.writerow(row)

            QtWidgets.QMessageBox.information(self, "Saved", f"CSV saved to: {out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
