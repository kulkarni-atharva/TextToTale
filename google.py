import requests
import openai
import os
from mutagen.mp3 import MP3
from PIL import Image
import imageio
from moviepy import editor
from pathlib import Path
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', default=None)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE')
CX = os.getenv('CUSTOM_SEARCH_ID', default=None)
print('Here is what is fetched from env:')
print(GOOGLE_API_KEY, '\n', OPENAI_API_KEY)
# API_KEY = 'AIzaSyBtPDvkVkJwjIEQYDp9qjfKkFW2Ma1wCbc'
# api_key = "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"
# CX = 'd183f7dd2de104355'
QUERY = input()
word = QUERY
os.makedirs('video',exist_ok=True)
# openai.api_key = api_key
openai.api_key = OPENAI_API_KEY
openai.api_base = OPENAI_API_BASE
prompt = f"Write 3 paragraph about the word '{word}':"
client = openai.OpenAI()
response = client.chat.completions.create(
  model="pai-001-light-beta",
#   prompt= prompt,
  temperature=0.7,
  max_tokens=256,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0,
#   stop=["Human: ", "AI: "]
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": prompt}
  ]
)

# response = openai.Completion.create(
#     engine="text-davinci-003",  # Instead of engine-text-davinici-003, you can choose anything
#     prompt=prompt,
#     max_tokens=450
# )
generated_paragraph = response.choices[0].text.strip()
print("generated paragrap: \n")
print(generated_paragraph)
file_name = f"{word}_paragraph.txt"
with open(file_name, "w") as file:
    file.write(generated_paragraph)
new_prompt=f"'{generated_paragraph}' \n \n Using this paragraph generate single or double word prompts such that these prompts will be used to generate images which will explain the entire paragraph. Also each prompt should be in a different line. Maximum prompts should be 10. Remove numbers in front of words"
response = openai.Completion.create(
    # engine="text-davinci-003",  # same as above code engine.
    model="pai-001-light-beta",
    prompt=new_prompt,
    max_tokens=150
)
generated_list=response.choices[0].text
file_name_2=f"{word}_prompts.txt"
with open(file_name_2, "w")as file:
    file.write(generated_list)
prompt_list=[]
with open(file_name_2, "r")as file:
    for line in file:
        if line!="\n" and line!=".\n":
            prompt_list.append(line.replace('\n',''))
print(prompt_list)
output_dir = 'downloaded_images'
os.makedirs(output_dir, exist_ok=True)
max_attempts=5
for x in prompt_list:
    url = f'https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={CX}&q={QUERY+x}&searchType=image'
    response = requests.get(url)
    data = response.json()

    if 'items' in data:
        # Limit to a maximum of 3 images per search query
        for i, item in enumerate(data['items'][:1]):
            image_url = item['link']
            response = requests.get(image_url)
            with open(f'{output_dir}/{word}_{x}_{i+1}.jpg', 'wb') as file:
                file.write(response.content)
                print(f'Downloaded {word} image {i+1} for prompt: {x}')
    else:
        print(f'No images found for {word} using prompt: {x}')


language="en"
text=generated_paragraph
speech = gTTS(text=text,lang=language,slow=False,tld="com.au")
speech.save("pfinal.mp3")

audio_path = os.path.join(os.getcwd(), "pfinal.mp3")
video_path = os.path.join(os.getcwd(), "video")
images_path = os.path.join(os.getcwd(), "downloaded_images")
audio = MP3(audio_path)
audio_length = audio.info.length
image_file = os.listdir(images_path)
target_width, target_height = (1000, 1000)
output_directory = "output_images"
os.makedirs(output_directory, exist_ok=True)
resized_images=[]

for image_filename in os.listdir(images_path):
    image_path = os.path.join(images_path, image_filename)
    output_filename = os.path.join(output_directory, image_filename)

    try:
        img = Image.open(image_path)
        img_width, img_height = img.size
        if img_width != target_width or img_height != target_height:
            new_img = Image.new("RGB", (target_width, target_height), (255, 255, 255))
            x_offset = (target_width - img_width) // 2
            y_offset = (target_height - img_height) // 2
            new_img.paste(img, (x_offset, y_offset))
            new_img.save(output_filename)
        else:
            img.save(output_filename)
        resized_images.append(image_filename)
    except Exception as e:
        print(f"Error processing {image_filename}: {str(e)}")

#print("Resized images:", resized_images)

#images_path = "output_images"
output_directory = "output_images"
#target_width = 1000
#target_height = 1000
resized_images = []

for images in os.listdir(output_directory):
     image_path = os.path.join(output_directory, images)
     img = Image.open(image_path)
     resized_images.append(img)
duration = audio_length/len(resized_images)
imageio.mimsave('images.gif',resized_images,fps=1/duration)
video = editor.VideoFileClip("images.gif")
audio = editor.AudioFileClip(audio_path)
final_video = video.set_audio(audio)
os.chdir(video_path)
final_video.write_videofile(fps=60, codec="libx264", filename="video.mp4")
