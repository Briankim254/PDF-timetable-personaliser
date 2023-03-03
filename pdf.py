import streamlit as st
from streamlit_option_menu import option_menu
from tabula import read_pdf
import pandas as pd
from csv2pdf import convert
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import plotly.express as px
import os
import streamlit_authenticator as stauth
from deta import Deta


st.set_page_config(layout="wide", page_title="Timetable Personalizer", page_icon="random", initial_sidebar_state="expanded",
                   menu_items={
                       'Get Help': 'mailto:bkimutai@kabarak.ac.ke',
                       'Report a bug': "mailto:bkimutai@kabarak.ac.ke",
                       'About': "# This is baan *extremely* cool app!"
                   },)



def database_connection():
    # initialize Deta with a Data Key
    deta = Deta(st.secrets["my_data_key"])
    db = deta.Base("users")
    db1 = deta.Base("reports")
    return db, db1

db, db1 = database_connection()

def insert_user(username,email,name, password, rank):
    return db.put({"key": username, "name":name ,"email": email, "password": password, "rank": rank})

def get_user(username):
    return db.get({"key": username})

def get_user_by_name(name):
    return db.get({"name": name})

def get_user_by_email(email):
    return db.get({"email": email})

def get_user_by_password(password):
    return db.get({"password": password})

def get_user_by_rank(rank):
    return db.get({"rank": rank})

def get_all_users():
    return db.fetch().items

def delete_user(username):
    return db.delete({"key": username})

def update_user(username, email, password):
    return db.update({"key": username}, {"email": email, "password": password})

def make_report(username, title, comment):
    return db1.put({"username": username, "title":title ,"comment": comment})

def get_reports():
    return db1.fetch().items

def delete_report(comment):
    db1.delete({"comment": comment})



# remove made with streamlit footer
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: visible;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


with st.sidebar:
    selected = option_menu(
        menu_title="Timetable Personalizer",  # required
        options=["Lecture", "Exam", "lecturer","Admin Panel"],  # required
        # icon name from https://fontawesome.com/icons?d=gallery&m=free
        icons=["easel", "file-earmark-easel", "file-earmark-person","person-workspace"],
        menu_icon="clock-history ",  # optinal
        default_index=0,  # optinal
        # orientation = "horizontal"
    )
    

if selected == "Admin Panel":
  
    users = get_all_users()
    usernames =[user["key"] for user in users]
    names = [user["name"] for user in users]
    emails = [user["email"] for user in users]
    passwords = [user["password"] for user in users]
    hashed_passwords = stauth.Hasher(passwords).generate()
    authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    'cookie', 'qwerpo', cookie_expiry_days=30)

    name, authentication_status, username = authenticator.login('Login', 'main')

    if st.session_state['authentication_status']:
        authenticator.logout('Logout', 'sidebar')
        st.subheader('Welcome *%s*' % (st.session_state['name']))
        # this is the menu in the admin panel
        admin = option_menu(
        menu_title= None,  # required
        options=["Reports", "Users"],  # required
        # icon name from https://fontawesome.com/icons?d=gallery&m=free
        icons=["flag", "clipboard-plus"],
        # menu_icon="tools ",  # optinal
        default_index=0,  # optinal
        orientation = "horizontal"
    )
        if admin == "Users":
            st.title("Register Users")
            st.write("Please fill in the form below to register a new user")
            def register():
                # Create a form
                with st.form(key='register_form'):
                    # Get user inputs
                    col01, col02, col03, col04, col05 = st.columns([1, 1, 1, 1, 1])
                    with col01:
                        username = st.text_input('Username')
                    with col02:
                        email = st.text_input('Email')
                    with col03:
                        name = st.text_input('Name')
                    with col04:
                        password = st.text_input('Password', type='password')
                    with col05:
                        rank = st.selectbox("user rank",["Representative","Lecturer","Adminstration"])
                    # If form is submitted
                    if st.form_submit_button('Register'):
                        # Perform validation
                        if not username:
                            st.warning('Please enter a username')
                            return
                        if not email:
                            st.warning('Please enter an email')
                            return
                        if not name:
                            st.warning('Please enter your name')
                            return
                        if not password:
                            st.warning('Please enter a password')
                            return
                        if not rank:
                            st.warning('Please enter your rank')
                            return
                        else:
                            # Insert user data into the database
                            insert_user(username, email, name, password,rank)
                            st.success('Registration successful')
                    

            # Display registration form
            register()

            
        elif admin == "Reports":
            st.title("Reports")
            st.write("Please find below the reports made by the users")
            #display a grid formart all the reports
            reports = get_reports()
            usernames =[report["username"] for report in reports]
            titles = [report["title"] for report in reports]
            comments = [report["comment"] for report in reports]
            df = pd.DataFrame(list(zip(usernames, titles, comments)), columns =['User', 'Title', 'Comment'])
            st.dataframe(df, use_container_width=True)
            #delete a report
            if st.checkbox("Delete a report"):
                comment = st.selectbox("Comment",comments)  
                if st.button('Delete Confirmation'):
                    delete_report(comment)
                    st.success('Report deleted successfully')

    
    elif st.session_state['authentication_status'] == False:
        st.error('Username/password is incorrect')
    elif st.session_state['authentication_status'] == None:
        st.warning('Please enter your username and password')


if selected == "Lecture":
    if "upload" not in st.session_state:
        st.session_state["upload"] = "not done"
        df = 0

    if "selected_subjects_df1" not in st.session_state:
        st.session_state["selected_subjects_df1"] = pd.DataFrame()

    if "lecture_success" not in st.session_state:
        st.session_state["lecture_success"] = False

    if "report_lecture" not in st.session_state:
        st.session_state["report_lecture"] = False

    def lecture_change_state():
        st.session_state["upload"] = "done"

    def lecture_clear_selection():
        st.session_state["selected_subjects_df1"] = pd.DataFrame()

    def lecture_success():
        st.session_state["lecture_success"] = True

    def lecture_report():
        st.session_state["report_lecture"] = True

    st.title("Lecture Timetable Personalizer :date:")

    col01, col02 = st.columns([2, 1])
    with col01:
        # allow the user to upload the pdf file then read it
        lecture_file = st.file_uploader("Choose a lecture timetable PDF file",
                                        type="pdf", on_change=lecture_change_state, help="Upload the pdf file",)
    complete_lec_df = pd.DataFrame()

    if st.session_state["upload"] == "done":
        # Read the pdf file
        if lecture_file is not None:
            df = read_pdf(lecture_file,  pages="all",
                          multiple_tables=True, encoding='latin-1', lattice=True)
            pages = len(df)
            # line seperator
            st.write(
                "--------------------------------------------------------------")
            # python dictionary to store the pages and the  value of the first col of each table in the pdf
            # the key is the first coloumn name and the value is the page number of each table in the pdf
            dict = {}
            for page in range(pages):
                tables = df[page]
                title = tables["Group"].iat[0]
                dict[title] = page
                # concatenate the table1 with complete_df
                complete_lec_df = pd.concat(
                    [complete_lec_df, tables], ignore_index=True)

            col1, col2 = st.columns([1, 3])
            with col1:
                # create a selectbox to select the value of [0,1] of each table in the pdf
                # the selectbox will display the cell value of [0,1] of each table in the pdf
                # the selectbox will return the page number of the selected table
                title = st.selectbox(
                    "Select the course group to display", list(dict.keys()))
                page = dict[title]

            with col2:
                table = df[page]
                st.write("page: ", page, ": ", table["Group"].iat[0])
            st.subheader(
                "Choose the subjects you would like in your table")
            st.write(""" :arrow_heading_down:  click on the checkboxes below to select a row
                        """)

            # table data preprocessing
            col = table.iat[0, 1]
            firstcol = table.columns
            # table.drop(index=0, axis=1, inplace=True,)
            table1 = table.drop(columns=firstcol[0], axis=0)
            # drop the last row
            table1.drop(index=table1.index[-1], axis=0, inplace=True)
            # loop to rename the columns unnamed:0 to Lesson, unnamed:1 to Day, unnamed:2
            # to Subject, unnamed:3 to Room, unnamed:4 to Teacher in the table
            for col in table1.columns:
                if col == "Unnamed: 0":
                    table1.rename(
                        columns={"Unnamed: 0": "Lesson"}, inplace=True)
                elif col == "Unnamed: 1":
                    table1.rename(
                        columns={"Unnamed: 1": "Day"}, inplace=True)
                elif col == "Unnamed: 2":
                    table1.rename(
                        columns={"Unnamed: 2": "Subject"}, inplace=True)
                elif col == "Unnamed: 3":
                    table1.rename(
                        columns={"Unnamed: 3": "Room"}, inplace=True)
                elif col == "Unnamed: 4":
                    table1.rename(
                        columns={"Unnamed: 4": "Teacher"}, inplace=True)
                else:
                    pass

            gd = GridOptionsBuilder.from_dataframe(table1)
            gd.configure_default_column(groupable=True, editable=True)
            gd.configure_pagination(enabled=True, paginationPageSize=10)
            gd.configure_auto_height(autoHeight=True)
            gd.configure_selection(use_checkbox=True, selection_mode='multiple',
                                   header_checkbox=True, rowMultiSelectWithClick=True, )
            options = gd.build()
            grid_table = AgGrid(
                table1, gridOptions=options, update_mode=GridUpdateMode.SELECTION_CHANGED, theme='alpine', columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,)
            sel_rows = grid_table["selected_rows"]

            # get the selected rows in a dataframe without the colomns _selectedRowNodeInfo

            selected_subjects_df = pd.DataFrame(sel_rows)
            if selected_subjects_df.empty:
                pass
            else:
                selected_subjects_df.drop(
                    columns='_selectedRowNodeInfo', axis=1, inplace=True)

            # line seperator
            st.write(
                "--------------------------------------------------------------")

            # save a concatinated dataframe of the selected_subjects_df1 and the selected_subjects_df to a session state variable
            st.session_state["selected_subjects_df1"] = pd.concat(
                [st.session_state["selected_subjects_df1"], selected_subjects_df], ignore_index=True)

            # drop duplicate rows in the selected_subjects_df1
            st.session_state["selected_subjects_df1"].drop_duplicates(
                inplace=True)
            st.subheader("Your selection:")
            # show the selected_subjects_df1 session state variable
            st.dataframe(
                st.session_state["selected_subjects_df1"], use_container_width=True)

            # save the selected_exams_df1 to a new csv file and propose the download button to the user
            csv_lecture = st.session_state["selected_subjects_df1"].to_csv(
                index=False,)

            st.button("Clear selection", on_click=lecture_clear_selection)

            # line seperator
            st.write(
                "--------------------------------------------------------------")

            # dowmload the selected table
            st.session_state["selected_subjects_df1"].to_csv(
                'lecture.csv', index=False,)
            if st.session_state["selected_subjects_df1"].empty:
                pass
            else:
                # convert the csv file to pdf
                convert("lecture.csv", "lecture.pdf", font=os.path.join(
                    os.path.dirname(__file__), "Fonts", "NewsCycle-Regular.ttf"), size=7)

                # plotly bar chart of the selected_subjects_df1 session state variable to show the day on the x axis and the lesson on the y axis and subject as the color
                fig = px.bar(
                    st.session_state["selected_subjects_df1"], x="Day", y="Lesson", color="Subject")
                st.plotly_chart(fig)

            # create a blank pdf file named lecture.pdf if it does not exist
            if not os.path.exists("lecture.pdf"):
                open("lecture.pdf", "w").close()

            # download button to download the sample.pdf
            with open("lecture.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            col3, col4, col5 = st.columns([1, 1, 1])
            with col3:
                st.download_button(label="Export pdf",
                                data=PDFbyte,
                                file_name="Personalized lecture timetable.pdf",
                                mime='application/octet-stream',
                                on_click=lecture_success
                                )
            with col4:
                st.download_button(
                    label="Export CSV",
                    data=csv_lecture,
                    file_name='Personalized lecture timetable.csv',
                    mime='text/csv',
                    on_click=lecture_success
                )

            if st.session_state["lecture_success"]:
                st.success("succesfully downloaded summarzied table")
                st.session_state["lecture_success"] = False
            
            with col5:
                #add abutton to execute the report block below
                st.button("Report", on_click= lecture_report)

            if st.session_state["report_lecture"] :
                users = get_all_users()
                usernames =[user["key"] for user in users]
                names = [user["name"] for user in users]
                emails = [user["email"] for user in users]
                passwords = [user["password"] for user in users]
                hashed_passwords = stauth.Hasher(passwords).generate()
                authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                'cookie', 'qwerpo', cookie_expiry_days=30)

                name, authentication_status, username = authenticator.login('Login', 'main')
                if st.session_state['authentication_status']:
                    st.subheader('Welcome *%s*' % (st.session_state['name']))
                    authenticator.logout('Logout', 'sidebar')
                    #report block
                    with st.form(key="reports"):
                        col6, col9 = st.columns([1, 1])
                        with col6:
                            st.subheader("Report")
                            title = st.text_input("subject of concern:", value="")
                        with col9:
                            st.subheader("Report")
                            comment = st.text_area("comment", value="")
                        submittion = st.form_submit_button("Submit")
                        if submittion:
                            if title == "" or comment == "":
                                st.warning("Please fill in all the fields")
                            else:
                                make_report(st.session_state['name'],title, comment)
                                st.success("Thank you for your feedback")
                        
                elif st.session_state['authentication_status'] == False:
                    st.error('Username/password is incorrect')
                elif st.session_state['authentication_status'] == None:
                    st.warning('Please enter your username and password')                    


if selected == "Exam":
    if "exam_upload" not in st.session_state:
        st.session_state["exam_upload"] = "not done"
        df = 0

    if "selected_exams_df1" not in st.session_state:
        st.session_state["selected_exams_df1"] = pd.DataFrame()

    if "exam_success" not in st.session_state:
        st.session_state["exam_success"] = False

    def exam_change_state():
        st.session_state["exam_upload"] = "done"

    def exam_clear_selection():
        st.session_state["selected_exams_df1"] = pd.DataFrame()

    def exam_success():
        st.session_state["exam_success"] = True

    st.title("Exam Timetable Personalizer :pencil:")

    col01, col02 = st.columns([2, 1])
    with col01:

        # allow the user to upload the pdf file then read it
        exam_file = st.file_uploader(
            "Choose a exam timetable PDF file", type="pdf", on_change=exam_change_state)

    if st.session_state["exam_upload"] == "done":
        if exam_file is not None:
            # Read the pdf file
            df = read_pdf(exam_file, pages="all", multiple_tables=True,
                          lattice=True, encoding='utf-8')
            pages = len(df)
            # line seperator
            st.write(
                "--------------------------------------------------------------")
            # python dictionary to store the pages and the  value of the first col of each table in the pdf
            # the key is the first coloumn name and the value is the page number of each table in the pdf
            dict = {}
            for page in range(pages):
                tables = df[page]
                title = tables.columns[0]
                dict[title] = page

            col1, col2 = st.columns([1, 3])
            with col1:
                # create a selectbox to select the value of [0,1] of each table in the pdf
                # the selectbox will display the cell value of [0,1] of each table in the pdf
                # the selectbox will return the page number of the selected table
                title = st.selectbox(
                    "which group do you want?", list(dict.keys()))
                page = dict[title]

            with col2:
                table = df[page]
                st.write("page: ", page)

                # table data preprocessing
                col = table.iat[0, 1]
                firstcol = table.columns
                table.drop(index=0, axis=1, inplace=True,)
                table1 = table.drop(columns=firstcol[0], axis=0)
                table1.drop(index=table1.index[-1], axis=0, inplace=True)
                # loop to rename the columns unnamed:0 to group, unnamed:1 to week, unnamed:2 to day,
                #  unnamed:3 to unit, unnamed:4 to venue,unnamed:5 to teacher in the taable
                for col in table1.columns:
                    if col == "Unnamed: 0":
                        table1.rename(
                            columns={"Unnamed: 0": "Group"}, inplace=True)
                    elif col == "Unnamed: 1":
                        table1.rename(
                            columns={"Unnamed: 1": "Week"}, inplace=True)
                    elif col == "Unnamed: 2":
                        table1.rename(
                            columns={"Unnamed: 2": "Day"}, inplace=True)
                    elif col == "Unnamed: 3":
                        table1.rename(
                            columns={"Unnamed: 3": "Unit"}, inplace=True)
                    elif col == "Unnamed: 4":
                        table1.rename(
                            columns={"Unnamed: 4": "Venue"}, inplace=True)
                    elif col == "Unnamed: 5":
                        table1.rename(
                            columns={"Unnamed: 5": "Teacher"}, inplace=True)
                    else:
                        pass

                st.dataframe(table1, use_container_width=True)

            # line seperator
            st.write(
                "--------------------------------------------------------------")
            # create a new dataframe called selected_subjects_df1

            # create a dropdown for selecting the list of items in the column Subject and saving the selected row,
            #  in a list called selected_subjects
            selected_exams = st.multiselect(
                "Select the subjects you want to summarize", table1["Unit"].unique())

        # create a new dataframe called selected_exams_df that contains the selected rows for multiplee tables
            selected_subjects_df = table1[table1["Unit"].isin(selected_exams)]

            # save a concatinated dataframe of the selected_exams_df1 and the selected_subjects_df to a session state variable
            st.session_state["selected_exams_df1"] = pd.concat(
                [st.session_state["selected_exams_df1"], selected_subjects_df], ignore_index=True)

            # drop the duplicates in the selected_exams_df1
            st.session_state["selected_exams_df1"].drop_duplicates(
                inplace=True)

            # show the selected_subjects_df1 session state variable
            st.dataframe(
                st.session_state["selected_exams_df1"], use_container_width=True)

            st.button("Clear", on_click=exam_clear_selection)

            # save the selected_exams_df1 to a new csv file and propose the download button to the user
            csv_exam = st.session_state["selected_exams_df1"].to_csv(
                index=False)

            # line seperator
            st.write(
                "--------------------------------------------------------------")

            st.session_state["selected_exams_df1"].to_csv(
                'exam.csv', index=False,)
            convert("exam.csv", "exam.pdf", font=os.path.join(
                    os.path.dirname(__file__), "Fonts", "NewsCycle-Regular.ttf"), size=7)

            # download button to download the sample.pdf
            with open("exam.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.download_button(label="Export pdf",
                               data=PDFbyte,
                               file_name="Personalized exam timetable.pdf",
                               mime='application/octet-stream',
                               on_click=exam_success)

            st.download_button(
                label="Export CSV",
                data=csv_exam,
                file_name='Personalized exam_timetable.csv',
                mime='text/csv', on_click=exam_success
            )

            if st.session_state["exam_success"]:
                st.success("succesfully downloaded summarzied table")
                st.session_state["exam_success"] = False
            else:
                pass

if selected == "lecturer":

    if "lecturer_success" not in st.session_state:
        st.session_state["lecturer_success"] = False

    if "lecturer_upload" not in st.session_state:
        st.session_state["lecturer_upload"] = "not done"
        df = 0

    def lecturer_change_state():
        st.session_state["lecturer_upload"] = "done"

    def lecturer_success():
        st.session_state["lecturer_success"] = True

    st.title("Lecturer Timetable Personalizer :briefcase:")
    complete_df = pd.DataFrame()
    col001, col002 = st.columns([2, 1])
    with col001:

        # allow the user to upload the pdf file then read it
        lecturer_file = st.file_uploader(
            """ Choose a lecture timetable PDF file """, type="pdf", on_change=lecturer_change_state)

    if st.session_state["lecturer_upload"] == "done":
        if lecturer_file is not None:
            # Read the pdf file
            df = read_pdf(lecturer_file, pages="all",
                          multiple_tables=True, encoding='utf-8', lattice=True)
            pages = len(df)

            # # line seperator
            # st.write("--------------------------------------------------------------")
            # python dictionary to store the pages and the  value of the first col of each table in the pdf
            # the key is the first coloumn name and the value is the page number of each table in the pdf
            dict_1 = {}
            for page in range(pages):
                tables = df[page]
                title = tables["Group"].iat[0]
                dict_1[page] = title

            col1, col2 = st.columns([1, 3])
            # with col1:
            #     # create a selectbox to select the value of [0,1] of each table in the pdf
            #     # the selectbox will display the cell value of [0,1] of each table in the pdf
            #     # the selectbox will return the page number of the selected table
            #     title = st.selectbox("which lecturer do you want?",list(dict.keys()))
            #     page = dict[title]

            for page in range(len(df)):

                table = df[page]

                # table data preprocessing
                col = table.iat[0, 1]
                firstcol = table.columns
                # table.drop(index=0, axis=1, inplace=True,)
                table1 = table.drop(columns=firstcol[0], axis=0)
                # drop the last row
                table1.drop(index=table1.index[-1], axis=0, inplace=True)

                # add a coloumn to the table with the value of the page number
                # table1.insert(0, "Group", dict_1[page])

                # loop to rename the columns unnamed:0 to Lesson, unnamed:1 to Day, unnamed:2 to Subject,
                #  unnamed:3 to Room, unnamed:4 to Teacher in the table
                for col in table1.columns:
                    if col == "Unnamed: 0":
                        table1.rename(
                            columns={"Unnamed: 0": "Lesson"}, inplace=True)
                    elif col == "Unnamed: 1":
                        table1.rename(
                            columns={"Unnamed: 1": "Day"}, inplace=True)
                    elif col == "Unnamed: 2":
                        table1.rename(
                            columns={"Unnamed: 2": "Subject"}, inplace=True)
                    elif col == "Unnamed: 3":
                        table1.rename(
                            columns={"Unnamed: 3": "Room"}, inplace=True)
                    elif col == "Unnamed: 4":
                        table1.rename(
                            columns={"Unnamed: 4": "Teacher"}, inplace=True)
                    else:
                        pass
                # concatenate the table1 with complete_df
                complete_df = pd.concat(
                    [complete_df, table1], ignore_index=True)

            # line seperator
            st.write(
                "--------------------------------------------------------------")

            with col1:
                # exept Nan values
                teacher = st.selectbox("Select the Lecturer you want to see", list(
                    complete_df["Teacher"].unique()), index=1)
                # select the rows with the selected teacher
                teacher_df = complete_df[complete_df["Teacher"] == teacher]
                # show the table
            with col2:
                # reindex the table
                teacher_df.reset_index(drop=True, inplace=True)

            # show the table
            st.subheader("Your Lecture Timetable")
            gd = GridOptionsBuilder.from_dataframe(table1)
            gd.configure_default_column(groupable=True, editable=True)
            gd.configure_pagination(enabled=False, paginationPageSize=10)
            gd.configure_auto_height(autoHeight=True)
            gd.configure_selection(use_checkbox=False, selection_mode='disabled',
                                   header_checkbox=True, rowMultiSelectWithClick=True, )
            options = gd.build()
            grid_table = AgGrid(
                teacher_df, gridOptions=options, update_mode=GridUpdateMode.VALUE_CHANGED, theme='alpine', columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,)

            # pass the table to the varible final_table even when edited
            edited_rows = grid_table["data"]

            # get the selected rows in a dataframe without the colomns _selectedRowNodeInfo

            selected_lecturer_df = pd.DataFrame(edited_rows)

            # To represent the days of the week and the time of day, you can use the x-axis to display the days of the week and the y-axis to display the time of day. To represent the lessons that are happening at specific times, you can use different colors or markers to indicate the different classes or subjects in a bar graph
            # st.subheader("Your Lecture Timetable")
            import plotly.express as px
            fig = px.bar(teacher_df, x="Day", y="Lesson", color="Subject",
                         orientation='v', )
            fig.update_layout(
                title="Your Lecture Timetable Graph",
                xaxis_title="Day",
                yaxis_title="Subject",
                font=dict(
                    family="Courier New, monospace",
                    size=18,
                    color="RebeccaPurple"
                )
            )
            st.plotly_chart(fig)
            

            # line seperator
            st.write(
                "--------------------------------------------------------------")

            # dowmload the selected table
            selected_lecturer_df.to_csv('lecturer.csv', index=False,)
            csv_lecturer = selected_lecturer_df.to_csv(index=False,)
            convert("lecturer.csv", "lecturer.pdf", font=os.path.join(
                    os.path.dirname(__file__), "Fonts", "NewsCycle-Regular.ttf"), size=7)

            # download button to download the sample.pdf
            with open("lecturer.pdf", "rb") as pdf_file:
                PDFbyte = pdf_file.read()

            st.download_button(label="Export pdf",
                               data=PDFbyte,
                               file_name="lecturer_timetable.pdf",
                               mime='application/octet-stream',
                               on_click=lecturer_success)

            st.download_button(
                label="Export csv",
                data=csv_lecturer,
                file_name='lecturer_timetable.csv',
                mime='text/csv',
                on_click=lecturer_success
            )

            if st.session_state["lecturer_success"]:
                st.success("succesfully downloaded summarzied table")
                st.session_state["lecturer_success"] = False
            else:
                pass
