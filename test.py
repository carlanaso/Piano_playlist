from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QStackedWidget, QSlider, QFileDialog, QTableView
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
import pandas as pd
import mido
import os
import sys

class IntroductionPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        introduction_label = QLabel('Hello! My name is Carlana, one of the URSA research under Prof. Donnelly!')
        introduction_label.setWordWrap(True)
        layout.addWidget(introduction_label)
        self.setLayout(layout)

class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.midi_output_port = None
        self.mid = None

    def initUI(self):
        layout = QVBoxLayout(self)

        self.sld = QSlider(Qt.Orientation.Vertical)
        self.sld.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sld.setFixedSize(30, 100)
        self.sld.valueChanged.connect(self.changeValue)
        self.label = QLabel('Volume: 0')

        slider_hbox = QHBoxLayout()
        slider_hbox.addWidget(self.sld)
        slider_hbox.addWidget(self.label)
        layout.addLayout(slider_hbox)

        self.playButton = QPushButton("Play")
        self.playButton.clicked.connect(self.playMidiFile)
        self.stopButton = QPushButton("Stop")
        self.stopButton.clicked.connect(self.stopMidiFile)
        self.pauseButton = QPushButton("Pause")
        self.pauseButton.clicked.connect(self.pauseMidiFile)

        hbox = QHBoxLayout()
        hbox.addWidget(self.playButton)
        hbox.addWidget(self.stopButton)
        hbox.addWidget(self.pauseButton)

        layout.addLayout(hbox)

    def changeValue(self, value):
        self.label.setText(f'Volume: {value}')
        if self.mid:
            # Adjust volume of all MIDI messages
            for track in self.mid.tracks:
                for msg in track:
                    if msg.type in ('note_on', 'note_off'):
                        msg.velocity = int(value / 100 * 127)

    def playMidiFile(self):
        # Ensure that the selected_midi_file attribute is set by the selection changed method
        midi_file_path = self.selected_midi_file

        if midi_file_path is None:
            print("MIDI file has not been selected.")
            return

        if not os.path.exists(midi_file_path):
            print(f"MIDI file does not exist: {midi_file_path}")
            return

        try:
            # Load the MIDI file
            self.mid = mido.MidiFile(midi_file_path)
            # You need to choose an available port
            with mido.open_output() as port:
                for msg in self.mid.play():
                    port.send(msg)
                    if msg.type == 'note_on':
                        print(f"Playing note: {msg.note}")
        except Exception as e:
            print(f"Error playing MIDI file: {e}")
            # Here, the audio playback will be asynchronous. You might want to keep track of the playback state.

    def stopMidiFile(self):
        if self.mid:
            self.mid.close()  # Close the MIDI file
            self.mid = None

    def pauseMidiFile(self):
        # Pause playback by stopping the MIDI file
        self.stopMidiFile()

    def closeEvent(self, event):
        self.stopMidiFile()
        super().closeEvent(event)

class SearchPage(QWidget):
    midi_file_selected = pyqtSignal(str)  # Define a signal to emit the selected MIDI file path

    def __init__(self, dataset_path, metadata):
        super().__init__()
        self.dataset_path = dataset_path
        self.metadata = metadata

        self.df = pd.read_csv(metadata)  # Load the metadata CSV
        self.selected_midi_file = None  # To store the path of the selected MIDI file
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.textChanged.connect(self.on_search)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.on_search)

        self.table_view = QTableView(self)
        self.set_dataframe(self.df)  # Display the loaded DataFrame in the QTableView

        hbox = QHBoxLayout()
        hbox.addWidget(self.search_input)
        hbox.addWidget(self.search_button)

        layout.addLayout(hbox)
        layout.addWidget(self.table_view)

        # Connect table view selection change to a new method
        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
    # Get the first selected index
        indexes = selected.indexes()
        if indexes:
            selected_row = indexes[0].row()
            # Assuming 'midi_filename' column contains the MIDI file names
            midi_filename = self.df.iloc[selected_row]['midi_filename']
            self.selected_midi_file = os.path.join(self.dataset_path, midi_filename)
            # Emit a signal to inform other components (e.g., MusicPage) about the selected MIDI file
            self.midi_file_selected.emit(self.selected_midi_file)  # Emit this signal
            print(f"Selected MIDI file: {self.selected_midi_file}")  # Debugging

            # Open the WAV file with the default application
            wav_file_path = os.path.splitext(self.selected_midi_file)[0] + ".wav"
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(wav_file_path))
            except Exception as e:
                print(f"Error opening WAV file: {e}")

    def set_dataframe(self, df):
        """Call this method to set the DataFrame with your data."""
        self.df = df
        self.update_table_view(self.df)  # Initially show all data

    def on_search(self):
        query = self.search_input.text().lower()
        if query:
            # Create a boolean series for rows that match the query across all text columns
            condition = pd.concat([
                self.df[col].astype(str).str.lower().str.contains(query)
                for col in self.df.select_dtypes(include=[object, "string"]).columns
            ], axis=1).any(axis=1)
            filtered_df = self.df[condition]
            self.update_table_view(filtered_df)
        else:
            self.update_table_view(self.df)

    def update_table_view(self, df):
        model = PandasTableModel(df)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

class MainWindow(QMainWindow):
    def __init__(self, dataset_path, metadata):
        super().__init__()
        self.search_page = SearchPage(dataset_path, metadata)
        self.setWindowTitle("Main Application")
        self.setGeometry(300, 300, 600, 400)

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.metadata = metadata
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar.setStyleSheet("background-color: #808080;")

        introduction_button = QPushButton('Introduction')
        music_button = QPushButton('Music Setting')
        search_button = QPushButton('Search')
        change_mode_button = QPushButton('Change Mode')

        introduction_button.clicked.connect(lambda: self.switch_page(0))
        music_button.clicked.connect(lambda: self.switch_page(1))
        search_button.clicked.connect(lambda: self.switch_page(2))
        change_mode_button.clicked.connect(lambda: self.switch_page(3))

        sidebar_layout.addWidget(introduction_button)
        sidebar_layout.addWidget(music_button)
        sidebar_layout.addWidget(search_button)
        sidebar_layout.addWidget(change_mode_button)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(IntroductionPage())
        self.stacked_widget.addWidget(MusicPage())
        self.stacked_widget.addWidget(self.search_page)  # Pass metadata to SearchPage
        #self.stacked_widget.addWidget(ChangeModePage())

        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(self.stacked_widget, 4)

        self.setCentralWidget(main_widget)

        self.search_page.midi_file_selected.connect(self.set_music_page_midi_file)

    def switch_page(self, page_index):
        self.stacked_widget.setCurrentIndex(page_index)

    def set_music_page_midi_file(self, midi_file):
        music_page = self.stacked_widget.widget(1)
        music_page.selected_midi_file = midi_file

class PandasTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()  # Properly initialize the parent class
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):  # Corrected enum access
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:  # Corrected enum access
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # Corrected enum access
        if role == Qt.ItemDataRole.DisplayRole:  # Corrected enum access
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None

def organize_audio_files_by_year(dataset_path, metadata_path):
    df = pd.read_csv(metadata_path)
    audio_files = {}
    for _, row in df.iterrows():
        year = row['year']
        midi_filename = row['midi_filename']
        audio_files.setdefault(year, []).append(os.path.join(dataset_path, midi_filename))
    return audio_files

if __name__ == "__main__":
    dataset_path = 'C:/Users/carla/maestro-v3.0.0/'  # Adjust the dataset path accordingly
    metadata = 'C:/Users/carla/maestro-v3.0.0/maestro-v3.0.0.csv'  # Adjust the metadata path accordingly

    audio_files = organize_audio_files_by_year(dataset_path, metadata)

    app = QApplication(sys.argv)
    main_window = MainWindow(dataset_path, metadata)
    main_window.show()
    sys.exit(app.exec())
