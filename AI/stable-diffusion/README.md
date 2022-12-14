```bash
# export MODEL_NAME="stabilityai/stable-diffusion-2"
export MODEL_NAME="CompVis/runwayml/stable-diffusion-v1-5"
export INSTANCE_DIR="../../../dataset/elien/500"
export OUTPUT_DIR="../../../model/elien"
export CLASS_DATA_DIR="../../../model/random"

cd diffusers/examples/dreambooth

# instance_prompt: description of what the object or style is with the initializer word sksperson
# we are tuning to batch size 2, learning rate 1e-6 and 1200 steps as recommended by hugging faces to train on faces
# train_batch_size=1 -> 1 per GPU
# we use prior-preservation to avoid overfitting by generating random pictures for the given class
# we enable train_text_encoder to fine-tune the text encoder
# class_data_dir to generate additional training data
accelerate launch train_dreambooth.py \
  --pretrained_model_name_or_path=$MODEL_NAME \
  --pretrained_vae_name_or_path="stabilityai/sd-vae-ft-mse" \
  --instance_data_dir=$INSTANCE_DIR \
  --class_data_dir=$CLASS_DATA_DIR \
  --output_dir=$OUTPUT_DIR \
  --instance_prompt="a photo of sksxvs2 person" \
  --class_prompt="a photo of a person" \
  --resolution=500 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=1 \
  --learning_rate=1e-6 \
  --lr_scheduler="constant" \
  --lr_warmup_steps=0 \
  --max_train_steps=1000 \
  --with_prior_preservation \
  --prior_loss_weight=1.0 \
  --num_class_images=200 \
  --sample_batch_size=4 \
  --train_text_encoder
```
