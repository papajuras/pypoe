from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

_app: QApplication | None = None
_icon: QSystemTrayIcon | None = None


def _make_pixmap() -> QPixmap:
    pm = QPixmap(22, 22)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setBrush(QColor(255, 50, 50))
    p.setPen(QColor(255, 50, 50))
    p.drawEllipse(2, 2, 18, 18)
    p.end()
    return pm


def create(quit_cb, show_cb=None):
    global _app, _icon
    _app = QApplication([])
    _icon = QSystemTrayIcon(QIcon(_make_pixmap()))
    _icon.setToolTip("PoE Crafting Macro")
    menu = QMenu()
    if show_cb:
        menu.addAction("Show").triggered.connect(show_cb)
        menu.addSeparator()
    menu.addAction("Quit").triggered.connect(quit_cb)
    _icon.setContextMenu(menu)
    _icon.show()
    _app.exec()


def update_tooltip(text: str):
    if _icon:
        _icon.setToolTip(text)


def stop():
    if _app:
        _app.quit()
