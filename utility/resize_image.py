import os
from PIL import Image

RAW_DIR = "utility/raw_images/"
EDITED_DIR = "utility/edited_images/"
SIZE = (64, 64)

if not os.path.exists(EDITED_DIR):
	os.makedirs(EDITED_DIR)

for filename in os.listdir(RAW_DIR):
	if filename.lower().endswith('.png'):
		# Remove 'raw' and '-Photoroom' and extra spaces, then .png
		dishname = filename.replace('raw', '').replace('-Photoroom', '').replace('  ', ' ').replace(' ', ' ').strip()
		dishname = dishname.replace('.png', '').replace('  ', ' ').replace(' ', ' ').strip()
		dishname = dishname.replace(' ', '_')  # Optional: use underscores for spaces
		output_name = f"{dishname}.png"
		input_path = os.path.join(RAW_DIR, filename)
		output_path = os.path.join(EDITED_DIR, output_name)
		try:
			img = Image.open(input_path)
			sprite = img.resize(SIZE, resample=Image.NEAREST)
			sprite.save(output_path)
			print(f"Saved {output_path}")
		except Exception as e:
			print(f"Failed to process {filename}: {e}")