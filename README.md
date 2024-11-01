# Build an AI voice assistant with OpenAI's Realtime API in Python


Use python 3.12

```sh
brew install python-tk@3.12
brew install graphviz
brew install espeak-ng

pip install piper-phonemize-cross
pip install piper-tts

export PATH=$(brew --prefix graphviz):$PATH
export CFLAGS="-I $(brew --prefix graphviz)/include"
export LDFLAGS="-L $(brew --prefix graphviz)/lib"

pip install pygraphviz 

```