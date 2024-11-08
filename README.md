# Build an AI voice assistant with OpenAI's Realtime API in Python


Use python 3.12

```sh
brew install python-tk@3.12
brew install graphviz
brew install espeak-ng
brew install libsndfile

pip install piper-phonemize-cross
pip install piper-tts

export PATH=$(brew --prefix graphviz):$PATH
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"

pip install pygraphviz 



docker run -p 9000:9000 \
    -e API_KEY=my_api_key_value \
    -e DATABASE_URL=my_database_url \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -v /home/user/gcloud/credentials.json:/app/credentials.json \
    my-fastapi-app

```

