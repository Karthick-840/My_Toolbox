import my_toolbox.streamlit_tools as streamlit_tools


def test_multiapp_add_and_run(monkeypatch):
    app = streamlit_tools.MultiApp()
    state = {"ran": False}

    def page():
        state["ran"] = True

    app.add_app("A", page)

    monkeypatch.setattr(
        streamlit_tools.st,
        "selectbox",
        lambda label, apps, format_func=None: apps[0],
    )
    app.run()
    assert state["ran"] is True


def test_require_option_menu_raises(monkeypatch):
    monkeypatch.setattr(streamlit_tools, "option_menu", None)
    try:
        streamlit_tools._require_option_menu()
        assert False, "Expected ImportError"
    except ImportError:
        pass


def test_streamlit_menu_manual_selection(monkeypatch):
    monkeypatch.setattr(streamlit_tools, "option_menu", lambda *args, **kwargs: "Home")

    streamlit_tools.st.session_state["menu_option"] = 0
    streamlit_tools.st.session_state["switch_button"] = True
    monkeypatch.setattr(streamlit_tools.st, "button", lambda *args, **kwargs: False)

    menu = streamlit_tools.StreamlitMenu(
        options=["Home", "Upload"],
        icons=["h", "u"],
        menu_type="Manual Selection",
    )
    selected = menu.manual_selection_menu()
    assert selected == "Home"
