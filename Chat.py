import streamlit as st
import os
import pandas as pd
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from docx import Document
import mimetypes
import openpyxl

# Initialize session state for authentication and conversation history
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['role'] = None

if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []

# Login functionality
def login():
    st.title("Login")
    col1, col2, col3 = st.columns([1, 2, 1])
    # login form
    with col2:
        form = st.form("login_form")
        username = form.text_input("Username")
        password = form.text_input("Password", type="password")
        submitted = form.form_submit_button("Login")
        if submitted:
            # admin login
            if username == "admin" and password == "admin@123":
                st.session_state['authenticated'] = True
                st.session_state['role'] = "admin"
                st.success("Logged in as Admin")
            # user login
            elif username == "user" and password == "user@123":
                st.session_state['authenticated'] = True
                st.session_state['role'] = "user"
                st.success("Logged in as User")
            else:
                st.error("Incorrect Username or Password")

# extracting text from the uploaded file
def get_text_from_file(uploaded_file):
    """Extract text from uploaded files of various types."""
    text = ""
    try:
        file_mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        
        if file_mime_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            # Reading Excel file using openpyxl explicitly
            df = pd.read_excel(uploaded_file, engine="openpyxl")
            text = df.to_string()
        elif file_mime_type == "application/pdf":
            # Handling PDF files using PyPDF2
            reader = PdfReader(uploaded_file)
            text = ' '.join(page.extract_text() for page in reader.pages if page.extract_text() is not None)
        elif file_mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Handling DOCX files using python-docx
            doc = Document(uploaded_file)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            text = "\n".join(paragraphs)
        else:
            # Unsupported file type
            st.warning(f"Unsupported file type: {file_mime_type}.")
    except Exception as e:
        st.error(f"Error processing file {uploaded_file.name}: {e}")
    return text

# combining text from uploaded files
def get_text_from_files(files):
    """Concatenate texts extracted from multiple uploaded files."""
    all_text = ""
    for file in files:
        file_text = get_text_from_file(file)
        all_text += file_text + "\n\n"
    return all_text

# generating text chunks for size of 10000 and overlapping of 1000
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

# transforming into vectors using embeddings
def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = Chroma.from_texts(text_chunks, embedding=embeddings)
    vector_store.persist()

# using a prompt template for question handling using gemini-pro model
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# Chatbot functionality
def chatbot_response(user_question):
    # embedding the question and generating a response
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = Chroma(persist_directory="chroma_store")
        docs = vector_store.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        return response["output_text"]
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "Sorry, I couldn't process the response."

# Initialize a counter for generating unique keys
unique_key_counter = 0

def generate_unique_key():
    """Generate a unique key using a counter."""
    global unique_key_counter
    unique_key_counter += 1
    return f"input_{unique_key_counter}"

# Main function with UI Specifications
def main():
    genai.configure(api_key="AIzaSyAnziUXE0zbGSoAb0VOqgHbkOTcFf7o97I")
    st.set_page_config(page_title="Chatbot2", layout="wide")

    if not st.session_state['authenticated']:
        login()
    else:
        if st.session_state['role'] == "admin":
            # Admin-specific functionality
            st.header("Admin Dashboard")
            with st.form(key='chat_form_admin'):
                user_question_admin = st.text_input(f"You:")
                submit_button_admin = st.form_submit_button(label="Send")
                if submit_button_admin and user_question_admin:
                    st.write(chatbot_response(user_question_admin))

            # Admin file upload
            with st.sidebar:
                st.title("Admin Document Upload:")
                uploaded_files_admin = st.file_uploader("Upload files (PDF, DOCX, etc.)", accept_multiple_files=True)
                if st.button("Process Admin Files"):
                    with st.spinner("Processing..."):
                        raw_text_admin = get_text_from_files(uploaded_files_admin)
                        text_chunks_admin = get_text_chunks(raw_text_admin)
                        get_vector_store(text_chunks_admin)
                        st.success("Admin files processed and indexed.")
        elif st.session_state['role'] == "user":
            # User-specific functionality
            st.header("Search in Files")
            with st.form(key='chat_form_user'):
                user_question_user = st.text_input(f"You:")
                submit_button_user = st.form_submit_button(label="Send")
                if submit_button_user and user_question_user:
                    st.write(chatbot_response(user_question_user))

# calling the main function
if __name__ == "__main__":
    main()
