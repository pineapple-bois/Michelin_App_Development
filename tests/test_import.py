from flask import Flask


def test_michelin_app_imports_and_exports_server(app_module):
    assert isinstance(app_module.server, Flask)
    assert app_module.app.server is app_module.server
    assert app_module.app.callback_map
