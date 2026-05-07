"""Frameworks for running multiple Streamlit applications as a single app.
credits to Data Professor - https://github.com/dataprofessor/multi-page-app
"""
import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ImportError:  # pragma: no cover
    option_menu = None


def _require_option_menu():
    if option_menu is None:
        raise ImportError(
            "streamlit_option_menu is required for menu rendering. "
            "Install with: pip install streamlit-option-menu"
        )


class MultiApp:
    """Framework for combining multiple streamlit applications.
    Usage:
        def foo():
            st.title("Hello Foo")
        def bar():
            st.title("Hello Bar")
        app = MultiApp()
        app.add_app("Foo", foo)
        app.add_app("Bar", bar)
        app.run()
    It is also possible keep each application in a separate file.
        import foo
        import bar
        app = MultiApp()
        app.add_app("Foo", foo.app)
        app.add_app("Bar", bar.app)
        app.run()
    """
    def __init__(self):
        self.apps = []

    def add_app(self, title, func):
        """Adds a new application.
        Parameters
        ----------
        func:
            the python function to render this app.
        title:
            title of the app. Appears in the dropdown in the sidebar.
        """
        self.apps.append({
            "title": title,
            "function": func
        })

    def run(self):
        app = st.selectbox(
            'Navigation',
            self.apps,
            format_func=lambda app: app['title'])

        app['function']()
        

class StreamlitMenu:
    def __init__(self, options, icons, menu_type, css_styles=None):
        """
        Initialize the menu with options, icons, type, and optional CSS styles.
        
        Parameters:
        - options: List of menu items
        - icons: List of icons corresponding to the menu items
        - menu_type: Type of menu to display ('Sidebar', 'Horizontal', 'CSS Styled', 'Manual Selection')
        - css_styles: Optional CSS styles for the CSS styled menu
        """
        self.options = options
        self.icons = icons
        self.menu_type = menu_type
        self.css_styles = css_styles if css_styles else {}
        
        # Initialize session state if not already done
        if 'menu_option' not in st.session_state:
            st.session_state['menu_option'] = 0
        if 'switch_button' not in st.session_state:
            st.session_state['switch_button'] = False

    def display_menu(self):
        if self.menu_type == "Sidebar":
            selected_option = self.sidebar_menu()
        elif self.menu_type == "Horizontal":
            selected_option = self.horizontal_menu()
        elif self.menu_type == "CSS Styled":
            selected_option = self.css_styled_menu()
        elif self.menu_type == "Manual Selection":
            selected_option = self.manual_selection_menu()

        st.write(f"You selected: {selected_option}")

    def sidebar_menu(self):
        _require_option_menu()
        with st.sidebar:
            selected = option_menu("Main Menu", self.options, 
                                   icons=self.icons, 
                                   menu_icon="cast", 
                                   default_index=1)
        return selected

    def horizontal_menu(self):
        _require_option_menu()
        selected = option_menu(None, self.options, 
                               icons=self.icons, 
                               menu_icon="cast", 
                               default_index=0, 
                               orientation="horizontal")
        return selected

    def css_styled_menu(self):
        _require_option_menu()
        selected = option_menu(None, self.options, 
                               icons=self.icons, 
                               menu_icon="cast", 
                               default_index=0, 
                               orientation="horizontal",
                               styles=self.css_styles)
        return selected

    def manual_selection_menu(self):
        _require_option_menu()
        if st.session_state.get('switch_button', False):
            st.session_state['menu_option'] = (st.session_state.get('menu_option', 0) + 1) % len(self.options)
            manual_select = st.session_state['menu_option']
        else:
            manual_select = None

        selected = option_menu(None, self.options, 
                               icons=self.icons, 
                               orientation="horizontal", 
                               manual_select=manual_select, 
                               key='menu_4')
        st.button(f"Move to Next {st.session_state.get('menu_option', 1)}", key='switch_button')
        return selected

def on_change(key):
    selection = st.session_state[key]
    st.write(f"Selection changed to {selection}")


def demo_menu():
    _require_option_menu()

    options = ["Home", "Upload", "Tasks", "Settings"]
    icons = ['house', 'cloud-upload', "list-task", 'gear']
    menu_type = "Horizontal"
    css_styles = {
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "25px"},
        "nav-link": {"font-size": "25px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "green"},
    }

    menu = StreamlitMenu(options, icons, menu_type, css_styles)
    menu.display_menu()

    selected = option_menu(
        None,
        ["Home", "Upload", "Tasks", 'Settings'],
        icons=['house', 'cloud-upload', "list-task", 'gear'],
        on_change=on_change,
        key='menu_5',
        orientation="horizontal",
    )
    return selected


if __name__ == "__main__":
    demo_menu()
  



# import streamlit as st
# from multiapp import MultiApp
# from apps import home, data, model # import your app modules here

# app = MultiApp()

# st.markdown("""
# # Multi-Page App

# This multi-page app is using the [streamlit-multiapps](https://github.com/upraneelnihar/streamlit-multiapps) framework developed by [Praneel Nihar](https://medium.com/@u.praneel.nihar). Also check out his [Medium article](https://medium.com/@u.praneel.nihar/building-multi-page-web-app-using-streamlit-7a40d55fa5b4).

# """)

# # Add all your application here
# app.add_app("Home", home.app)
# app.add_app("Data", data.app)
# app.add_app("Model", model.app)
# # The main app
# app.run()


import streamlit as st
import streamlit.components.v1 as components
import os

_RELEASE = True

# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        "option_menu",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/dist")
    _component_func = components.declare_component(
        "option_menu", path=build_dir)

# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.


def option_menu(menu_title, options, default_index=0, menu_icon=None, icons=None, orientation="vertical",
                styles=None, manual_select=None, key=None, on_change=None):
    """_summary_

    Args:
        menu_title (_type_): Title of the menu
        options (_type_): The options to present
        default_index (int, optional): Default index to start on. Defaults to 0.
        menu_icon (_type_, optional): Add a menu Icon. Defaults to None.
        icons (_type_, optional): Add icons for the options. Defaults to None.
        orientation (str, optional): Horizontal or Vertical. Defaults to "vertical".
        styles (_type_, optional): You can add a css style here. Defaults to None.
        manual_select (_type_, optional): An index to select. If passed, will change current selection to the passsed.
        key (_type_, optional): The component key. Defaults to None.
        on_change (_type_, optional): A callback function to call when the selection changes. Defaults to None. The callback function must accept a single argument, which will be the key of the option menu. You can fetch current selection by calling st.session_state[key]

    Returns:
        str: The selected option
    """
    _on_change = None
    if on_change is not None:
        if key is None:
            st.error("You must pass a key if you want to use the on_change callback for the option menu")
        else:
            def _on_change() -> any:
                return on_change(key)
    
    if manual_select is not None:  
        default_index = manual_select
        
    component_value = _component_func(options=options, 
                key=key, defaultIndex=default_index, icons=icons, menuTitle=menu_title, 
                menuIcon=menu_icon, default=options[default_index], 
                orientation=orientation, styles=styles, manualSelect=manual_select, on_change=_on_change)
    return component_value

# Create a second instance of our component whose `name` arg will vary
# based on a text_input widget.
#
# We use the special "key" argument to assign a fixed identity to this
# component instance. By default, when a component's arguments change,
# it is considered a new instance and will be re-mounted on the frontend
# and lose its current state. In this case, we want to vary the component's
# "name" argument without having it get recreated.
if __name__ == "__main__":
    st.set_page_config(page_title="Option Menu", layout="wide")
    with st.sidebar:
        selected = option_menu("Main Menu", ["Home", "Upload","---", "Tasks", 'Settings'], 
        icons=['house', 'cloud-upload', None, "list-task", 'gear'], menu_icon="cast", default_index=1)

    selected2 = option_menu(None, ["Home", "Upload", "---", "Tasks", 'Settings'], 
        icons=['house', 'cloud-upload', None, "list-task", 'gear'], 
        menu_icon="cast", default_index=0, orientation="horizontal")

    selected3 = option_menu(None, ["Home", "Upload",  "Tasks", 'Settings'], 
        icons=['house', 'cloud-upload', "list-task", 'gear'], 
        menu_icon="cast", default_index=0, orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "25px"}, 
            "nav-link": {"font-size": "25px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "green"},
        }
    )
