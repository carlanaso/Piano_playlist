from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QStackedWidget, QSlider, QFileDialog, QTableView
import pandas as pd

from PyQt6.QtCore import Qt, QAbstractTableModel
import mido
import os


import sys
from glob import glob

# Create a dictionary to store the audio files for each year
audio_files = {
    2004: '/maestro-v3.0.0/2004',
    2006: '/maestro-v3.0.0/2006',
    2008: '/maestro-v3.0.0/2008',
    2009: '/maestro-v3.0.0/2009',
    2011: '/maestro-v3.0.0/2011',
    2013: '/maestro-v3.0.0/2013',
    2014: '/maestro-v3.0.0/2014',
    2015: '/maestro-v3.0.0/2015',
    2017: '/maestro-v3.0.0/2017',
    2018: '/maestro-v3.0.0/2018'
}


metadata = '/maestro-v3.0.0.csv'

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

        playButton = QPushButton("Play")
        playButton.clicked.connect(self.playMidiFile)
        stopButton = QPushButton("Stop")
        pauseButton = QPushButton("Pause")
    
        hbox = QHBoxLayout()
        hbox.addWidget(playButton)
        hbox.addWidget(stopButton)
        hbox.addWidget(pauseButton)
        
        layout.addLayout(hbox)

    def changeValue(self, value):
        self.label.setText(f'Volume: {value}')

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
            mid = mido.MidiFile(midi_file_path)
            # You need to choose an available port
            with mido.open_output() as port:
                for msg in mid.play():
                    port.send(msg)
                    if msg.type == 'note_on':
                        print(f"Playing note: {msg.note}")
        except Exception as e:
            print(f"Error playing MIDI file: {e}")
            # Here, the audio playback will be asynchronous. You might want to keep track of the playback state.
            
        

    def closeEvent(self, event):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio_instance.terminate()
        super().closeEvent(event)

        
class SearchPage(QWidget):
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
            self.selected_midi_file = f"{self.dataset_path}{midi_filename}"
            print(f"Selected MIDI file: {self.selected_midi_file}")  # Debugging

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


    def on_selection_changed(self, selected, deselected):
    # Get the first selected index
    indexes = selected.indexes()
    if indexes:
        selected_row = indexes[0].row()
        # Get the 'midi_filename' and 'year' of the selected MIDI file
        midi_filename = self.df.iloc[selected_row]['midi_filename']
        year = self.df.iloc[selected_row]['year']
        # Construct the full path to the selected MIDI file
        self.selected_midi_file = os.path.join(audio_files[year], midi_filename)
        print(f"Selected MIDI file: {self.selected_midi_file}")  # Debugging





    def update_table_view(self, df):
        model = PandasTableModel(df)
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()

#class ChangeModePage(QWidget):
 #   def __init__(self):
   #      super().__init__()
     #    layout = QVBoxLayout(self)
       #  label = QLabel("This is the change mode site! You can choose to change between human and machine to play! Enjoy!")
        # self.machine_button = QPushButton("Machine Play")
 #        self.human_button = QPushButton("Human Play")
   #      hbox = QHBoxLayout()
     #    hbox.addWidget(self.machine_button)
       #  hbox.addWidget(self.human_button)
        # layout.addWidget(label)
         #layout.addLayout(hbox)#

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
        search_page = SearchPage(dataset_path, metadata)
        self.stacked_widget.addWidget(self.search_page)  # Pass metadata to SearchPage
         #self.stacked_widget.addWidget(ChangeModePage())

        main_layout.addWidget(sidebar, 1)
        main_layout.addWidget(self.stacked_widget, 4)

        self.setCentralWidget(main_widget)

        music_page = self.stacked_widget.widget(1)  # Get the MusicPage instance
        music_page.selected_midi_file = search_page.selected_midi_file  # Pass the selected MIDI file path to MusicPage

    def switch_page(self, page_index):
        self.stacked_widget.setCurrentIndex(page_index)

class CSVPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.open_csv_button = QPushButton("Open CSV")
        self.open_csv_button.clicked.connect(self.openFileDialog)
        
        self.table_view = QTableView()
        
        layout.addWidget(self.open_csv_button)
        layout.addWidget(self.table_view)
        
    def openFileDialog(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)", options=options)
        if filePath:
            self.loadCsv(filePath)
    
    def loadCsv(self, filePath):
        df = pd.read_csv(filePath)
        print(df.head())  # Add this line to check if the DataFrame is loaded correctly
        model = PandasTableModel(df)
        self.table_view.setModel(model)

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
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow(dataset_path, metadata)
    main_window.show()
    sys.exit(app.exec())
