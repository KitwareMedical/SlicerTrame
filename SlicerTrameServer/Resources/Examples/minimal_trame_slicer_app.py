"""
Minimal example of starting a trame-slicer server for testing and integration purposes.

For a more complete example, please take a look at : https://github.com/KitwareMedical/trame-slicer/blob/main/examples/medical_viewer_app.py
"""

from trame.app import get_server
from trame.decorators import TrameApp, change
from trame.widgets import vuetify3
from trame_client.widgets.html import Div
from trame_vuetify.ui.vuetify3 import SinglePageLayout

from trame_slicer.core import LayoutManager, SlicerApp
from trame_slicer.rca_view import register_rca_factories


@TrameApp()
class MyTrameSlicerApp:
    def __init__(self, server=None):
        self._server = get_server(server, client_type="vue3")
        self._server.state.setdefault("file_loading_busy", False)

        self._slicer_app = SlicerApp()

        register_rca_factories(self._slicer_app.view_manager, self._server)

        self._layout_manager = LayoutManager(
            self._slicer_app.scene,
            self._slicer_app.view_manager,
            self._server.ui.layout_grid,
        )

        self._layout_manager.register_layout_dict(LayoutManager.default_grid_configuration())

        self._build_ui()

        default_layout = "Axial Primary"
        self.server.state.setdefault("current_layout_name", default_layout)
        self._layout_manager.set_layout(default_layout)

    @change("current_layout_name")
    def on_current_layout_changed(self, current_layout_name, *args, **kwargs):
        self._layout_manager.set_layout(current_layout_name)

    @property
    def server(self):
        return self._server

    def _build_ui(self, *args, **kwargs):
        with SinglePageLayout(self._server) as self.ui:
            self.ui.root.theme = "dark"

            # Toolbar
            self.ui.title.set_text("Slicer Trame")

            with self.ui.toolbar:
                vuetify3.VSpacer()

            # Main content
            with self.ui.content:
                with Div(classes="fill-height d-flex flex-row flex-grow-1"):
                    self._server.ui.layout_grid(self.ui)


def main(server=None, **kwargs):
    app = MyTrameSlicerApp(server)
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
