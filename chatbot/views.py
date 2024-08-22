import os
import markdown2
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ChatForm
from langchain.chains import ConversationalRetrievalChain
from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_community.vectorstores import Chroma
from django.views.decorators.csrf import csrf_exempt
from langchain.prompts import PromptTemplate
from .forms import ResumeUploadForm
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import authenticate, login

def login_view(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('chat')  # Redirect to the dashboard after successful login
        else:
            # Invalid login
            return render(request, 'login.html', {'error_message': 'Invalid username or password'})
    else:
        return render(request, 'login.html')


from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegistrationForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            # Create the user
            user = User.objects.create_user(username=username, email=email, password=password)
            # Set the role
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form})

@login_required
def logout_view(request):
    try:
        auth_logout(request)
        messages.success(request, 'You have logged out successfully!')
    except Exception as e:
        messages.error(request, f'Error occurred during logout: {e}')
    return redirect('login')


@login_required
def upload_success_view(request):
    return render(request, 'upload_success.html')
@login_required
@csrf_exempt
def upload_resume_view(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.cleaned_data['resume']
            resume_name = resume.name
            resume_path = os.path.join(PDF_DIRECTORY, resume_name)

            # Save the uploaded file to the PDF_DIRECTORY
            with open(resume_path, 'wb+') as destination:
                for chunk in resume.chunks():
                    destination.write(chunk)

            # Redirect to a success page or render a success message
            return redirect('upload_success')
    else:
        form = ResumeUploadForm()

    return render(request, 'upload_resume.html', {'form': form})
# Set the directory path where your PDF files are located
PDF_DIRECTORY = os.path.join(os.path.dirname(__file__), 'pdf')  # Assuming 'pdf' directory is located in the same directory as views.py

PERSIST = True
os.environ['HUGGINGFACEHUB_API_TOKEN'] = "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"  # Set your Hugging Face API token

# Initialize the model using HuggingFaceEndpoint
llm = HuggingFaceEndpoint(
            repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
            temperature=0.8,
            max_length=1000
    )
@login_required
@csrf_exempt
def chat_view(request):
    response = None
    chat_history = request.session.get('chat_history', [])

    try:
        if 'new_chat' in request.GET:
            # Handle creating a new chat session
            request.session.flush()  # Clear existing session data
            return redirect('chat')  # Redirect back to the chat page with a fresh session

        if request.method == 'POST':
            form = ChatForm(request.POST)
            if form.is_valid():
                query = form.cleaned_data['input_text']
                print("Received query:", query)  # Debug print statement for query

                try:
                    # Initialize the embedding model using HuggingFaceEmbeddings
                    embeddings = HuggingFaceEmbeddings()

                    if PERSIST and os.path.exists("persist"):
                        vectorstore = Chroma(persist_directory="persist", embedding_function=embeddings)
                        index = VectorStoreIndexWrapper(vectorstore=vectorstore)
                    else:
                        if not os.path.exists(PDF_DIRECTORY):
                            os.makedirs(PDF_DIRECTORY)
                        loader = DirectoryLoader(PDF_DIRECTORY)
                        if PERSIST:
                            index_creator = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=Chroma, vectorstore_kwargs={"persist_directory": "persist"})
                        else:
                            index_creator = VectorstoreIndexCreator(embedding=embeddings)
                        index = index_creator.from_loaders([loader])

                    
                    """
                    # Define your custom prompt template
                    custom_prompt_template = 
                    You are a resume parsing assistant. When provided with an applicant's name,
                    you will retrieve and summarize relevant details from their resume. 
                    The details could include work experience, skills, education, and other relevant information.

                    <context>
                    {context}
                    </context>

                    Question: {question}
                

                    # Create a PromptTemplate instance with your custom template
                    custom_prompt = PromptTemplate(
                        template=custom_prompt_template,
                        input_variables=["context", "question"],
                    )
                        """
                    # Create a retrieval chain to answer questions
                    qa_chain = ConversationalRetrievalChain.from_llm(
                        llm=llm,
                        retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
                        verbose=True
                    )

                    # Process the input question through the retrieval chain
                    chat_history_tuples = [(message[0], message[1], "hr") for message in chat_history]
                    result = qa_chain.invoke({"question": query, "chat_history": chat_history_tuples})

                    # Retrieve both context and answer
                    context = result.get("context", "No context available.")
                    answer = result.get("answer", "No answer available.")

                    # Combine context and answer into the response text
                    response_text = f"**Context:**\n{context}\n\n**Answer:**\n{answer}"

                    # Convert the combined response text to markdown format
                    response_text_markdown = markdown2.markdown(response_text)

                    # Append the response to chat history
                    chat_history.append((query, response_text_markdown, "assistant"))
                    request.session['chat_history'] = chat_history

                except Exception as e:
                    # Log the error
                    print("An error occurred:", e)
                    # You can add more detailed logging here if needed

        else:
            form = ChatForm()

        print("Chat History:", chat_history)

        return render(request, 'chat.html', {'form': form, 'response': response, 'chat_history': chat_history})

    except Exception as e:
        # Log the error
        print("An error occurred:", e)
        # You can add more detailed logging here if needed
        # Render an error page or return an appropriate response
        return HttpResponse("An error occurred. Please try again later.")
