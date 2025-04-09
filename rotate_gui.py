import sys
from PyQt5 import QtWidgets
from rotate_main import Rotator, GUIRotatorUI


class QtListWidgetWrapper:
    """
    An adapter class for PyQt5's QListWidget to fit the expected interface of GUIRotatorUI.
    """
    def __init__(self, list_widget: QtWidgets.QListWidget):
        self.list_widget = list_widget

    def clear(self):
        self.list_widget.clear()

    def addItem(self, item: str):
        self.list_widget.addItem(item)


def run_gui():
    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QMainWindow()
    window.setWindowTitle("Rotator GUI")
    window.resize(600, 400)

    # Create a QListWidget widget to display results
    list_widget = QtWidgets.QListWidget()
    window.setCentralWidget(list_widget)

    # Wrap the QListWidget with our adapter
    list_adapter = QtListWidgetWrapper(list_widget)

    # Instantiate the Rotator and run the image analysis
    rotator = Rotator(overwrite_files=False)
    rotations = rotator.analyze_images()

    # Create the GUI UI instance and display the results
    gui_ui = GUIRotatorUI(list_adapter)
    gui_ui.display_rotations(rotations)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()