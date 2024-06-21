import openai
from azure.identity import DefaultAzureCredential
import streamlit as st
import pandas as pd

# Directly set your Azure OpenAI service configuration
endpoint = "https://insightgen.openai.azure.com/"
deployment = "ChatBot"  # Replace with your deployment name
api_version = "2024-02-15-preview"  # Replace with your API version
api_key = "54de899334ca4850b3f71da993dd0346"  # Replace with your OpenAI API key

# Configure the OpenAI API to use Azure
openai.api_type = "azure"
openai.api_base = endpoint
openai.api_version = api_version
openai.api_key = api_key

# Load the Excel file into a pandas DataFrame
excel_file = r"C:\Users\guru.km\Downloads\Book.xlsx"   # Replace with your Excel file path
df = pd.read_excel(excel_file)

def get_openai_response(history, data):
    try:
        prompt = (
            f"The following is the data from the Excel file:\n{data}\n\n"
            "Please provide a response to the user's query in a table format where applicable.Donot give incorrect response."
            "\n\n" + "\n".join([f"{h['role']}: {h['content']}" for h in history])
        )
        response = openai.ChatCompletion.create(
            engine=deployment,
            messages=[{"role": "system", "content": "You are an assistant."}, {"role": "user", "content": prompt}],
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # CSS for logo and background image
    
    st.markdown("""
        <style>
        .logo {
            position: fixed;
            top: 0;
            right: 0;
            margin-right: 10px;
            margin-top: 25px;
            width: 140px;  # Adjust this value as needed
            height: 100px;
        }
        </style>
        """, unsafe_allow_html=True)
    st.markdown("""
        <img src="data:image/png;base64,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" class="logo">
        """, unsafe_allow_html=True)

    # Sidebar with an image
    with st.sidebar:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRViRfutvNG9i9GtCPAC6qiwcK_uIOvKU0QP-zvFl3iMHKpUvAvStpetXH8o2AQ_fA4tBg&usqp=CAU")
        st.write("CHATBOT-SGP")
        st.write("### Example Prompts:")
        st.write("- What are the details of employees in the Engineering department?")
        st.write("- Show me the list of all Project Managers.")
        st.write("- Provide the email addresses of all employees.")
        st.write("- List all employees in the Human Resources department.")
    
    st.subheader("Employee Details for Sonata Global Project")

   

    if 'history' not in st.session_state:
        st.session_state['history'] = []

    user_input = st.text_input("You: ", "")
    send_button = st.button("↪", key="send_button", help="Send your query")

    if send_button and user_input:
        history = st.session_state['history']
        history.append({"role": "user", "content": user_input})
        
        # Prepare data from the DataFrame
        data = df.to_string(index=False)
        
        try:
            bot_response = get_openai_response(history, data)
            history.append({"role": "assistant", "content": bot_response})
            st.session_state['history'] = history
            
            for chat in history:
                st.write(f"{chat['role'].capitalize()}: {chat['content']}")
               
        except Exception as e:
            st.error(f"Error: {e}")

    
if __name__ == "__main__":
    main()