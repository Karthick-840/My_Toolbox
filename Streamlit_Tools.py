"""Frameworks for running multiple Streamlit applications as a single app.
credits to Data Professor - https://github.com/dataprofessor/multi-page-app
"""
import streamlit as st

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
        # app = st.sidebar.radio(
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
        with st.sidebar:
            selected = option_menu("Main Menu", self.options, 
                                   icons=self.icons, 
                                   menu_icon="cast", 
                                   default_index=1)
        return selected

    def horizontal_menu(self):
        selected = option_menu(None, self.options, 
                               icons=self.icons, 
                               menu_icon="cast", 
                               default_index=0, 
                               orientation="horizontal")
        return selected

    def css_styled_menu(self):
        selected = option_menu(None, self.options, 
                               icons=self.icons, 
                               menu_icon="cast", 
                               default_index=0, 
                               orientation="horizontal",
                               styles=self.css_styles)
        return selected

    def manual_selection_menu(self):
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

# Example of how to use the class
options = ["Home", "Upload", "Tasks", "Settings"]
icons = ['house', 'cloud-upload', "list-task", 'gear']
menu_type = "Horizontal"  # You can change this to "Sidebar", "Horizontal", or "Manual Selection"
css_styles = {
    "container": {"padding": "0!important", "background-color": "#fafafa"},
    "icon": {"color": "orange", "font-size": "25px"}, 
    "nav-link": {"font-size": "25px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
    "nav-link-selected": {"background-color": "green"},
}

# Create an instance of the menu
menu = StreamlitMenu(options, icons, menu_type, css_styles)
menu.display_menu()

    # 5. Add on_change callback
def on_change(key):
    selection = st.session_state[key]
    st.write(f"Selection changed to {selection}")
    
selected5 = option_menu(None, ["Home", "Upload", "Tasks", 'Settings'],
                        icons=['house', 'cloud-upload', "list-task", 'gear'],
                        on_change=on_change, key='menu_5', orientation="horizontal")
selected5
  



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


