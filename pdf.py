import streamlit as st
from streamlit_option_menu import option_menu
from tabula import read_pdf
import pandas as pd

st.set_page_config(layout="wide",page_title="Timetable Personalizer",page_icon="random",initial_sidebar_state="expanded",
    menu_items={
       'Get Help': 'mailto:bkimutai@kabarak.ac.ke',
        'Report a bug': "mailto:bkimutai@kabarak.ac.ke",
        'About': "# This is baan *extremely* cool app!"
    },)

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
            menu_title = "Timetable Personalizer",#required
            options =["Lecture","Exam","lecturer"],#required
            icons =["easel","file-earmark-easel","file-earmark-person"],#icon name from https://fontawesome.com/icons?d=gallery&m=free
            menu_icon = "tools ",#optinal
            default_index = 0,#optinal
            # orientation = "horizontal"     
            )
        
if selected == "Lecture":
    if "upload" not in st.session_state:
        st.session_state["upload"]= "not done"
        df = 0

    if "selected_subjects_df1" not in st.session_state:
        st.session_state["selected_subjects_df1"]= pd.DataFrame()

    if "lecture_success" not in st.session_state:
            st.session_state["lecture_success"]= False

    def lecture_change_state():
        st.session_state["upload"]="done"

    def lecture_clear_selection():
        st.session_state["selected_subjects_df1"]= pd.DataFrame()

    def lecture_success():
        st.session_state["lecture_success"]= True
        

    st.title("Lecture Timetable Personalizer :sparkles:")


    col01,col02 = st.columns([2,1])
    with col01:
        #allow the user to upload the pdf file then read it
        lecture_file = st.file_uploader("Choose a lecture timetable PDF file", type="pdf", on_change= lecture_change_state, help="Upload the pdf file",)


    if st.session_state["upload"] == "done":
        # Read the pdf file
        if lecture_file is not None:
            df = read_pdf(lecture_file, pages="all", multiple_tables=True,encoding='latin-1',lattice=True)
            pages = len(df)
            # line seperator
            st.write("--------------------------------------------------------------")
            #python dictionary to store the pages and the  value of the first col of each table in the pdf
            # the key is the first coloumn name and the value is the page number of each table in the pdf
            dict = {}
            for page in range(pages):
                tables = df[page]
                title =tables.columns[0]
                dict[title] = page
                
            col1,col2 = st.columns([1,3])
            with col1:
                # create a selectbox to select the value of [0,1] of each table in the pdf
                # the selectbox will display the cell value of [0,1] of each table in the pdf
                # the selectbox will return the page number of the selected table
                title = st.selectbox("which group do you want?",list(dict.keys()))
                page = dict[title]
                
                

            with col2:
                table = df[page]
                st.write("page: ",page,": ",table.columns[0])

                # table data preprocessing
                col = table.iat[0,1]
                firstcol = table.columns
                table.drop(index=0,axis=1,inplace=True,)
                table1 = table.drop(columns=firstcol[0], axis=0)
                #drop the last row
                table1.drop(index=table1.index[-1],axis=0,inplace=True)
                # loop to rename the columns unnamed:0 to Lesson, unnamed:1 to Day, unnamed:2 to Subject, unnamed:3 to Room, unnamed:4 to Teacher in the table
                for col in table1.columns:
                    if col == "Unnamed: 0":
                        table1.rename(columns={"Unnamed: 0":"Lesson"}, inplace=True)
                    elif col == "Unnamed: 1":
                        table1.rename(columns={"Unnamed: 1":"Day"}, inplace=True)
                    elif col == "Unnamed: 2":
                        table1.rename(columns={"Unnamed: 2":"Subject"}, inplace=True)
                    elif col == "Unnamed: 3":
                        table1.rename(columns={"Unnamed: 3":"Room"}, inplace=True)
                    elif col == "Unnamed: 4":
                        table1.rename(columns={"Unnamed: 4":"Teacher"}, inplace=True)
                    else:
                        pass

                st.dataframe(table1,use_container_width=True)

            # line seperator
            st.write("--------------------------------------------------------------") 
            
            # create a dropdown for selecting the list of items in the column Subject and saving the selected row in a list called selected_subjects 
            selected_subjects = st.multiselect("Select the subjects you want to see",table1["Subject"].unique())
        
        # create a new dataframe called selected_subjects_df that contains the selected rows for multiplee tables
            selected_subjects_df = table1[table1["Subject"].isin(selected_subjects)]

            #save a concatinated dataframe of the selected_subjects_df1 and the selected_subjects_df to a session state variable
            st.session_state["selected_subjects_df1"] = pd.concat([ st.session_state["selected_subjects_df1"],selected_subjects_df],ignore_index=True)
            
            # show the selected_subjects_df1 session state variable
            st.dataframe(st.session_state["selected_subjects_df1"],use_container_width=True)
            
            # save the selected_exams_df1 to a new csv file and propose the download button to the user
            csv_lecture = st.session_state["selected_subjects_df1"].to_csv(index=False)

            st.button("Clear",on_click=lecture_clear_selection)
            
            # line seperator
            st.write("--------------------------------------------------------------") 
        
            st.download_button(
                label="Download CSV",
                data=csv_lecture,
                file_name='Personalized lecture_timetable.csv',
                mime='text/csv',on_click=lecture_success
            )

            if st.session_state["lecture_success"]:
                st.success("succesfully downloaded summarzied table")
                st.session_state["lecture_success"] = False
            else:
                pass


if selected == "Exam":
    if "exam_upload" not in st.session_state:
        st.session_state["exam_upload"]= "not done"
        df = 0

    if "selected_exams_df1" not in st.session_state:
        st.session_state["selected_exams_df1"]= pd.DataFrame()

    if "exam_success" not in st.session_state:
        st.session_state["exam_success"]= False

    def exam_change_state():
        st.session_state["exam_upload"]="done"

    def exam_clear_selection():
        st.session_state["selected_exams_df1"]= pd.DataFrame()

    def exam_success():
        st.session_state["exam_success"]= True
        

    st.title("Exam Timetable Personalizer :dizzy:")

    col01,col02 = st.columns([2,1])
    with col01:

        #allow the user to upload the pdf file then read it
        exam_file = st.file_uploader("Choose a exam timetable PDF file", type="pdf", on_change= exam_change_state)


    if st.session_state["exam_upload"] == "done":
        if exam_file is not None:
            # Read the pdf file
            df = read_pdf(exam_file, pages="all", multiple_tables=True,lattice=True)
            pages = len(df)
            # line seperator
            st.write("--------------------------------------------------------------")
            #python dictionary to store the pages and the  value of the first col of each table in the pdf
            # the key is the first coloumn name and the value is the page number of each table in the pdf
            dict = {}
            for page in range(pages):
                tables = df[page]
                title =tables.columns[0]
                dict[title] = page
            
            col1,col2 = st.columns([1,3])
            with col1:
                # create a selectbox to select the value of [0,1] of each table in the pdf
                # the selectbox will display the cell value of [0,1] of each table in the pdf
                # the selectbox will return the page number of the selected table
                title = st.selectbox("which group do you want?",list(dict.keys()))
                page = dict[title]
                
                
            
            with col2:
                table = df[page]
                st.write("page: ",page)

                # table data preprocessing
                col = table.iat[0,1]
                firstcol = table.columns
                table.drop(index=0,axis=1,inplace=True,)
                table1 = table.drop(columns=firstcol[0], axis=0)
                table1.drop(index=table1.index[-1],axis=0,inplace=True)
                # loop to rename the columns unnamed:0 to group, unnamed:1 to week, unnamed:2 to day, unnamed:3 to unit, unnamed:4 to venue,unnamed:5 to teacher in the taable
                for col in table1.columns:
                    if col == "Unnamed: 0":
                        table1.rename(columns={"Unnamed: 0":"Group"}, inplace=True)
                    elif col == "Unnamed: 1":
                        table1.rename(columns={"Unnamed: 1":"Week"}, inplace=True)
                    elif col == "Unnamed: 2":
                        table1.rename(columns={"Unnamed: 2":"Day"}, inplace=True)
                    elif col == "Unnamed: 3":
                        table1.rename(columns={"Unnamed: 3":"Unit"}, inplace=True)
                    elif col == "Unnamed: 4":
                        table1.rename(columns={"Unnamed: 4":"Venue"}, inplace=True)
                    elif col == "Unnamed: 5":
                        table1.rename(columns={"Unnamed: 5":"Teacher"}, inplace=True)
                    else:
                        pass

                st.dataframe(table1,use_container_width=True)

            # line seperator
            st.write("--------------------------------------------------------------") 
            # create a new dataframe called selected_subjects_df1
            
                

            # create a dropdown for selecting the list of items in the column Subject and saving the selected row in a list called selected_subjects 
            selected_exams = st.multiselect("Select the subjects you want to summarize",table1["Unit"].unique())
        
        # create a new dataframe called selected_exams_df that contains the selected rows for multiplee tables
            selected_subjects_df = table1[table1["Unit"].isin(selected_exams)]

            #save a concatinated dataframe of the selected_exams_df1 and the selected_subjects_df to a session state variable
            st.session_state["selected_exams_df1"] = pd.concat([ st.session_state["selected_exams_df1"],selected_subjects_df],ignore_index=True)
            
            # show the selected_subjects_df1 session state variable
            st.dataframe(st.session_state["selected_exams_df1"],use_container_width=True)
            
            st.button("Clear",on_click=exam_clear_selection)
          
            # save the selected_exams_df1 to a new csv file and propose the download button to the user
            csv_exam = st.session_state["selected_exams_df1"].to_csv(index=False)

            # line seperator
            st.write("--------------------------------------------------------------") 
        
            st.session_state["download"] = st.download_button(
                label="Download CSV",
                data=csv_exam,
                file_name='Personalized exam_timetable.csv',
                mime='text/csv',on_click=exam_success
            )
            
            if st.session_state["exam_success"]:
                st.success("succesfully downloaded summarzied table")
                st.session_state["exam_success"] = False
            else:
                pass

if selected == "lecturer":

    if "lecturer_upload" not in st.session_state:
        st.session_state["lecturer_upload"]= "not done"
        df = 0

    def lecturer_change_state():
        st.session_state["lecturer_upload"]="done"

    st.title("Lecturer Timetable Personalizer :alien:")
    complete_df = pd.DataFrame()
    col001,col002 = st.columns([2,1])
    with col001:

        #allow the user to upload the pdf file then read it
        lecturer_file = st.file_uploader(""" Choose a lecture timetable PDF file :star:""", type="pdf", on_change= lecturer_change_state)


    if st.session_state["lecturer_upload"] == "done":
        if lecturer_file is not None:
                # Read the pdf file
                df = read_pdf(lecturer_file, pages="all", multiple_tables=True,encoding='latin-1',lattice=True)
                pages = len(df)



                # # line seperator
                # st.write("--------------------------------------------------------------")
                #python dictionary to store the pages and the  value of the first col of each table in the pdf
                # the key is the first coloumn name and the value is the page number of each table in the pdf
                dict_1 = {}
                for page in range(pages):
                    tables = df[page]
                    title =tables.columns[0]
                    dict_1[page] = title
                
                col1,col2 = st.columns([1,4])
                # with col1:
                #     # create a selectbox to select the value of [0,1] of each table in the pdf
                #     # the selectbox will display the cell value of [0,1] of each table in the pdf
                #     # the selectbox will return the page number of the selected table
                #     title = st.selectbox("which lecturer do you want?",list(dict.keys()))
                #     page = dict[title]
                    
                    
                
                
                for page in range(len(df)):

                    table = df[page]

                    # table data preprocessing
                    col = table.iat[0,1]
                    firstcol = table.columns
                    table.drop(index=0,axis=1,inplace=True,)
                    table1 = table.drop(columns=firstcol[0], axis=0)
                    #drop the last row
                    table1.drop(index=table1.index[-1],axis=0,inplace=True)

                    # add a coloumn to the table with the value of the page number
                    table1.insert(0,"Group",dict_1[page])

                    # loop to rename the columns unnamed:0 to Lesson, unnamed:1 to Day, unnamed:2 to Subject, unnamed:3 to Room, unnamed:4 to Teacher in the table
                    for col in table1.columns:
                        if col == "Unnamed: 0":
                            table1.rename(columns={"Unnamed: 0":"Lesson"}, inplace=True)
                        elif col == "Unnamed: 1":
                            table1.rename(columns={"Unnamed: 1":"Day"}, inplace=True)
                        elif col == "Unnamed: 2":
                            table1.rename(columns={"Unnamed: 2":"Subject"}, inplace=True)
                        elif col == "Unnamed: 3":
                            table1.rename(columns={"Unnamed: 3":"Room"}, inplace=True)
                        elif col == "Unnamed: 4":
                            table1.rename(columns={"Unnamed: 4":"Teacher"}, inplace=True)
                        else:
                            pass
                    #concatenate the table1 with complete_df
                    complete_df= pd.concat([complete_df,table1],ignore_index=True)
                with col1:        
                    teacher = st.selectbox("Select the Lecturer you want to see",list(complete_df["Teacher"].unique(),))
                    #select the rows with the selected teacher
                    teacher_df = complete_df[complete_df["Teacher"]==teacher]
                    # show the table
                with col2:
                    st.dataframe(teacher_df,use_container_width=True)
