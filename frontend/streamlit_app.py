"""Private Streamlit test UI for MCP-backed Claims Assistant."""
import os

import httpx
import streamlit as st

API = os.getenv('CLAIMS_API_URL', 'http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='Claims Document Assistant', page_icon='📄')
st.title('Claims Document Assistant')
st.caption('Local capstone prototype — use fictional claims only')

if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'pending' not in st.session_state:
    st.session_state.pending = None


def api_post(path, *, json=None, files=None, params=None):
    try:
        with httpx.Client(timeout=180.0) as client:
            response = client.post(API + path, json=json, files=files, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        st.error(f'Backend request failed: {exc}')
        return None


def record(text, role='assistant'):
    st.session_state.messages.append({'role': role, 'content': text})


def process_response(data):
    if data is None:
        return
    st.session_state.session_id = data['session_id']
    record(data.get('message', ''))
    st.session_state.pending = data if data.get('type') in ('confirm_claim', 'upload_request') else None


for item in st.session_state.messages:
    with st.chat_message(item['role']):
        st.write(item['content'])

pending = st.session_state.pending
if pending and pending['type'] == 'confirm_claim':
    st.subheader('Confirm claim creation')
    st.json(pending['claim'])
    a, b = st.columns(2)
    with a:
        if st.button('Confirm and create claim', type='primary'):
            process_response(api_post('/api/chat/confirm', json={
                'session_id': st.session_state.session_id, 'approved': True,
            }))
            st.rerun()
    with b:
        if st.button('Cancel creation'):
            process_response(api_post('/api/chat/confirm', json={
                'session_id': st.session_state.session_id, 'approved': False,
            }))
            st.rerun()

if pending and pending['type'] == 'upload_request':
    st.subheader('Attach document')
    st.write(f"Claim: `{pending['claim_id']}` · Type: `{pending['document_type']}`")
    with st.form('upload_form'):
        file = st.file_uploader('Choose a document', type=['pdf','png','jpg','jpeg','txt'])
        submit = st.form_submit_button('Upload document', type='primary')
    if submit:
        if file is None:
            st.warning('Choose a file first.')
        else:
            with st.spinner('Uploading and processing...'):
                data = api_post('/api/chat/upload', params={
                    'session_id': st.session_state.session_id,
                }, files={'file': (file.name, file.getvalue(), file.type or 'application/octet-stream')})
            if data:
                result = data.get('result', {})
                process_response(data)
                record('Upload processing details:\n```json\n' +
                       __import__('json').dumps({key: result.get(key) for key in (
                           'document_id', 'classification', 'verification', 'rag_indexing'
                       )}, indent=2) + '\n```')
                st.rerun()
    if st.button('Cancel upload'):
        process_response(api_post('/api/chat/cancel-upload', json={
            'session_id': st.session_state.session_id,
        }))
        st.rerun()

if pending is None:
    message = st.chat_input('Ask about a claim, create a claim, or upload a document')
    if message:
        record(message, 'user')
        with st.spinner('Thinking...'):
            process_response(api_post('/api/chat/message', json={
                'session_id': st.session_state.session_id,
                'message': message,
            }))
        st.rerun()

if st.sidebar.button('New chat'):
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.pending = None
    st.rerun()
