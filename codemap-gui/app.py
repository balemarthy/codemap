import sys
from PySide6.QtWidgets import QApplication

from codemap_gui.backend.workspace_backend import WorkspaceBackend
from codemap_gui.presenter import CodeMapPresenter
from codemap_gui.views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    backend = WorkspaceBackend()
    view = MainWindow()
    presenter = CodeMapPresenter(view=view, backend=backend)
    presenter.start()

    view.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
