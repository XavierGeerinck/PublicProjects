from diffusers import StableDiffusionPipeline
import torch

model_id = "./model/elien"

pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16).to("cuda")

subject = "myselfiepicture person"

# prompt = f"{subject} dog in a bucket"
# prompt = f"as an oil painting by the ocean"
# prompt = f"{subject} as mad max from mad max fury road"
prompt = f"{subject} as the joker from the dark knight"
prompt = f"{subject} as a beautiful harley quinn from suicide squad with a dark background illuminated by a red light holding a baseball bat"
prompt = f"{subject} posing as a beautiful women while looking outside and holding a book to read, 4k render, photorealistic, global illumination"
# prompt = f"{subject} as the terminator"
# prompt = f"{subject} as tyler durden from fight club"
# prompt = f"{subject} as a hobbit"
# prompt = "{subject} as gandalf from lord of the rings"

# https://mpost.io/best-100-stable-diffusion-prompts-the-most-beautiful-ai-text-to-image-prompts/
# https://openart.ai/
# https://www.krea.ai/
# https://lexica.art/

# prompt = f"{subject} as a strong boxer, wearing a red robe"
# prompt = f"{subject} as keanu reeves from the matrix"
# prompt = f"{subject} as a wizard"
# prompt = f"{subject} as a wizard, wearing a red robe"
# prompt = f"{subject} as keanu reeves as an asian old warrior chief"
# prompt = f"{subject} sitting with heaphones in a photorealistic render"

# prompt = f"a photorealistic photo of sks as a business person in a suit"
# prompt = f"{subject} shooting the moon with a beautiful night sky and stars illuminating the sky in a photorealistic scene"
# prompt = f"{subject} as a beautiful portrait as a handsome superhero, full body concept, cyberpunk 2077, 4k render, global illumination"
# prompt = f"{subject} as a beautiful portrait of a winx club fairy character, 4k render, global illumination"

# https://www.reddit.com/r/StableDiffusion/comments/ya4zxm/dreambooth_is_crazy_prompts_workflow_in_comments/

#Guidance scale: 12Steps: 130Strength: .95
prompt = f"cinematic still of {subject} person with glasses as rugged warrior, threatening xenomorph, alien movie (1986),ultrarealistic" 

#Guidance scale: 6Steps: 60Strength: .999
prompt = "fcolorful cinematic still of {subject} person with glasses, armor, cyberpunk,background made of brain cells, back light, organic, art by greg rutkowski, ultrarealistic, leica 30mm" 

#Guidance scale: 6Steps: 60Strength: .999
prompt = f"colorful cinematic still of {subject} person with glasses, armor, cyberpunk, with a xenonorph, in alien movie (1986),background made of brain cells, organic, ultrarealistic, leic 30mm" 

#Guidance scale: 12Steps: 100Strength: 0.999
# prompt = f"colorful cinematic still of {subject} person with glasses, {subject} with long hair, color lights, on stage, ultrarealistic" 

#Guidance scale: 6Steps: 60Strength: 0.9
# prompt = f"colorful portrait of {subject} person with dark glasses as eminem, gold chain necklace, relfective puffer jacket, short white hair, in front of music shop,ultrarealistic, leica 30mm" 

#Guidance scale: 12Steps: 180Strength: 0.999
# prompt = f"colorful photo of {subject} as kurt cobain with glasses, on stage, lights, ultrarealistic, leica 30mm-2022-10-14 22-43-47.249519-seed 22273242-guid 12-step 180-strng 0.999" 

#Guidance scale: 11Steps: 130Strength: 0.98
# prompt = f"impressionist painting of (({subject})) by Daniel F Gerhartz, (({subject} person with glasses painted in an impressionist style)), nature, trees" 

#Guidance scale: 6Steps: 33Strength: 0.92
# prompt = f"pencil sketch of {subject} man, {subject}, {subject} man, inpired by greg rutkowski, digital art by artgem" 

#Guidance scale: 11Steps: 60Strength: 0.99
# prompt = f"photo, colorful cinematic still of {subject} person with glasses, organic armor,cyberpunk,background brain cells mesh, art by greg rutkowski" 

#Guidance scale: 11Steps: 80Strength: 0.99
# prompt = f"photo, colorful cinematic still of {subject} with organic armor, cyberpunk background, {subject}, greg rutkowski" 

#ce scale: 11.5Steps: 50Strength: 0.9
# prompt = f"photo of {subject} astronaut, astronaut, glasses, helmet in alien world abstract oil painting, greg rutkowski, detailed faceGuidan" 

#Guidance scale: 14Steps: 150Strength: 0.8
# prompt = f"photo of {subject} as firefighter, helmet, ultrarealistic, leica 30mm"

#Guidance scale: 12Steps: 100Strength: 0.95
# prompt = f"photo of {subject} as person with glasses, bowler hat, in django unchained movie, ultrarealistic, leica 30mm" 

#Guidance scale: 12Steps: 100Strength: 0.95
# prompt = f"photo of {subject} as serious spiderperson with glasses, ultrarealistic, leica 30mm"

#Guidance scale: 13Steps: 150Strength: 0.9
# prompt = f"photo of {subject} person as steampunk warrior, neon organic vines, glasses, digital painting"

#Guidance scale: 11Steps: 180Strength: 0.69
# prompt = f"photo of {subject} person as supermario with glassesm mustach, blue overall, red short,{subject} man,{subject}. ultrarealistic, leica 30mm" 

#Guidance scale: 12Steps: 50Strength: 0.94
# prompt = f"photo of {subject} person as targaryen warrior with glasses, long white hair, armor, ultrarealistic, leica 30mm" 

#Guidance scale: 8Steps: 153Strength: 0.9
# prompt = f"portrait of {subject} as knight, with glasses white eyes, white mid hair, scar on face, handsome, elegant, intricate, headshot, highly detailed, digital" 

#Guidance scale: 8Steps: 153Strength: 0.9
# prompt = f"portrait of {subject} person with glasses as hulk, handsome, elegant, intricate luminescent cyberpunk background, headshot, highly detailed, digital painting" 

# Guidance scale: 9Steps: 80Strength: 0.97
# prompt = f"portrait of {subject} person with glasses as private eye detective, intricate, war torn, highly detailed, digital painting, concept art, smooth, sharp focus"

# https://www.reddit.com/r/StableDiffusion/comments/yctjyt/prompt_to_create_comic_art_great_for_use_with/
# prompt = f"{subject} in Retro comic style artwork, highly detailed James Bond, comic book cover, symmetrical, vibrant"

image = pipe(prompt, num_inference_steps=50, guidance_scale=0.9).images[0]

image.save("result.png")