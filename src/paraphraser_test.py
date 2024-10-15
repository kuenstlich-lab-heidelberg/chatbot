from paraphraser.openai import OpenAIParaphraser
from paraphraser.jan import JanParaphraser

from dotenv import load_dotenv
load_dotenv() 

para = JanParaphraser()
para = OpenAIParaphraser()

print(para.paraphrase("Ich habe 8 Äpfel."))
print("")

print(para.paraphrase("Du must durch die große rote tür gehen. sei aber vorsichtig."))
print("")

print(para.paraphrase("Du hast in deinem Beutel einen Schlüssel, einen Apfel und, wie ich gerade sehe , auch ein Messer."))
print("")

